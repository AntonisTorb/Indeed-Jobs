from datetime import datetime, timedelta
import logging
import re
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

from .configuration import Config
from .database import IndeedDb
from .utils import INDEED_COUNTRIES 


class IndeedScraper:

    def __init__(self, config: Config, indeed_db: IndeedDb) -> None:
        '''Scraper class for `Indeed` Job postings.'''

        self.config = config
        self.indeed_db: IndeedDb = indeed_db

        self.logger: logging.Logger = logging.getLogger(__name__)

        self.options: Options = Options()
        self.options.add_argument("--headless")
        self.options.set_preference("general.useragent.override", 
                                    "userAgent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0")
        

    def _construct_urls(self) -> list[str]:
        '''Creates and returns a list of URLs for each location and job title specified in the configuration.'''

        url_list: list[str] = []
        try:
            for country_code, cities in self.config.locations.items():
                if country_code not in INDEED_COUNTRIES.values():
                    try:
                        country_code = INDEED_COUNTRIES[country_code.lower()]
                    except KeyError:
                        self.logger.error(f'Country {country_code} not supported or wrong spelling. Skipping...')
                        continue
                
                for city in cities:
                    city = city.replace(" ", "+").replace(",", "%2C")
                    for job_title in self.config.job_titles:
                        job_title = job_title.replace(" ", "+")
                        url_list.append(f'https://{country_code}.indeed.com/jobs?q={job_title}&l={city}&sort=date')
        except Exception as e:
            self.logger.exception(e)
            self.config.kill = True

        return url_list


    def _get_date_posted(self, posted: str) -> str | None:
        '''Returns the string representation of the date the job was posted in the format `YYYY-MM-DD`.'''

        regex_id: re.Pattern = re.compile("([0-9]+)")
        today = datetime.now()

        try:
            if "today" in posted.lower() or "just" in posted.lower():
                return today.strftime("%Y-%m-%d")

            posted = int(re.findall(regex_id, posted)[0])
            diff = timedelta(hours=posted*24)

            if diff.days > self.config.ignore_older_than_days:
                return None
            
            final = today - diff
            return final.strftime("%Y-%m-%d")
        except Exception as e:
            self.logger.exception(e)
            self.config.kill = True


    def _scrape(self) -> None:
        '''Scrapes `Indeed` for the specified job(s) and location(s) and adds any new ones to the database.
        Additionally, if any new job posting is added, signals the Discord bot to notify the user.
        '''

        url_list = self._construct_urls()

        while self.indeed_db.busy:
            time.sleep(1)
        
        self.indeed_db.busy = True
        con, cur = self.indeed_db.get_con_cur()
        
        jobs_found: int = 0
        new_jobs_found: int = 0
        job_id_regex: re.Pattern = re.compile('jk=([a-zA-Z0-9]*)&')
        # scrape_job_ids: list[str] = []

        try:
            results = cur.execute('SELECT url FROM indeed_jobs')
            url_results: list[tuple[str]] = results.fetchall()
            job_ids_in_db: list[str] = []
            if len(url_results):
                url_list_db: list[str] = [url for url_tuple in url_results for url in url_tuple]
                for url in url_list_db:
                    try:
                        job_ids_in_db.append(re.search(job_id_regex, url).group(1))
                    except AttributeError:  # Ad in db.
                        pass

            with webdriver.Firefox(options=self.options) as driver:
                for url in url_list:
                    last_page = False
                    while not last_page:
                        if self.config.kill:
                            return
                        
                        driver.get(url)
                        time.sleep(self.config.selenium_sleep_sec)

                        try:  # If pop-up, refresh.
                            _ = driver.find_element(By.CSS_SELECTOR, "#mosaic-desktopserpjapopup")
                            driver.get(url)
                            time.sleep(self.config.selenium_sleep_sec)
                        except NoSuchElementException:
                            pass

                        postings = driver.find_elements(By.CLASS_NAME, "job_seen_beacon")
                        
                        for posting in postings:
                            jobs_found += 1
                            job_url = posting.find_element(By.CLASS_NAME, "jcs-JobTitle").get_attribute("href")

                            if "pagead" in job_url:
                                continue

                            try:
                                job_id: str = re.search(job_id_regex, job_url).group(1)
                                if job_id in job_ids_in_db:
                                    continue
                            except AttributeError:  # Ad.
                                continue
                                
                            job_ids_in_db.append(job_id)
                            
                            posted = posting.find_element(By.CSS_SELECTOR, "[data-testid='myJobsStateDate']").text
                            job_date_posted = self._get_date_posted(posted)
                            if job_date_posted is None:
                                continue

                            job_title = posting.find_element(By.CLASS_NAME, 'jcs-JobTitle').find_element(By.CSS_SELECTOR, 'span').text
                            job_employer = posting.find_element(By.CSS_SELECTOR, "[data-testid='company-name']").text
                            description_parts = [paragraph.text for paragraph in posting.find_elements(By.CSS_SELECTOR, "li")]
                            job_description = "\n".join([part for part in description_parts if part])
                            self.indeed_db.insert_new_job(con, cur, job_url, job_title, job_employer, job_description, job_date_posted)
                            new_jobs_found += 1

                        try:  # Get next page URL
                            url = driver.find_element(By.CSS_SELECTOR, "[data-testid='pagination-page-next']").get_attribute("href")
                        except NoSuchElementException:
                            last_page = True

        except Exception as e:
            self.logger.exception(e)
            self.config.kill = True
        finally:
            cur.close()
            con.close()
            self.indeed_db.busy = False

        self.logger.info(f'{jobs_found} jobs found, {new_jobs_found} new.')

        if new_jobs_found:
            self.indeed_db.new_jobs = True

    
    def scrape_loop(self):
        '''Performs the scraping on a schedule according to the configuration options.'''

        while not self.config.kill:
            # Taking the following approach in order to properly terminate the app without affecting potential db operations
            # or waiting for the full scraper delay. This way the killswitch check happens every second.
            start = datetime.now()
            end = start + timedelta(seconds=self.config.scraper_delay_sec)

            self.logger.info("Starting to scrape Indeed...")
            self._scrape()

            while datetime.now() < end:
                if self.config.kill:
                    break

                time.sleep(1)
            
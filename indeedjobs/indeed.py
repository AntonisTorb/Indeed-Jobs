import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

from .configuration import Config
from .database import IndeedDb


class IndeedScraper:

    def __init__(self, config: Config, indeed_db: IndeedDb) -> None:
        '''Scraper class for `Indeed` Job postings.'''

        self.config = config
        self.indeed_db: IndeedDb = indeed_db
        

    def _construct_urls(self) -> list[str]:
        '''Creates and returns a list of URLs for each location and job title specified in the configuration.'''

        url_list: list[str] = []
        for country_code, cities in self.config.locations.items():
            for city in cities:
                for job_title in self.config.job_titles:
                    url_list.append(f'https://{country_code}.indeed.com/jobs?q={job_title}&l={city}&sort=date')

        return url_list


    def scrape(self) -> None:
        '''Scrapes `Indeed` for the specified job(s) and location(s) and adds any new ones to the database.
        Additionally, if any new job posting is added, signals the Discord bot to notify the user.
        '''

        url_list: list[str] = self._construct_urls()
        new_job_found = False

        while self.indeed_db.busy:
            time.sleep(1)
        
        self.indeed_db.busy = True
        con, cur = self.indeed_db.get_con_cur()
        cur.execute('SELECT url FROM indeed_jobs')
        url_list = [url_tuple[0] for url_tuple in cur.fetchall()]

        try:
            with webdriver.Firefox() as driver:
                for url in url_list:
                    last_page = False
                    while not last_page:
                        driver.get(url)
                        time.sleep(self.config.selenium_sleep_sec)
                        postings = driver.find_elements(By.CLASS_NAME, "job_seen_beacon")
                        
                        for posting in postings:
                            job_url = posting.find_element(By.CLASS_NAME, "jcs-JobTitle").get_attribute("href")

                            if job_url in url_list:
                                continue

                            job_title = posting.find_element(By.CLASS_NAME, 'jcs-JobTitle').find_element(By.CSS_SELECTOR, 'span').text
                            job_employer = posting.find_element(By.CSS_SELECTOR, "[data-testid='company-name']").text
                            description_parts = [paragraph.text for paragraph in posting.find_elements(By.CSS_SELECTOR, "li")]
                            job_description = "\n".join([part for part in description_parts if part])
                            job_date_posted = posting.find_element(By.CSS_SELECTOR, "[data-testid='myJobsStateDate']").text.replace("\n", ": ")
                            
                            self.indeed_db.insert_new_job(con, cur, job_title, job_employer, job_description, job_date_posted)
                            if not new_job_found:
                                new_job_found = True

                        try:  # Get next page URL
                            url = driver.find_element(By.CSS_SELECTOR, "[data-testid='pagination-page-next']").get_attribute("href")
                        except NoSuchElementException:
                            last_page = True

        except Exception as e:
            self.logger.error(e)
            self.config.kill = True
        finally:
            cur.close()
            con.close()
            self.indeed_db.busy = False

        if new_job_found:
            self.indeed_db.new_jobs = True

    
    def scrape_loop(self):
        '''Performs the scraping on a schedule according to the configuration options.'''

        while not self.config.kill:
            self.scrape()
            time.sleep(self.config.scraper_delay_sec)
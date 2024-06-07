from requests import session

from .configuration import Config

class IndeedScraper:

    def __init__(self, config: Config) -> None:
        self.config = config
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
        }
        


    def _construct_url(self, country_code: str, job_title: str, city: str, start: int):

        return f'https://{country_code}.indeed.com/jobs?q={job_title}&l={city}&sort=date&start={start}'
        
    def scrape(self):

        s = session()
        r1 = s.get("https://ie.indeed.com/", headers=self.headers)
        print(r1.status_code, r1.text)
        # for country_code, cities in self.config.locations.items():
        #     for city in cities:
        #         for job_title in self.config.job_titles:
        #             # starting with one page
        #             url = self._construct_url(country_code, job_title, city, 0)
        #             print(url)
        #             r = s.get(url=url, headers=self.headers)
        #             print(r.status_code)
        with open("result.html", "w") as f:
            f.write(r1.text)
        
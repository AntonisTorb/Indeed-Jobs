import json
from pathlib import Path

class Config():

    def __init__(self, config_path: Path) -> None:
        '''Configuration class for the application.'''

        # Configuration settings typing.
        self.locations: dict[str, list[str]]
        self.job_titles: list[str]
        self.selenium_sleep_sec: int
        self.scraper_delay_sec: int
        self.bot_delay_sec: int

        try:
            with open(config_path, 'r') as f:
                self.__dict__ = json.load(f)
        except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
            print("Configuration file not found or corrupted. Please check the template in order to create one.")
            raise e
        
        self.new_jobs_in_db: bool = False
        self.kill = False
        


    def __repr__(self) -> str:
        return f'self.__dict'

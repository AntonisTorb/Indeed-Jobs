import json
from pathlib import Path


class Config():

    def __init__(self, config_path: Path) -> None:
        '''Configuration class for the application.'''

        # Configuration settings typing.
        self.locations: dict[str, list[str]]
        self.job_titles: list[str]
        self.db_path: str
        self.log_path: str
        self.selenium_sleep_sec: int = 10
        self.scraper_delay_sec: int = 3600
        self.bot_delay_sec: int = 600
        self.ignore_older_than_days: int = 7

        try:
            with open(config_path, 'r') as f:
                self.__dict__ = json.load(f)
        except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
            print("Configuration file not found or corrupted. Please check the template in order to create one.")
            raise e
        
        self.kill = False


    def __repr__(self) -> str:
        return f'self.__dict'

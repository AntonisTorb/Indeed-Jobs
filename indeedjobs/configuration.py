import json
from pathlib import Path

class Config():

    def __init__(self, config_path: Path) -> None:
        '''Configuration class for the application.'''

        # Default configuration values.
        self.locations: dict[str, list[str]]
        self.job_titles: list[str]

        try:
            with open(config_path, 'r') as f:
                self.__dict__ = json.load(f)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            print("Configuration file not found or corrupted. Please check the template in order to create one.")
            # self._dump_config(config_path)


    def _dump_config(self, config_path: Path) -> None:
        '''Creates the `config.json` configuration file if it does not exist or is corrupted.'''

        with open(config_path, 'w') as f:
            config = self.__dict__
            json.dump(config, f, indent=4)

    def __repr__(self) -> str:
        return f'self.__dict'

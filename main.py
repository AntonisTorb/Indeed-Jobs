import logging
from pathlib import Path


from indeedjobs import Config, DiscordBot, IndeedDb, IndeedScraper, maintain_log


def main() -> None:
    
    cwd: Path = Path.cwd()
    config_path: Path = cwd / "config.json"
    config = Config(config_path)

    if config.log_path:
        log_path: Path = Path(config.log_path)
    else:
        log_path = cwd / "IndeedJobs.log"
        
    main_logger: logging.Logger = logging.getLogger(__name__)
    logging.basicConfig(filename=log_path, 
                        level=logging.INFO,
                        format="%(asctime)s|%(levelname)8s|%(name)s|%(message)s")

    try:
        maintain_log(log_path, 30)
        indeed_db: IndeedDb = IndeedDb(config)
        indeed_db.create_adapters_converters()
        # indeed_db.create_table()
        
        # scraper = IndeedScraper(config, indeed_db)
        # scraper.scrape_loop()
    except Exception as e:
        main_logger.exception(e)

    try:
        bot: DiscordBot = DiscordBot(config, indeed_db)
        main_logger.info("Starting bot...")
        bot.run()
        main_logger.info("Closing bot...")
    except Exception as e:
        main_logger.exception(e)


if __name__ == "__main__":

    main()
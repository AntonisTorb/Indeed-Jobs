import logging
from pathlib import Path


from indeedjobs import Config, DiscordBot, IndeedDb, IndeedScraper, maintain_log


def main() -> None:

    cwd: Path = Path.cwd()

    logger_path: Path = cwd / "IndeedJobs.log"
    config_path: Path = cwd / "config.json"
    db_path: Path = cwd / "indeed.db"
    main_logger: logging.Logger = logging.getLogger(__name__)
    logging.basicConfig(filename=logger_path, 
                        level=logging.INFO,
                        format="%(asctime)s|%(levelname)8s|%(name)s|%(message)s")

    try:
        config = Config(config_path)
        indeed_db: IndeedDb = IndeedDb(db_path, config)
        indeed_db.create_adapters_converters()
        #indeed_db.create_table()
        
        scraper = IndeedScraper(config, indeed_db)
        #scraper.scrape()
    except Exception as e:
        main_logger.exception(e)

    try:
        maintain_log(logger_path, 30)
        bot: DiscordBot = DiscordBot(config, indeed_db)
        main_logger.info("Starting bot...")
        bot.run()
        main_logger.info("Closing bot...")
    except Exception as e:
        main_logger.exception(e)


if __name__ == "__main__":

    main()
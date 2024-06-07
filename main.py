import logging
from pathlib import Path


from indeedjobs import Config, DiscordBot, IndeedScraper


def main() -> None:

    cwd: Path = Path.cwd()

    logger_path: Path = cwd / "IndeedJobs.log"
    config_path: Path = cwd / "config.json"
    main_logger: logging.Logger = logging.getLogger(__name__)
    logging.basicConfig(filename=logger_path, 
                        level=logging.INFO,
                        format="%(asctime)s|%(levelname)8s|%(name)s|%(message)s")
    

    try:
        config = Config(config_path)
        scraper = IndeedScraper(config)
        scraper.scrape()
    except Exception as e:
        main_logger.exception(e)

    # try:
    #     #maintain_log(logger_path, 30)
    #     bot: DiscordBot = DiscordBot()
    #     main_logger.info("Starting bot...")
    #     bot.run()
    #     main_logger.info("Closing bot...")
    # except Exception as e:
    #     main_logger.exception(e)


if __name__ == "__main__":

    main()

    # country_code = ""
    # job_title = ""
    # location = ""
    # start = 0
    
    # print(construct_url(country_code, job_title, location, start))
import logging
from pathlib import Path
import threading
import time

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
        indeed_db.create_table()

        scraper: IndeedScraper = IndeedScraper(config, indeed_db)
        scraper_thread: threading.Thread = threading.Thread(target=scraper.scrape_loop)

        bot: DiscordBot = DiscordBot(config, indeed_db)
        bot_thread: threading.Thread = threading.Thread(target=bot.run)


        main_logger.info("Starting application.")
        scraper_thread.start()
        bot_thread.start()

    except Exception as e:
        main_logger.exception(e)
        config.kill = True

    while True:
        if config.kill:

            while scraper_thread.is_alive() or bot_thread.is_alive():
                time.sleep(1)

            main_logger.info("Closing application.")
            break

        try:
            time.sleep(1)
        except KeyboardInterrupt:  # Manual shutdown.
            config.kill = True

if __name__ == "__main__":

    main()
import logging
from pathlib import Path
import sqlite3

from .configuration import Config

class IndeedDb:

    def __init__(self, db_path: Path, config: Config) -> None:
        '''Class containing logic related to the `sqlite` database holding the `Indeed` job postings.'''

        self.db_path: Path = db_path
        self.config: Config = config

        self.logger: logging.Logger = logging.getLogger(__name__)


    def get_con_cur(self) -> tuple[sqlite3.Connection, sqlite3.Cursor]|tuple[None, None]:
        '''Creates and returns the `Connection` and `Cursor` objects for the specified `sqlite` database'''

        try:
            con: sqlite3.Connection = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
            cur: sqlite3.Cursor = con.cursor()
            return con, cur
        except Exception as e:
            self.logger.error(e)
            self.config.kill = True
            return None, None


    def create_adapters_converters(self) -> None:

        sqlite3.register_adapter(bool, int)
        sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))


    def create_table(self, drop_existing: bool = True) -> None:
        
        
        con: sqlite3.Connection
        cur: sqlite3.Cursor
        con, cur = self.get_con_cur()
        
        if drop_existing:
            cur.execute("DROP TABLE IF EXISTS indeed_jobs")

        try:
            cur.execute('''CREATE TABLE IF NOT EXISTS indeed_jobs(
                        id INTEGER PRIMARY KEY,
                        url TEXT,
                        job_title TEXT,
                        employer TEXT,
                        description TEXT,
                        date_posted TEXT,
                        notified BOOLEAN,
                        interested BOOLEAN,
                        response BOOLEAN,
                        rejected BOOLEAN,
                        interviews INTEGER,
                        job_offer BOOLEAN
                        )''')
            
            cur.execute('''INSERT INTO indeed_jobs(
                            url, job_title, employer, description, date_posted, notified, interested, response, rejected, interviews, job_offer
                        ) VALUES (
                            "test url", "test title", "test employer", "test description", "test date", ?, ?, ?, ?, 0, ?
                        )''', 
                        (False, False, False, False, False))
            con.commit()
            res = cur.execute("SELECT * FROM indeed_jobs")
            print(res.fetchall())
        except Exception as e:
            self.logger.error(e)
            self.config.kill = True
        finally:
            cur.close()
            con.close()

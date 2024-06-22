import asyncio
import logging
from pathlib import Path
import sqlite3

from .configuration import Config

class IndeedDb:

    def __init__(self, config: Config) -> None:
        '''Class containing logic related to the `sqlite` database holding the `Indeed` job postings.'''

        self.config: Config = config

        if config.db_path:
            self.db_path: Path = Path(config.db_path)
        else:
            self.db_path = Path.cwd() / "indeed.db"

        self.logger: logging.Logger = logging.getLogger(__name__)
        self.busy = False
        self.new_jobs = False


    def get_con_cur(self) -> tuple[sqlite3.Connection, sqlite3.Cursor]|tuple[None, None]:
        '''Creates and returns the `Connection` and `Cursor` objects for the specified `sqlite` database'''

        try:
            con: sqlite3.Connection = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
            cur: sqlite3.Cursor = con.cursor()
            return con, cur
        except Exception as e:
            self.logger.error(e)
            self.config.kill = True


    def create_adapters_converters(self) -> None:
        '''Creates adapters and converters for the Sqlite3 database.'''

        sqlite3.register_adapter(bool, int)
        sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))


    def create_table(self, drop_existing: bool = True) -> None:
        '''Initial creation of the `indeed_jobs` table.'''
        
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
                        applied BOOLEAN,
                        response BOOLEAN,
                        rejected BOOLEAN,
                        interviews INTEGER,
                        job_offer BOOLEAN
                        )''')
        except Exception as e:
            self.logger.error(e)
            self.config.kill = True
        finally:
            cur.close()
            con.close()


    def insert_new_job(self, con: sqlite3.Connection, cur: sqlite3.Cursor, job_url: str, job_title: str, 
                       job_employer: str, job_description: str, job_date_posted: str) -> None:
        '''Insert new job row to the database.'''
        
        values = (job_url,  job_title, job_employer, job_description, job_date_posted, False, False, False, False, False, 0, False)
        
        cur.execute('''INSERT INTO indeed_jobs(
                    url, job_title, employer, description, date_posted, notified, interested, applied, response, rejected, interviews, job_offer
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)''', values)
        con.commit()


    async def update_for_id(self, job_id: int, field: str, value: str):
        '''Update the database field with the values provided for the specified Id'''
        
        while self.busy:
            asyncio.sleep(1)

        self.busy = True 
        con, cur = self.get_con_cur()

        try:
            if value == "interviews":
                cur.execute("UPDATE indeed_jobs SET interviews = interviews + 1 WHERE id = ?", (job_id))
            else:
                cur.execute("UPDATE indeed_jobs SET ? = ? WHERE id = ?", (field, int(value), job_id))
        except Exception as e:
            raise e
        finally:
            cur.close()
            con.close()
            self.busy = False
import sqlalchemy as db
from sqlalchemy import Table, create_engine, Column
from sqlalchemy.orm import Session
import datetime
from typing import List, Dict, Any
from smartmailer.utils.new_logger import Logger

class Database:
    _instance = None
    
    # This will be a singleton class
    def __new__(cls, *args, **kwargs):
        if Database._instance is None:
            Database._instance = object.__new__(cls)
            Database._instance.__init__(*args, **kwargs)

        return Database._instance
    
    def __init__(self, dbfile_path: str):
        self.logger = Logger()

        self.logger.info(f"Initializing database at {dbfile_path}")
        self.engine = create_engine(f"sqlite:///{dbfile_path}")
        self.engine.connect()
        self.meta = db.MetaData()

        self._sent = Table(
            "sent", self.meta,
            Column("recipient_hash", db.String, primary_key=True),
            Column("sent_time", db.DateTime))
        
        self._create_tables()
    
    def _create_tables(self):
        assert self.meta is not None, "Metadata is not initialized."
        assert self.engine is not None, "Engine is not initialized."
        self.meta.create_all(self.engine)
    
    def insert_recipient(self, recipient_hash: str) -> int:
        with Session(self.engine) as session:
            command = self._sent.insert().values(recipient_hash=recipient_hash, sent_time=datetime.datetime.now())
            result = session.execute(command)
            session.commit()
            self.logger.info(f"Recipient {recipient_hash} inserted successfully.")
            return result.lastrowid

    def check_recipient_sent(self, recipient_hash: str) -> bool:
        with Session(self.engine) as session:
            query = self._sent.select().where(self._sent.c.recipient_hash == recipient_hash)
            result = session.execute(query).fetchone()
            return result is not None
    
    def get_sent_recipients(self) -> List[Dict[str, Any]]:
        self.logger.info("Fetching all sent recipients from database.")
        with Session(self.engine) as session:
            query = self._sent.select()
            columns = [col.name for col in self._sent.columns]  # Get column names from the table
            query_result = session.execute(query).fetchall()
            return [dict(zip(columns, row)) for row in query_result]
        
    def delete_recipient(self, recipient_hash: str) -> None:
        self.logger.info(f"Trying to delete recipient with hash {recipient_hash}.")
        if not self.check_recipient_sent(recipient_hash):
            self.logger.error(f"{recipient_hash} not found. Cannot delete.")
            raise ValueError(f"Recipient with hash {recipient_hash} not found in the database.")
    
        with Session(self.engine) as session:
            command = self._sent.delete().where(self._sent.c.recipient_hash == recipient_hash)
            session.execute(command)
            session.commit()
            self.logger.info(f"{recipient_hash} deleted successfully.")
    
    def clear_database(self) -> None:
        with Session(self.engine) as session:
            command = self._sent.delete()
            session.execute(command)
            session.commit()
        self._create_tables()  # Recreate the table structure after clearing
        self.logger.info("Database cleared and table structure recreated.")
    
    def close(self) -> None:
        if self.engine:
            self.logger.info("Closing database connection and disposing engine.")
            self.engine.dispose()
            self.engine = None
            self.meta = None
            Database._instance = None
    
    def __del__(self):
        self.close()
        self.logger.info("Database connection closed.")
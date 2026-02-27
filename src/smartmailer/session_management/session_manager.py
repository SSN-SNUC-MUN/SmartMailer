from tabulate import tabulate
from typing import List, Dict, Any
from smartmailer.session_management.db_operator import DBOperator
from smartmailer.utils.strings import get_os_safe_name
import os
from smartmailer.config import DB_FOLDER
from smartmailer.utils.new_logger import Logger
from smartmailer.utils.types import TemplateModelType
from smartmailer.core.template import TemplateModel

class SessionManager:
    def __init__(self, session_name: str) -> None:
        #Initialize connection
        self.session_name = session_name
        self.session_name_os_safe = get_os_safe_name(session_name)
        self.logger = Logger()
        # don't need to configure,
        # it will use the same instance we made during the SmartMailer init

        self.dbname = self.session_name_os_safe + ".db"
        db_folder_path = os.path.join(os.getcwd(), DB_FOLDER)
        if not os.path.exists(folder := db_folder_path):
            os.makedirs(folder)

        self.dbfile_path = os.path.join(db_folder_path, self.dbname)
        
        if os.path.exists(self.dbfile_path):
            self.logger.info(f"Using existing database file: {self.dbfile_path}")
        else:
            self.logger.info(f"Creating new database file: {self.dbfile_path}")

        # Initialize database operator
        self.db_op = DBOperator(self.dbfile_path)
    
    #Filter the recipients whose email wasn't sent in the previous run
    def _filter_unsent_recipients(self, recipients: List[TemplateModelType]) -> List[TemplateModelType]:
        unsent_recipients: List[TemplateModelType] = []
        for recipient in recipients:
            recipient_hash = recipient.hash_string
            if not self.db_op.check_recipient_sent(recipient_hash):
                unsent_recipients.append(recipient)
        return unsent_recipients
    
    def filter_sent_recipients(self, recipients: List[TemplateModelType]) -> List[TemplateModelType]:
        sent: List[str] = [r['recipient_hash'] for r in self.db_op.get_sent_recipients()]
        return [recipient for recipient in recipients if recipient.hash_string in sent]
    
    def get_sent_recipients(self) -> List[Dict[str, Any]]:
        return self.db_op.get_sent_recipients()
    
    def add_recipient(self, recipient: TemplateModel) -> None:
        recipient_hash = recipient.hash_string
        if not self.db_op.check_recipient_sent(recipient_hash):
            self.db_op.add_to_db(recipient_hash)

    def get_current_session_id(self) -> str:
        return self.session_name_os_safe
import time
import datetime

from collections import Counter

import CONSTANTS
from logger import log
from printer import Printer


class Motor:
   
    def __init__(self, config):
        self.last_search = None
        self.status = 'ON'

        self._parse_config(config)
        self._initialize_email_engine()
        self._connect()

        self._define_actions()
        self.command_center()
    
    def _define_actions(self):
        self.ACTIONS = {
            CONSTANTS.SUMMARY_ALL_EMAILS: self.summarize,
            CONSTANTS.GET_ALL_BOXES: self.get_mailboxes,
            CONSTANTS.GET_RECEIVED_FROM: self.get_emails_from,
            CONSTANTS.GET_SENT_TO: self.get_emails_from,
            CONSTANTS.DELETE_EMAILS: self.delete_emails,
            CONSTANTS.LOGOUT: self.logout,
        }
 
    def command_center(self):
        while self.status == 'ON':
            question = "What action would you like to do ?"
            action = Printer.main_menu(question, self.ACTIONS)
            self.ACTIONS[action]()

    def summarize(self):
        ids, raw_data = self.email.get_all_emails()

        log.info('{} on {} emails received'.format(len(raw_data), len(ids)))
        log.info('Below is the top 10 senders')

        data = self._group_emails_by(raw_data, 'From')
        Printer.table_summary(data)
       
    def _group_emails_by(self, raw_data, by):
        return Counter(msg[by] for msg in raw_data)

    def delete_emails():
        pass

    def get_emails_from(self):
        question = "Type in the sender's email address:"
        email_address = Printer.ask_for_email(question)
        emails = self.email.search_by_sender(email_address)
        Printer.table_summary(emails)
        self.last_search = emails

    def get_summary_email_by_id(self, ids):
        return self.email.fetch_header_email(ids)

    def get_full_email_by_id(self, ids):
        return self.email.fetch_full_email(ids)

    def get_mailboxes(self):
        """
        Get a list of all the available folders in the mail box
        """
        return self.email.get_mailboxes()

    def get_storage_info(self):
        return self.email.get_quota()

    def logout(self):
        self.email.logout()
        log.info("Connexion successfully closed !")
        self.status = 'OFF'

    def _connect(self):
        log.info("Logging in as {}...".format(self.email_address))
        self.email.init_mail(self.host_name,
                             self.port,
                             self.email_address,
                             self.password)
        log.info("Logged in !")

    def _initialize_email_engine(self):
        self.email = self.email_engine_class()

    def _parse_config(self, config):
        self.host_name = config['host']
        self.port = config['port']
        self.email_address = config['email_address']
        self.password = config['password']
        self.name = config['name']
        self.server_type = config['server_type']
        self.ssl = config['ssl']
        self.email_engine_class = config['email_access_class']


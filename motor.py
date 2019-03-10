from collections import Counter
from logger import log
from printer import Printer
import time
import datetime


class Motor:
    def __init__(self, config):
        self.parse_config(config)
        self.initialize_email_engine()
        self.connect()
       
        self.summarize()

        self.logout()

    def parse_config(self, config):
        self.host_name = config['host']
        self.port = config['port']
        self.email_address = config['email_address']
        self.password = config['password']
        self.name = config['name']
        self.server_type = config['server_type']
        self.ssl = config['ssl']
        self.email_engine_class = config['email_access_class']

    def summarize(self):
        ids, raw_data = self.email.get_all_emails()
        log.info('{} on {} emails received'.format(len(raw_data), len(ids)))
        log.info('Below is the top 10 senders')
        data = self.count_by(raw_data, 'From')
        Printer.table_summary(data)
       
    def count_by(self, raw_data, by):
        out = Counter(msg[by] for msg in raw_data)
        return out

    def initialize_email_engine(self):
        self.email = self.email_engine_class()

    def search_email_by_sender(self, email, full=False):
        res = self.email.search_by_sender(email)
        return res

    def get_summary_email_by_id(self, ids):
        return self.email.fetch_header_email(ids)

    def get_full_email_by_id(self, ids):
        return self.email.fetch_full_email(ids)

    def connect(self):
        log.info("Logging in as {}...".format(self.email_address))
        self.email.init_mail(self.host_name,
                             self.port,
                             self.email_address,
                             self.password)
        log.info("Logged in !")

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

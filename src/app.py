import time
import datetime
import argparse
import re
import io
import contextlib

from collections import Counter

from src import CONSTANTS
from src.logger import log
from src.printer import Printer


class Motor:

    def __init__(self, config, connections=15):
        self.last_search = None
        self.status = 'ON'
        self._print = Printer()
        self.max_open_connections = connections

        self._parse_config(config)
        self._help_message()
        self._initialize_email_engine()
        self._connect()


    def run(self):
        self._parser()
        self.command_center()


    def _help_message(self):
        template = "{s:3}  {l:15}\t{t:10}\t{h}\n"
        msg = "\nIncorrect !\nUse one of the below options\n\n[options]\n"

        for action in CONSTANTS.ACTIONS:
            data = CONSTANTS.USAGES[action]

            if 'type' in data['kwargs']:
                type_ = re.search("'(\w+)'", repr(data['kwargs']['type']))
                type_ = type_[1]

                if data['kwargs']['nargs'] in ('*', '+'):
                    type_ = "[{} ...]".format(type_)
            else:
                type_ = ''

            msg += template.format(s=data['args']['short'],
                                   l=data['args']['long'],
                                   t=type_,
                                   h=data['kwargs']['help'])
        self.help_message = msg


    def _parser(self):
        self.parser = argparse.ArgumentParser(prog=CONSTANTS.PROGRAM_NAME,
                                              add_help=False)

        excl = self.parser.add_mutually_exclusive_group(required=True)

        for action in CONSTANTS.ACTIONS:
            data = CONSTANTS.USAGES[action]
            excl.add_argument(data['args']['short'],
                              data['args']['long'],
                              **data['kwargs'])

        return True


    def parse_answer(self, answer):
        try:
            f = io.StringIO()
            with contextlib.redirect_stderr(f):
                parsed = self.parser.parse_args(answer.split())
        except SystemExit as e:
            print(self.help_message)
            return False

        parsed = vars(parsed) 
        
        for action in CONSTANTS.ACTIONS:
            if parsed[action]:
                print(action)



    def command_center(self):
        while self.status == 'ON':
            answer = self._print.main_menu()

            if answer:
                self.parse_answer(answer)



    def summarize(self):
        top = 10

        data = self.email.get_all_emails()

        log.info('{} emails successfully analysed'.format(len(data)))
        log.info('Below is the top {} senders'.format(top))

        if data:
            self.last_search = self._print.summary_by_top_senders(data, top)


    def delete_emails():
        pass


    def get_emails_from(self):
        question = "Type in the sender's email address:"
        sender_email_address = self._print.ask_for_email(question)
        emails_list = self.email.search_by_sender(sender_email_address)

        if not emails_list:
            log.info("No emails were retrieved")
        else:
            log.info("{} emails were retrieved".format(len(emails_list)))
            self._print.display_emails(emails_list)
            self.last_search = emails_list


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
        self.email.initialize(self.host_name,
                              self.port,
                              self.email_address,
                              self.password,
                              self.max_open_connections)
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
        self.max_open_connections = config['maximum_open_connexions']
        self.email_engine_class = config['email_access_class']


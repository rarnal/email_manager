import time
import datetime
import argparse

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
        self._initialize_email_engine()
        self._connect()


    def run(self):
        self._parser()
        self.command_center()


    def _help_message(self):
        template = "    {s:3} {l:15}        {h}\n"
        msg = "Use one of the below options\n\n[options]\n"

        for action in CONSTANTS.ACTIONS:
            data = CONSTANTS.USAGES[action]
            msg += template.format(s=data['args']['short'],
                                   l=data['args']['long'],
                                   h=data['kwargs']['help'])
        return msg


    def _parser(self):
        self.parser = argparse.ArgumentParser(prog=CONSTANTS.PROGRAM_NAME,
                                              usage=self._help_message(),
                                              add_help=False)

        excl = self.parser.add_mutually_exclusive_group(required=True)

        excl.add_argument('-h', '--help', action="store_true")

        for action in CONSTANTS.ACTIONS:
            data = CONSTANTS.USAGES[action]
            excl.add_argument(data['args']['short'],
                              data['args']['long'],
                              **data['kwargs'])

        return True



        excl.add_argument('-ts', '--top-senders',
                          nargs='?', type=int,
                          default=10,
                          help=CONSTANTS.USAGES[CONSTANTS.TOP_SENDERS])

        excl.add_argument('-b', '--boxes',
                          action='store_true',
                          help=CONSTANTS.USAGES[CONSTANTS.LIST_BOXES])

        excl.add_argument('-f', '--from',
                          nargs=1, type=str,
                          help=CONSTANTS.USAGES[CONSTANTS.RECEIVED_FROM])

        excl.add_argument('-t', '--to',
                          nargs=1, type=str,
                          help=CONSTANTS.USAGES[CONSTANTS.SENT_TO])

        excl.add_argument('-r', '--read',
                          nargs=1, type=int,
                          help=CONSTANTS.USAGES[CONSTANTS.READ_EMAIL])

        excl.add_argument('-di', '--delete-id',
                          nargs='+', type=int,
                          help=CONSTANTS.USAGES[CONSTANTS.DELETE_ID])

        excl.add_argument('-df', '--delete-from',
                          nargs=1, type=str,
                          help=CONSTANTS.USAGES[CONSTANTS.DELETE_FROM])

        excl.add_argument('-q', '--quit',
                          action='store_true',
                          help=CONSTANTS.USAGES[CONSTANTS.LOGOUT])


    def parse_answer(self, answer):
        try:
            parsed = self.parser.parse_args(answer.split())
        except SystemExit as e:
            return False

        for action in CONSTANTS.ACTIONS:
            if parsed[action]:
                print(action)



    def command_center(self):
        while self.status == 'ON':
            question = ("-h or --help to get a list of different actions\n\n"
                        "What action would you like to do ?")
            answer = self._print.main_menu(question)

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


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
from src.cacher import Cacher


class Motor:

    def __init__(self, config, connections=15):
        self.last_search = None
        self.status = 'ON'
        self._print = Printer()
        self._cacher = Cacher()
        self.max_open_connections = connections
        self.mailboxes = None
        self.errors = {}

        self._parse_config(config)

        self._initialize_email_engine()
        self._connect()

        self._create_parser()
        self._assign_arg_to_command()
        self._create_help_message()


    def run(self):
        self.get_all_mailboxes(display_help=False)
        self.select_bigger_mailbox()
        self.display_help()
        self.command_center()


    def select_bigger_mailbox(self):
        bigger = max(self.mailboxes, key=lambda x: self.mailboxes[x])
        self.email.select_inbox(bigger)


    def _create_help_message(self):
        template = "{s:3}  {l:15}\t{t:10}\t{h}\n"

        msg = '\n[OPTIONS]\n\n'
        for action in CONSTANTS.ACTIONS:
            if action == CONSTANTS.SPACE:
                msg += '\n'
                continue

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


    def _create_parser(self):
        self.parser = argparse.ArgumentParser(prog=CONSTANTS.PROGRAM_NAME,
                                              add_help=False)

        excl = self.parser.add_mutually_exclusive_group(required=True)

        for action in CONSTANTS.ACTIONS:
            if not action:
                continue

            data = CONSTANTS.USAGES[action]
            excl.add_argument(data['args']['short'],
                              data['args']['long'],
                              **data['kwargs'])


    def _assign_arg_to_command(self):
        self.commands = {
            CONSTANTS.TOP_SENDERS: self.summarize_per_sender,
            CONSTANTS.LIST_BOXES: self.get_all_mailboxes,
            CONSTANTS.SELECT_BOX: self.get_selected_mailbox,
            CONSTANTS.RECEIVED_FROM: self.get_emails_from,
            CONSTANTS.SENT_TO: self.get_emails_sent_to,
            CONSTANTS.READ_EMAIL: self.read_email,
            CONSTANTS.DELETE_ID: self.delete_emails_by_id,
            CONSTANTS.DELETE_FROM: self.delete_emails_by_sender,
            CONSTANTS.DELETE_CACHE: self.delete_cache,
            CONSTANTS.HELP: self.display_help,
            CONSTANTS.LOGOUT: self.logout
        }


    def display_help(self):
        print(self.help_message)


    def delete_cache(self):
        self._cacher.delete_cache(self.email_address)


    def read_email(self, id_):
        id_ = str(id_[0]).encode()
        email_message = self.email.get_selected_emails(id_, self.errors)
        self._check_errors()

        self._print.print_one_email(email_message)


    def parse_answer(self, answer):
        try:
            f = io.StringIO()
            with contextlib.redirect_stderr(f):
                parsed = self.parser.parse_args(answer.split())
        except SystemExit:
            print("Incorrect usage. Type -h for help !")
            return False

        parsed = vars(parsed)

        for action in CONSTANTS.ACTIONS:
            if not action:
                continue

            if parsed[action]:
                arg = parsed[action]
                if isinstance(arg, bool):
                    return self.commands[action]()
                return self.commands[action](arg)


    def command_center(self):
        while self.status == 'ON':
            answer = self._print.main_menu()

            if answer:
                self.parse_answer(answer)


    def summarize_per_sender(self, top):

        data = self.email.get_all_emails(self.errors)
        self._check_errors()

        log.info('{} emails successfully analysed'.format(len(data)))
        log.info('Below is the top {} senders'.format(top))

        if data:
            self.last_search = self._print.summary_by_top_senders(data, top)


    def delete_emails_by_sender(self, email_addresses):
        self.email.delete_emails_by_sender(email_addresses)


    def delete_emails_by_id(self, ids):
        self.email.delete_emails_by_id(ids)


    def _check_errors(self):
        if self.errors:
            self._print.errors(self.errors)
            self.errors = {}


    def get_emails_sent_to(self, email_address):
        self.get_selected_mailbox('Sent')
        email_address = email_address[0]
        emails_list = self.email.search_filtered(email_address,
                                                 'TO',
                                                 self.errors)
        self._check_errors()
        self._display_emails(emails_list)


    def get_emails_from(self, email_address):
        email_address = email_address[0]
        emails_list = self.email.search_filtered(email_address,
                                                 'FROM',
                                                 self.errors)
        self._check_errors()
        self._display_emails(emails_list)


    def _display_emails(self, emails_list):
        if not emails_list:
            log.info("No emails were retrieved")
        else:
            log.info("{} emails were retrieved".format(len(emails_list)))
            self._print.display_emails(emails_list)
            self.last_search = emails_list


    def get_summary_email_by_id(self, ids):
        return self.email.fetch_header_email(ids)


    def get_full_email_by_id(self, ids):
        res = self.email.fetch_full_email(ids, self.errors)
        self._check_errors()
        return res


    def get_selected_mailbox(self, mailbox_id):
        if not self.mailboxes:
            self.get_all_mailboxes(display_help=False)

        mailbox_id = int(mailbox_id[0])
        if not (0 <= mailbox_id < len(self.mailboxes)):
            log.info("Invalid input, please try again")
            return False

        mailbox = list(self.mailboxes.keys())[mailbox_id]
        res = self.email.select_inbox(mailbox.encode())

        if b'Failure' in res:
            log.info("Could not find the mailbox: {}".format(mailbox))
        else:
            log.info("Connected to {} !".format(mailbox))
            log.info("{} emails in that mailbox".format(res.decode()))


    def get_all_mailboxes(self, display_help=True):
        """
        Get a list of all the available folders in the mail box
        """
        self.mailboxes = self.email.get_mailboxes()

        if display_help:
            self._print.print_mailboxes(self.mailboxes)


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
        log.info("Will process a few more things for some seconds")


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


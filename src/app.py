import time
import datetime
import argparse
import re
import io
import contextlib

from collections import Counter

from src import email_engine
from src import CONSTANTS
from src.logger import log
from src.printer import Printer
from src.cacher import Cacher


class Motor:
    def __init__(self, config):
        self.config = config
        self.last_search = None
        self.status = "ON"
        self._print = Printer()
        self._cacher = Cacher()
        self.max_open_connections = None
        self.mailboxes = None
        self.errors = {}
        self.timestamp = datetime.datetime.now()

        self.choose_account()
        self._parse_config()

        self._initialize_email_engine()
        self._connect()

        self._create_parser()
        self._assign_arg_to_command()
        self._create_help_message()

    def run(self):
        """
        Put the user in its biggest mailbox and display the help message
        before running the command center
        """
        self.get_all_mailboxes(display_help=False)
        self.select_bigger_mailbox()
        self.display_help()
        self.command_center()

    def select_bigger_mailbox(self):
        """
        Search through all mailboxes the biggest one and log in it
        """
        bigger = max(self.mailboxes, key=lambda x: self.mailboxes[x])
        self.email.select_inbox(bigger)

    def _create_help_message(self):
        """
        Create the help message to display to user when needed
        """
        template = "{s:3}  {l:15}\t{t:10}\t{h}\n"

        msg = "\n[OPTIONS]\n\n"
        for action in CONSTANTS.ACTIONS:
            if action == CONSTANTS.SPACE:
                msg += "\n"
                continue

            data = CONSTANTS.USAGES[action]

            if "type" in data["kwargs"]:
                type_ = re.search("'(\w+)'", repr(data["kwargs"]["type"]))
                type_ = type_[1]

                if data["kwargs"]["nargs"] in ("*", "+"):
                    type_ = "[{} ...]".format(type_)
            else:
                type_ = ""

            short, full = data["args"]["short"], data["args"]["long"]

            for part in data["kwargs"]["help"].split("\n"):
                msg += template.format(s=short, l=full, t=type_, h=part)

                short, full, type_ = "", "", ""

        self.help_message = msg

    def _create_parser(self):
        """
        Create the parser we will use to parse arguments.
        It will be used interactively so had to customize a bunch of things
        like the help message
        """
        self.parser = argparse.ArgumentParser(
            prog=CONSTANTS.PROGRAM_NAME, add_help=False
        )

        excl = self.parser.add_mutually_exclusive_group(required=True)

        for action in CONSTANTS.ACTIONS:
            if not action:
                continue

            data = CONSTANTS.USAGES[action]

            if not data["actif"]:
                continue

            excl.add_argument(
                data["args"]["short"], data["args"]["long"], **data["kwargs"]
            )

    def _assign_arg_to_command(self):
        """
        Register all commands that can be actionnated by the user
        """
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
            CONSTANTS.RESET: self.reset,
            CONSTANTS.LOGOUT: self.logout,
        }

    def display_help(self):
        """
        Print the help message
        """
        print(self.help_message)

    def delete_cache(self):
        """
        Delete the cache for the current user
        """
        self._cacher.delete_cache(self.email_address)

    def read_email(self, email_id):
        """
        Read the email provided by its id
        """
        email_id = str(email_id[0]).encode()
        email_message = self.email.get_selected_emails(email_id, self.errors)
        self._check_errors()

        self._print.print_one_email(email_message)

    def parse_answer(self, answer):
        """
        Parse the command received from user.
        We use the parser interactively so we make sure the system doesn't exit
        on error and that default error message doesn't show up
        """
        try:
            f = io.StringIO()
            with contextlib.redirect_stderr(f):
                parsed = self.parser.parse_args(answer.split())
        except SystemExit:
            print("Incorrect usage. Type -h for help !")
            return False

        parsed = vars(parsed)

        now = datetime.datetime.now()
        if (now - self.timestamp).total_seconds() > 60:
            self.email.check_connections()
        self.timestamp = now

        for action in CONSTANTS.ACTIONS:
            if not action:
                continue

            if parsed[action]:
                arg = parsed[action]
                if isinstance(arg, bool):
                    return self.commands[action]()
                return self.commands[action](arg)

    def command_center(self):
        """
        Infinite loop for receiving actions from user
        """
        while self.status == "ON":
            answer = self._print.main_menu()

            if answer:
                try:
                    self.parse_answer(answer)
                except Exception as error:
                    if "Errno 32" in str(error):
                        self.reset()
                        continue

                    print(
                        "An unexpected error happened:\n"
                        "{}\n"
                        "If it's related to connections, you can reset them"
                        " with the command -rc".format(error)
                    )

    def summarize_per_sender(self, top):
        """
        Summarize all emails per top senders
        """
        data = self.email.get_all_emails(self.errors)
        self._check_errors()

        log.info("\n{} emails successfully analysed".format(len(data)))
        log.info("Below is the top {} senders".format(top))

        if data:
            self.last_search = self._print.summary_by_top_senders(data, top)

    def delete_emails_by_sender(self, email_addresses):
        """
        Delete all emails received from email_address
        and available in current mailbox
        """
        self.look_for_delete_mailboxes()

        if all(email.isdigit() for email in email_addresses):
            email_addresses = [self.last_search[int(ind)-1][0]
                               for ind in email_addresses]
            print(email_addresses)

        self.email.delete_emails_by_sender(email_addresses)

    def delete_emails_by_id(self, email_ids):
        """
        Delete the emails whose IDs has been provided
        """
        self.look_for_delete_mailboxes()
        self.email.delete_emails_by_id(email_ids)

    def look_for_delete_mailboxes(self):
        if not self.email.delete_mailbox:
            mailbox = self._print.ask_for_delete_mailbox(self.mailboxes)
            self.email.delete_mailbox = mailbox

    def _check_errors(self):
        """
        Display the errors if any error has been caught
        """
        if self.errors:
            self._print.errors(self.errors)
            self.errors = {}

    def get_emails_sent_to(self, email_address):
        """
        Get and display all the emails sent to a specific person
        """
        self.get_selected_mailbox("Sent")
        email_address = email_address[0]
        emails_list = self.email.search_filtered(
            email_address, "TO", self.errors
        )
        self._check_errors()
        self._display_emails(emails_list)

    def get_emails_from(self, email_address):
        """
        Get and display all the emails received from a specific person
        """
        email_address = email_address[0]
        emails_list = self.email.search_filtered(
            email_address, "FROM", self.errors
        )
        self._check_errors()
        self._display_emails(emails_list)

    def _display_emails(self, emails_list):
        """
        Display all emails provided in the emails_list
        """
        if not emails_list:
            log.info("No emails were retrieved")
        else:
            log.info("{} emails were retrieved".format(len(emails_list)))
            self._print.display_emails(emails_list)
            self.last_search = emails_list

    def get_summary_email_by_id(self, ids):
        """
        I think this function is not used anymore. To be deletel if useless ?
        """
        return self.email.fetch_header_email(ids)

    def get_full_email_by_id(self, ids):
        """
        useless ?
        """
        res = self.email.fetch_full_email(ids, self.errors)
        self._check_errors()
        return res

    def get_selected_mailbox(self, mailbox_id):
        """
        Log in the selected mailbox
        """
        if not self.mailboxes:
            self.get_all_mailboxes(display_help=False)

        mailbox_id = int(mailbox_id[0])
        if not (0 <= mailbox_id < len(self.mailboxes)):
            log.info("Invalid input, please try again")
            return False

        mailbox = list(self.mailboxes.keys())[mailbox_id]
        res = self.email.select_inbox(mailbox.encode())

        if b"Failure" in res:
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
            self._print.print_mailboxes(
                self.mailboxes, self.email.current_mailbox
            )

    def get_last_emails(self, nb):
        """
        Get & display a sumary of the last nb emails received
        """
        pass

    def get_storage_info(self):
        """
        Display memory usage for the whole account
        """
        return self.email.get_quota()

    def reset(self):
        self.email.logout()
        self._connect()

    def logout(self):
        """
        Log out all the active connections
        """
        self.email.logout()
        log.info("Connexion successfully closed !")
        self.status = "OFF"

    def _connect(self):
        """
        Initialize the email engine and connect to all connections
        """
        log.info("Logging in as {}...".format(self.email_address))
        self.email.initialize(
            self.host_name,
            self.port,
            self.email_address,
            self.password,
            self.max_open_connections,
        )
        log.info("Logged in !")
        log.info("Will process a few more things for some seconds")

    def _initialize_email_engine(self):
        """
        Create an instance of the email_engine
        """
        if self.logins["server_type"] == "imap":
            self.email = email_engine.IMAP_SSL()
        else:
            raise TypeError(
                "The app only accepts imap server as of now.\n"
                "Be sure the config file is correct"
            )

    def choose_account(self):
        if len(self.config.sections()) == 1:
            account = self.config.sections()[0]
        else:
            account = self._print.choose_account(self.config)

        self.logins = account

    def _parse_config(self):
        """
        Parse the config yaml file
        """
        self.host_name = self.logins["server_address"]
        self.port = self.logins["port"]
        self.email_address = self.logins.name
        self.password = self.logins["password"]
        self.server_type = self.logins["server_type"]
        self.ssl = self.logins.getboolean("ssl")
        self.max_open_connections = int(self.logins["max_open_connections"])

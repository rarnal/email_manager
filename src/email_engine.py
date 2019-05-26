import time
import imaplib
import email
import email.parser
import email.message
import email.policy
import email.header
import email.utils
from concurrent import futures
from collections import deque
import re

# import smtplib

import ssl


from progressBar import ProgressCounter
from src import CONSTANTS
from src.logger import log
from src.cacher import Cacher


class IMAP_SSL:
    def __init__(self):
        self.mail = None
        self.cache = Cacher()

        self.current_mailbox = None
        self.delete_mailbox = None

    def initialize(
        self, host_name, port, email_address, password, max_conns=10
    ):
        """
        Initialize nb connections to the host and log them in
        """
        self.host_name = host_name
        self.port = port
        self.email_address = email_address
        self.password = password

        self.max_connexions = max_conns

        self.connections = self._create_connection(self.max_connexions)

    def _create_connection(self, nb=1):
        """
        Create nb new connections
        """
        bar = ProgressCounter(nb, "Creating connections")
        connections = deque()

        for _ in range(nb):
            connections.append(self._open_one_connection())
            bar += 1

        return connections

    def _open_one_connection(self):
        """
        Create and return a new connection instance
        """
        connection = imaplib.IMAP4_SSL(
            host=self.host_name, port=self.port, ssl_context=ssl.SSLContext()
        )
        self.login(connection)
        return connection

    def login(self, connections):
        """
        Login in the provided connection instance
        Make sure we are in a AUTH mode before leaving the function
        Might be safer to add some kind of exception if we can't login...
        """
        if not isinstance(connections, (deque, list, tuple, set)):
            connections = [connections]

        for connection in connections:

            while connection.state == "NONAUTH":
                connection.login(
                    user=self.email_address, password=self.password
                )
                time.sleep(0.1)

            while connection.state == "AUTH":
                connection.select()
                time.sleep(0.1)

        return True

    def check_connections(self):
        """
        Check if all connections are still functionnal.
        If not, create a new one
        """
        for i, conn in enumerate(self.connections):
            if conn.check()[0] != "OK":
                self.connections[i] = self._open_one_connection()

    def logout(self):
        """
        Close all connections and quit
        """
        for connection in self.connections:
            connection.close()
            connection.logout()
        return True

    def get_mailboxes(self):
        """
        Get a list of all mailboxes
        Will also look for the mailbox where deleted emails go
        (that part is extremely ugly and subjects to bugs - to be FIXED)
        """
        _, res = self.connections[0].list()
        compiler = """(\(.+\))\s(".+")\s("?.+"?)"""
        boxes = {}

        for mailbox in res:
            here = re.match(compiler, mailbox.decode())
            mailbox_name = here[3]

            if mailbox_name not in ('"[Gmail]"',):
                total_emails = self.connections[0].select(mailbox_name)[1][0]
                boxes[mailbox_name] = int(total_emails)
                if mailbox_name.lower() in CONSTANTS.DELETE_MAILBOXES:
                    self.delete_mailbox = mailbox_name
                    # TODO: fix issue we might have if the delete inbox
                    # is not in that DELETE_MAILBOXES list

        self.select_inbox(
            mailbox=self.current_mailbox, connections=self.connections[0]
        )
        return boxes

    def select_inbox(self, mailbox=None, connections=None):
        """
        Log in the provided mailbox if provided (other default one)
        The operation can be done on a specific connection, or all of them
        if no connections have been provided
        """
        if not connections:
            connections = self.connections

        if not isinstance(connections, (tuple, list, deque)):
            connections = [connections]

        if not mailbox:
            self.current_mailbox = None
            for conn in connections:
                _, res = conn.select()
        else:
            self.current_mailbox = mailbox
            for conn in connections:
                _, res = conn.select(mailbox)

        return res[0]

    def delete_emails_by_sender(self, email_addresses):
        """
        Delete all emails sent from the provided email addresses
        Only the emails in the current mailbox are concerned
        """
        ids = []
        for email_address in email_addresses:
            ids += self._search("FROM", email_address)[0].split()
        self.delete_emails_by_id(ids)

    def delete_emails_by_id(self, email_ids):
        """
        Delete a bunch of emails whose ID has been provided by the user
        """
        if isinstance(email_ids, (int, bytes)):
            email_ids = [email_ids]

        if not email_ids:
            return None

        bar = ProgressCounter(
            len(email_ids),
            "Deleting {} emails".format(len(email_ids)),
            percentage=True,
        )
        # I haven't been able delete emails by threading
        # Getting a error 32 broken pipe error
        # Processing them one by one might be slow but at least it works
        for email_id in email_ids:
            self._delete_one_email(email_id)
            bar += 1

        self._expunge_mailbox()

        cached = self._get_cached_email_headers()
        cached = [msg for msg in cached if msg.id not in email_ids]
        self.cache.add(
            cached, self.email_address, self.current_mailbox, overwrite=True
        )

    def _delete_one_email(self, email_id):
        """
        Mark a single email as to be deleted by:
            moving it to the "delete" mailbox
            flagging it as "deleted"
        """
        self.connections[0].uid("copy", email_id, self.delete_mailbox)
        self.connections[0].uid("store", email_id, "+FLAGS", "\\Deleted")

    def _expunge_mailbox(self):
        """
        Delete all emails flagged as "\\Deleted"
        """
        _, res = self.connections[0].expunge()

    def get_quota(self):
        """
        Get the memory size current usage and treshold for the whole account
        """
        _, res = self.connections[0].getquotaroot("inbox")
        return res

    def _search(self, *args):
        """
        Execute a search and return the matching email ids
        """
        _, res = self.connections[0].uid("search", *args)
        return res

    def get_last_emails(nb):
        """
        Retrive last xx emails received in the default mailbox (inbox)
        """

        self.sele

    def search_filtered(self, string, filter, errors):
        """
        Return headers of all emails matching the given search.
        Newly downloaded emails will be added to the cache.
        """
        email_ids = self._search(filter, string)
        if not email_ids[0]:
            return None

        email_ids = set(email_ids[0].split())

        cached_emails = self._get_cached_email_headers()
        cached_emails_filtered = []

        for cached_email in cached_emails:
            if cached_email.id in email_ids:
                cached_emails_filtered.append(cached_email)
                email_ids.discard(cached_email.id)

        downloaded_emails = self._fetch_emails(
            email_ids, "(RFC822.HEADER)", errors
        )

        self.cache.add(
            downloaded_emails, self.email_address, self.current_mailbox
        )

        return downloaded_emails + cached_emails_filtered

    def get_all_emails(self, errors):
        """
        Return headers of all emails available in the current mailbox.
        Newly downladed emails will be added to the cache
        """
        email_ids = self._search(None, "ALL")
        if not email_ids[0]:
            return None

        email_ids = set(email_ids[0].split())

        cached_emails = self._get_cached_email_headers()

        to_return = []

        for cached_email in cached_emails:
            if cached_email.id in email_ids:
                email_ids.discard(cached_email.id)
                to_return.append(cached_email)

        downloaded_emails = self._fetch_emails(
            email_ids, "(RFC822.HEADER)", errors
        )

        self.cache.add(
            downloaded_emails, self.email_address, self.current_mailbox
        )

        return downloaded_emails + to_return

    def get_selected_emails(self, ids, errors):
        """
        Download full content of provided email ids
        """
        downloaded_emails = self._fetch_emails(ids, "(RFC822)", errors)
        return downloaded_emails

    def _get_cached_email_headers(self):
        """
        Return all the emails we have cached for the current user
        """
        emails = self.cache.load(self.email_address, self.current_mailbox)
        return emails

    def _fetch_emails(self, email_ids, formatting, errors):
        """
        Downloads and parse emails contained in email_ids.
        Formatting might include the body or headers only.
        """
        if not email_ids:
            return []

        if isinstance(email_ids, bytes):
            email_ids = [email_ids]

        raw_emails = self._download_emails(email_ids, formatting, errors)

        if not raw_emails:
            return []

        return self._parse_emails(raw_emails, errors)

    def _download_emails(self, email_ids, formatting, errors):
        """
        Asynchronously download emails contained in email_ids.
        """
        out = []
        log.info("Processing {} emails...".format(len(email_ids)))
        bar = ProgressCounter(total=len(email_ids), name="Downloading emails")

        with futures.ThreadPoolExecutor(len(self.connections)) as executor:

            todo = (
                executor.submit(self._fetch_one_email, email_id, formatting)
                for email_id in email_ids
            )

            for ready in futures.as_completed(todo):
                try:
                    res = ready.result()
                except Exception as error:
                    error = "Download error: " + str(error)
                    if error not in errors:
                        errors[error] = 0
                    errors[error] += 1
                    res = None

                if res:
                    out.append(res)

                bar += 1

        return out

    def _parse_emails(self, raw_emails, errors):
        """
        Synchronously parse a bunch of emails
        """
        parsed_emails = []
        bar = ProgressCounter(len(raw_emails), "Parsing emails")

        for email_id, email_raw in raw_emails:
            try:
                parsed_emails.append(self._parse_email(email_id, email_raw))
            except Exception as error:
                error = "Parsing error: " + str(error)
                if error not in errors:
                    errors[error] = 0
                errors[error] += 1
            bar += 1

        return parsed_emails

    def _fetch_one_email(self, email_id, formatting):
        """
        Download an email and return its raw content.
        We are using uid instead of fetch because IDs we get from fetch
        might change over time, while the IDs we get from uid are permanent
        """
        with OpenConn(self.connections) as connection:
            _, email_raw = connection.uid("fetch", email_id, formatting)
            if not email_raw[0]:
                return False
            email_raw = (email_id, email_raw[0][1])

        # this 121 is a result I get sometimes. I don't know the reason.
        if email_raw[1] == 121:
            return self._fetch_one_email(email_id, formatting)

        return email_raw

    def _parse_email(self, email_id, email_raw):
        """
        Parse the content of an email.
        The email id will be attached to the returned Email object
        """
        parsed_email = email.parser.BytesParser().parsebytes(email_raw)

        parsed_email = self._transform_parsed_email(email_id, parsed_email)
        return parsed_email

    def _transform_parsed_email(self, email_id, parsed_email):
        """
        Transform the EmailMessage into a Email class
        Rework some data to ease stuff later on
        """
        transformed_email = Email()

        if isinstance(email_id, str):
            email_id = email_id.encode()
        elif isinstance(email_id, int):
            email_id = str(email_id).encode()
        transformed_email.id = email_id

        # issue to dig: sometime the parser_email['From'] is not an str
        # making sure it's actually an string prevent some errors to happen
        # while parsing the header
        temp = email.utils.parseaddr(str(parsed_email["From"]))
        transformed_email.sender = temp[1]

        temp = email.utils.parseaddr(str(parsed_email["To"]))
        transformed_email.receiver = temp[1]

        temp = email.utils.parseaddr(str(parsed_email["Cc"]))
        transformed_email.cc = temp[1]

        temp = email.utils.parseaddr(str(parsed_email["Bcc"]))
        transformed_email.bcc = temp[1]

        temp = email.utils.parsedate_to_datetime(parsed_email["Date"])
        temp = temp.replace(tzinfo=None)
        transformed_email.date = temp

        try:
            temp = email.header.decode_header(parsed_email["Subject"])
        except TypeError:
            if parsed_email["Subject"]:
                temp = parsed_email["Subject"]
            else:
                temp = ""
        else:
            temp = temp[0][0]
            if isinstance(temp, bytes):
                temp = temp.decode(errors="replace")
            if not isinstance(temp, (bytes, str)):
                temp = ""

        transformed_email.subject = temp

        temp = self._get_email_content(parsed_email)
        transformed_email.content = temp

        return transformed_email

    def _get_email_content(self, parsed_email):
        """
        Parse an email content through the payload function
        Will replace actual images with the word "IMAGE"
        """
        type_ = parsed_email.get_content_maintype()

        if type_ == "text" and parsed_email.get_content_subtype() == "plain":
            return parsed_email.get_payload(decode=True)
        elif "image" in type_:
            return b" [IMAGE] "
        elif "multipart" in type_:
            content = b""
            for part in parsed_email.get_payload():
                content += self._get_email_content(part)
            return content
        else:
            return b""


class Email:
    """
    Custom Email class.
    Lighter, easier, and only contain the stuff I need to use for caching
    """

    def __init__(self):
        self.id = None
        self.sender = None
        self.receiver = None
        self.cc = None
        self.bcc = None
        self.date = None
        self.subject = None
        self.content = None
        self.size = None

    def __eq__(self, other):
        if isinstance(other, int):
            return self.id == str(other).encode()
        elif isinstance(other, type(self)):
            return self.id == other.id
        elif isinstance(other, bytes):
            return self.id == other
        elif isinstance(other, str):
            return self.id == other.encode()
        else:
            raise NotImplementedError

    def __str__(self):
        print("id", self.id)
        print("sender", self.sender)
        print("date", self.date)
        print("subject", self.subject)
        print("content", self.content.decode())
        return ""


class OpenConn:
    """
    Context manager class for threading and being sure a connection instance
    won't be use by several workers
    """

    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        self.connection = self.conn.pop()
        return self.connection

    def __exit__(self, here, there, that):
        self.conn.appendleft(self.connection)

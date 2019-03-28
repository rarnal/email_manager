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
import datetime
import re
# import smtplib

import ssl

import sys

from progressBar import ProgressBar
from src.logger import log
from src.cacher import Cacher


class IMAP_SSL:

    def __init__(self):
        self.mail = None
        self.cache = Cacher()


    def initialize(self, host_name, port,
                  email_address, password,
                  max_conns=10):

        self.host_name = host_name
        self.port = port
        self.email_address = email_address
        self.password = password

        self.max_connexions = max_conns

        self.connections = self._create_connection(self.max_connexions)


    def _create_connection(self, nb=1):
        bar = ProgressBar(nb, "Creating {} connexions...".format(nb), size=40)
        connections = deque()
        for _ in range(nb):
            connection = imaplib.IMAP4_SSL(host=self.host_name,
                                           port=self.port,
                                           ssl_context=ssl.SSLContext())
            self.login(connection)
            connections.append(connection)
            bar += 1
        return connections


    def login(self, connections):
        if not isinstance(connections, (list, tuple, set)):
            connections = [connections]

        for connection in connections:

            while connection.state == "NONAUTH":
                connection.login(user=self.email_address,
                                 password=self.password)
                time.sleep(0.1)

            while connection.state == "AUTH":
                connection.select()
                time.sleep(0.1)

        return True


    def logout(self):
        for connection in self.connections:
            connection.logout()
        return True


    def get_mailboxes(self):
        _, res = self.connections[0].list()
        compiler = """(\(.+\))\s(".+")\s(".+")"""
        boxes = {}
    
        n = 1

        for mailbox in res:
            here = re.match(compiler, mailbox.decode())

            if here[3] not in ('"[Gmail]"'):
                total_emails = self.select_inbox(box=here[3])
                boxes[n] = (here[3], int(total_emails))
                n += 1

        return boxes


    def select_inbox(self, box=None, connections=None):
        if not connections:
            connections = self.connections

        if not isinstance(connections, (tuple, list, deque)):
            connections = [connections]

        if not box:
            for conn in connections:
                _, res = conn.select()
        else:
            for conn in connections:
                _, res = conn.select(box)

        return res[0]


    def get_quota(self):
        _, res = self.connections[0].getquotaroot('inbox')
        return res


    def _search(self, *args):
        _, res = self.connections[0].uid('search', *args)
        return res


    def search_filtered(self, string, filter):
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

        downloaded_emails = self._fetch_emails(email_ids, '(RFC822.HEADER)')
        self.cache.add(downloaded_emails, self.email_address)

        return downloaded_emails + cached_emails_filtered


    def get_all_emails(self):
        email_ids = self._search(None, 'ALL')
        if not email_ids[0]:
            return None

        email_ids = set(email_ids[0].split())

        cached_emails = self._get_cached_email_headers()

        for cached_email in cached_emails:
            if cached_email.id in email_ids:
                email_ids.discard(cached_email.id)

        downloaded_emails = self._fetch_emails(email_ids, '(RFC822.HEADER)')
        self.cache.add(downloaded_emails, self.email_address)

        return downloaded_emails + cached_emails


    def get_selected_emails(self, ids):
        downloaded_emails = self._fetch_emails(ids, '(RFC822)')
        return downloaded_emails


    def _get_cached_email_headers(self):
        emails = self.cache.load(self.email_address)
        return emails


    def _fetch_emails(self, email_ids, formatting):
        if not email_ids:
            return []

        if isinstance(email_ids, bytes):
            email_ids = [email_ids]

        raw_emails = self._download_emails(email_ids, formatting)

        if not raw_emails:
            return []

        return self._parse_emails(raw_emails)


    def _download_emails(self, email_ids, formatting):
        out = []
        log.info("Processing {} emails...".format(len(email_ids)))
        bar = ProgressBar(len(email_ids), "Downloading new emails...", size=40)

        with futures.ThreadPoolExecutor(max(1, self.max_connexions)) as executor:

            todo = (
                executor.submit(self._fetch_one_email, email_id, formatting)
                for email_id in email_ids
            )

            for ready in futures.as_completed(todo):
                try:
                    res = ready.result()
                except Exception as error:
                    # the 100 spaces help to "erase" the progress bar
                    log.error("One email was not correctly downloaded: "
                              "{}{}".format(error, ' ' * 100))
                    res = None

                if res:
                    out.append(res)

                bar += 1

        return out


    def _parse_emails(self, raw_emails):
        parsed_emails = []
        bar = ProgressBar(len(raw_emails), "Parsing emails...", size=40)

        for email_id, email_raw in raw_emails:
            try:
                parsed_emails.append(self._parse_email(email_id, email_raw))
            except Exception as error:
                log.error("One email could not be parsed:{}\n"
                          "{}".format(' ' * 100, error))
            bar += 1

        return parsed_emails


    def _fetch_one_email(self, email_id, formatting):
        with OpenConn(self.connections) as connection:
            _, email_raw = connection.uid('fetch', email_id, formatting)
            if not email_raw[0]:
                return False
            email_raw = (email_id, email_raw[0][1])
    
        # this 121 is a result I get sometimes. I don't know the reason.
        if email_raw[1] == 121:
            return self._fetch_one_email(email_id, formatting)

        return email_raw


    def _parse_email(self, email_id, email_raw):
        try:
            parsed_email = email.parser \
                                .BytesParser() \
                                .parsebytes(email_raw)
        except AttributeError as error:
            raise AttributeError("{} : {}\n{}".format(email_id,
                                                      error,
                                                      email_raw))

        parsed_email = self._transform_parsed_email(email_id, parsed_email)
        return parsed_email


    def _transform_parsed_email(self, email_id, parsed_email):
        transformed_email = Email()

        if isinstance(email_id, str):
            email_id = email_id.encode()
        elif isinstance(email_id, int):
            email_id = str(email_id).encode()
        transformed_email.id = email_id

        # issue to dig: sometime the parser_email['From'] is not an str
        # making sure it's actually an string prevent some errors to happen
        # while parsing the header
        temp = email.utils.parseaddr(str(parsed_email['From']))
        transformed_email.sender = temp[1]

        temp = email.utils.parseaddr(str(parsed_email['To']))
        transformed_email.receiver = temp[1]

        temp = email.utils.parseaddr(str(parsed_email['Cc']))
        transformed_email.cc = temp[1]

        temp = email.utils.parseaddr(str(parsed_email['Bcc']))
        transformed_email.bcc = temp[1]

        temp = email.utils.parsedate_to_datetime(parsed_email['Date'])
        temp = temp.replace(tzinfo=None)
        transformed_email.date = temp

        try:
            temp = email.header.decode_header(parsed_email['Subject'])
        except TypeError:
            if parsed_email['Subject']:
                temp = parsed_email['Subject']
            else:
                temp = ''
        else:
            temp = temp[0][0]
            if isinstance(temp, bytes):
                temp = temp.decode(errors='replace')
            if not isinstance(temp, (bytes, str)):
                temp = ''

        transformed_email.subject = temp

        temp = self._get_email_content(parsed_email)
        transformed_email.content = temp

        return transformed_email


    def _get_email_content(self, parsed_email):
        type_ = parsed_email.get_content_maintype()

        if type_ == 'text' and parsed_email.get_content_subtype() == 'plain':
                return parsed_email.get_payload(decode=True)
        elif 'image' in type_:
            return b" [IMAGE] "
        elif 'multipart' in type_:
            content = b''
            for part in parsed_email.get_payload():
                content += self._get_email_content(part)
            return content
        else:
            return b''



class Email:
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
        print('id', self.id)
        print('sender', self.sender)
        print('date', self.date)
        print('subject', self.subject)
        print('content', self.content.decode())
        return ''


class OpenConn():
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        self.connection = self.conn.pop()
        return self.connection

    def __exit__(self, here, there, that):
        self.conn.appendleft(self.connection)


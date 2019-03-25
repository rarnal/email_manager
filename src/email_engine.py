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
        self.max_workers = 20

        self.connections = self._create_connection(self.max_connexions)


    def _create_connection(self, nb=1):
        bar = ProgressBar(nb, "Creating {} connexions...".format(nb))
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
        return res


    def select_inbox(self, box='Inbox'):
        _, res = self.connections[0].select(box)
        return res[0]


    def get_quota(self):
        _, res = self.connections[0].getquotaroot('inbox')
        return res


    def _search(self, *args):
        _, res = self.connections[0].uid('search', *args)
        return res


    def search_by_sender(self, sender_email_address):
        email_ids = self._search('FROM', sender_email_address)
        if not email_ids[0]:
            return None
        email_ids = email_ids[0].split()
        return self._fetch_emails(email_ids, '(RFC822)')


    def get_all_emails(self):
        email_ids = self._search(None, 'ALL')
        email_ids = set(email_ids[0].split())

        cached_emails = self.cache.load(self.email_address)

        if cached_emails:
            cached_ids = set(msg['id'].encode() for msg in cached_emails)
            email_ids -= cached_ids

        if email_ids:
            parsed_emails = self._fetch_emails(email_ids, '(RFC822.HEADER)')
            self.cache.dump(parsed_emails, self.email_address)

        return parsed_emails + cached_emails


    def _fetch_emails(self, email_ids, formatting):
        if isinstance(email_ids, str):
            email_ids = [email_ids]

        raw_emails = self._download_emails(email_ids, formatting)

        if not raw_emails:
            return None

        return self._parse_emails(raw_emails)


    def _download_emails(self, email_ids, formatting):
        out = []
        log.info("Processing {} emails...".format(len(email_ids)))
        bar = ProgressBar(len(email_ids), "Downloading emails...")

        with futures.ThreadPoolExecutor(self.max_connexions) as executor:

            todo = (
                executor.submit(self._fetch_one_email, email_id, formatting)
                for email_id in email_ids
            )

            for ready in futures.as_completed(todo):
                try:
                    out.append(ready.result())
                except Exception as error:
                    # the 100 spaces help to "erase" the progress bar
                    log.error("One email was not correctly downloaded: "
                              "{}{}".format(error, ' ' * 100))
                bar += 1

        return out


    def _parse_emails(self, raw_emails):
        parsed_emails = []
        bar = ProgressBar(len(raw_emails), "Parsing emails...")

        with futures.ThreadPoolExecutor(self.max_workers) as executor:

            todo = (
                executor.submit(self._parse_email, email_id, email_raw)
                for email_id, email_raw in raw_emails
            )

            for ready in futures.as_completed(todo):
                try:
                    parsed_emails.append(ready.result())
                except Exception as error:
                    log.error("One email was not correctly parsed: "
                              "{}{}".format(error, ' ' * 100))
                bar += 1

        return parsed_emails


    def _fetch_one_email(self, email_id, formatting):
        connection = self.connections.pop()
        _, email_raw = connection.uid('fetch', email_id, formatting)
        email_raw = (email_id, email_raw[0][1])
        self.connections.appendleft(connection)
        return email_raw


    def _parse_email(self, email_id, email_raw):
        parsed_email = email.parser \
                            .BytesParser() \
                            .parsebytes(email_raw)

        parsed_email = self._transform_parsed_email(email_id, parsed_email)

        return parsed_email


    def _transform_parsed_email(self, email_id, parsed_email):
        parsed_email['id'] = email_id.decode()

        # issue to dig: sometime the parser_email['From'] is not an str
        # making sure it's actually an string prevent some errore to happen
        # while parsing the header
        temp = email.utils.parseaddr(str(parsed_email['From']))[1]
        del parsed_email['From']
        parsed_email['From'] = temp

        temp = email.utils.parsedate_to_datetime(parsed_email['Date'])
        del parsed_email['Date']
        parsed_email['Date'] = temp

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

        del parsed_email['Subject']
        parsed_email['Subject'] = temp

        return parsed_email






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
# import smtplib

import ssl

import sys

from progressBar import ProgressBar
from logger import log


class Email:
    def __init__(self, data, formatting):
        self.read_email(data, formatting) 

    def read_email(self, data, formatting):

        raw_email = self.parse_email(data, formatting)

        self.content = self.get_email(raw_email)

        sender_info = self.get_sender(raw_email)
        self.sender_name = sender_info[0]
        self.sender_email = sender_info[1]

    @staticmethod
    def parse_email(data, formatting):

        if formatting == '(RFC822)':
            raw_email = email.parser \
                             .BytesParser(policy=email.policy.default) \
                             .parsebytes(data)
        elif formatting == '(ENVELOPE)':
            raw_email = email.parser \
                             .BytesHeaderParser(policy=email.policy.default) \
                             .parsebytes(data)
            print(type(data))
            raw_email = email.header.decode_header(data)
        print(raw_email)
        return raw_email

    @staticmethod
    def get_sender(raw_email):
        return email.utils.parseaddr(raw_email['From'])

    @staticmethod
    def get_email(raw_email):
        out = ""
        email_type = raw_email.get_content_maintype()
        if email_type == 'text':
            out = raw_email.get_payload()
        elif email_type == 'multipart':
            for part in raw_email.get_payload():
                if part.get_content_type() == 'text/plain':
                    out += part.get_payload()
                elif 'image' in part.get_content_type():
                    out += """\n\n***IMAGE***\n\n"""
        return out

    def __str__(self):
        return self.content



class IMAP_SSL:
    def __init__(self):
        self.mail = None

    def init_mail(self, host_name, port, email_address, password):
        self.host_name = host_name
        self.port = port
        self.email_address = email_address
        self.password = password

        self.max_connexions = 10
        self.conns = self._create_conn(login=True, nb=self.max_connexions)

    def _create_conn(self, login=True, nb=1):
        progress_bar = ProgressBar(nb, "Creating {} connexions...".format(nb))
        conns = deque()
        for _ in range(nb):
            conn = imaplib.IMAP4_SSL(
                host=self.host_name,
                port=self.port,
                ssl_context=ssl.SSLContext()
            )
            if login:
                self.login(conn)
            conns.append(conn)
            progress_bar += 1
        return conns

    def login(self, conns):
        if not isinstance(conns, (list, tuple, set)):
            conns = [conns]
        # TODO add some error checks about connexion issues
        for conn in conns:
            conn.login(user=self.email_address,
                       password=self.password)
            while conn.state != "SELECTED":
                conn.select()
                time.sleep(0.1)
        return True

    def logout(self):
        for conn in self.conns:
            conn.logout()
        return True

    def get_mailboxes(self):
        answer, res = self.conns[0].list()
        return res

    def select(self, box='Inbox'):
        answer, res = self.conns[0].select(box)
        return res[0]

    def get_quota(self):
        answer, res = self.conns[0].getquotaroot('inbox')
        return res

    def search(self, *args):
        _, res = self.conns[0].uid('search', *args)
        ids = res[0].split()
        return self._fetch_emails(ids, '(RFC822)')

    def get_all_emails(self):
        _, res = self.conns[0].uid('search', 'FROM', 'arnal.romain@gmail.com')
        ids = res[0].split()
        log.info("Getting ready to download {} emails...".format(len(ids)))
        synchrone = len(ids) < 10
        return ids, self._fetch_emails(ids, '(RFC822.HEADER)', synchrone)

    def _fetch_emails(self, ids, formatting, synchrone=False):
        if isinstance(ids, str):
            ids = [ids]

        out = []
        with futures.ThreadPoolExecutor(self.max_connexions-2) as executor:
            downloaded = []
            todo = (
                executor.submit(self._fetch_one_email, id, formatting)
                for id in ids
            )

            progress_bar = ProgressBar(len(ids), "Downloading emails...")
            for ready in futures.as_completed(todo):
                try:
                    downloaded.append(ready.result())
                except Exception as error:
                    log.error("One email was not correctly downloaded: "
                              "{}{}\nContinuing downloading..."
                              .format(error, ' '*50))
                              # 50 spaces to remove the bar status
                progress_bar += 1

            todo = (
                executor.submit(self.parse_email, id, res, formatting)
                for id, res in downloaded
            )
            progress_bar = ProgressBar(len(ids), "Parsing emails...")
            for ready in futures.as_completed(todo):
                try:
                    out.append(ready.result())
                except Exception as error:
                    log.error("One email was not correctly parsed: "
                              "{}{}".format(error, ' '*50))
                    pass
                progress_bar += 1
        return out

    def _fetch_one_email(self, id, formatting):
        conn = self.conns.pop() 
        _, res = conn.uid('fetch', id, formatting)
        res = (id, res[0][1])
        self.conns.appendleft(conn)
        return res

    def parse_email(self, id, raw_email, formatting):
        msg = email.parser \
                   .BytesParser() \
                   .parsebytes(raw_email)
        msg.id = id
        return msg

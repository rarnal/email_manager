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
from logger import log


class IMAP_SSL:
    def __init__(self):
        self.mail = None

    def init_mail(self, host_name, port, email_address, password):
        self.host_name = host_name
        self.port = port
        self.email_address = email_address
        self.password = password

        self.max_connexions = 10
        self.max_workers = 20
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
        _, res = self.conns[0].uid('search', None, 'ALL')
        ids = res[0].split()
        log.info("Getting ready to download {} emails...".format(len(ids)))
        return ids, self._fetch_emails(ids, '(RFC822.HEADER)')

    def _fetch_emails(self, ids, formatting):
        if isinstance(ids, str):
            ids = [ids]
        raw_emails = self._download_emails(ids, formatting)
        parsed_emails = self._parse_emails(raw_emails)
        return parsed_emails

    def _download_emails(self, ids, formatting):
        out = []
        progress_bar = ProgressBar(len(ids), "Downloading emails...")
        with futures.ThreadPoolExecutor(self.max_connexions-2) as executor:
            todo = (
                executor.submit(self._fetch_one_email, id, formatting)
                for id in ids
            )
            for ready in futures.as_completed(todo):
                try:
                    out.append(ready.result())
                except Exception as error:
                    log.error("One email was not correctly downloaded: "
                              "{}{}".format(error, ' '*50))
                              # 50 spaces to remove the bar status
                progress_bar += 1
        return out

    def _parse_emails(self, raw_emails):
        out = []
        progress_bar = ProgressBar(len(raw_emails), "Parsing emails...")
        with futures.ThreadPoolExecutor(self.max_workers) as executor:
            todo = (
                executor.submit(self._parse_email, id, res)
                for id, res in raw_emails
            )
            for ready in futures.as_completed(todo):
                try:
                    out.append(ready.result())
                except Exception as error:
                    log.error("One email was not correctly parsed: "
                              "{}{}".format(error, ' '*50))
                progress_bar += 1
        return out

    def _fetch_one_email(self, id, formatting):
        conn = self.conns.pop() 
        _, res = conn.uid('fetch', id, formatting)
        res = (id, res[0][1])
        self.conns.appendleft(conn)
        return res

    def _parse_email(self, id, raw_email):
        msg = email.parser \
                   .BytesParser() \
                   .parsebytes(raw_email)

        msg = self._transform_parsed_email(id, msg)
        return msg
    
    def _transform_parsed_email(self, id, msg):
        msg['id'] = id
        
        temp = email.utils.parseaddr(msg['From'])[1]
        del msg['From']
        msg['From'] = temp
    
        temp = email.utils.parsedate_to_datetime(msg['Date'])
        del msg['Date']
        msg['Date'] = temp
        
        return msg






import configparser
import os


def get_config(source=None):
    """
    Load the email configuration and return the result as a dictionnary
    """

    if not source:
        source = 'config.ini'

    if not os.path.exists(source):
        raise ValueError("The file config.ini could not be found")

    config = configparser.ConfigParser()
    config.read(source)
    return config



def sort_emails_by_date(emails_list):
    sorted_emails = sorted(emails_list, key=lambda msg: msg.date, reverse=True)
    return sorted_emails


def get_max_sender_size(emails_list):
    return len(max(emails_list, key=lambda msg: len(msg.sender)).sender)



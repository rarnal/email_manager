import yaml
from src import email_engine

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


def get_config(source=None):
    """
    Load the email configuration and return the result as a dictionnary
    """

    if not source:
        source = 'config.yaml'

    with open(source) as stream:
        config = yaml.load(stream, Loader=Loader)

        if config['server_type'] == 'imap':
            config['email_access_class'] = email_engine.IMAP_SSL
        else:
            raise ValueError("Unknown server type: {}".format(
                             config['server_type']))

        return config



def sort_emails_by_date(emails_list):
    sorted_emails = sorted(emails_list, key=lambda msg: msg.date, reverse=True)
    return sorted_emails


def get_max_sender_size(emails_list):
    return len(max(emails_list, key=lambda msg: len(msg.sender)).sender)



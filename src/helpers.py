import yaml
from src import email_engine


def get_config(source=None):
    """
    Load the email configuration and return the result as a dictionnary
    """

    if not source:
        source = 'config.yaml'

    with open(source) as stream:
        config = yaml.load(stream)

        if config['server_type'] == 'imap':
            if config['ssl']:
                config['email_access_class'] = email_engine.IMAP_SSL
            else:
                config['email_access_class'] = email_engine.IMAP
        else:
            raise ValueError("Unknown server type: {}".format(
                             config['server_type']))

        return config



def sort_emails_by_date(emails_list):
    # TODO implement a better algorythm if not efficient enough
    sorted_emails = sorted(emails_list, key= lambda msg: msg['Date'], reverse=True)
    return sorted_emails


def get_max_field_size(emails_list, field):
    return len(max(emails_list, key=lambda msg: len(msg[field]))[field])



import yaml
import email_engine


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




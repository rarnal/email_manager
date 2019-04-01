
PROGRAM_NAME = 'Program'

DELETE_MAILBOXES = ('"[gmail]/trash"',
                    'deleted',
                    'trash',
                    '"trash"',
                    '"deleted"')

### ACTIONS
TOP_SENDERS = 'top_senders'
LIST_BOXES = 'boxes'
SELECT_BOX = 'select_box'
LAST_EMAIL = 'last_emails'
RECEIVED_FROM = 'from'
SENT_TO = 'to'
READ_EMAIL = 'read'
DELETE_ID = 'delete_id'
DELETE_FROM = 'delete_from'
DELETE_CACHE = 'delete_cache'
HELP = 'help'
LOGOUT = 'quit'
SPACE = None


ACTIONS = (
    HELP,
    SPACE,
    LIST_BOXES,
    SELECT_BOX,
    SPACE,
#    LAST_EMAIL,
    READ_EMAIL,
    SPACE,
    RECEIVED_FROM,
    SENT_TO,
    SPACE,
    DELETE_ID,
    DELETE_FROM,
    SPACE,
    DELETE_CACHE,
    SPACE,
    TOP_SENDERS,
    SPACE,
    LOGOUT
)

USAGES = {
    TOP_SENDERS:
    {
        'actif': True,
        'args': {'short': "-ts",
                 'long': "--{}".format(TOP_SENDERS)},
        'kwargs': {'nargs': '?',
                   'type': int,
                   'const': 10,
                   'help': "Summarize all emails from the top [INT] senders (by default top 10)"}
    },
    LIST_BOXES:
    {
        'actif': True,
        'args': {'short': "-b",
                 'long': "--{}".format(LIST_BOXES)},
        'kwargs': {'action': "store_true",
                   'help': "Display all availables mailboxes"}
    },
    SELECT_BOX:
    {
        'actif': True,
        'args': {'short': "-sb",
                 'long': "--{}".format(SELECT_BOX)},
        'kwargs': {'nargs': 1,
                   'type': int,
                   'help': "Select mailbox [mailbox id]"}
    },
    LAST_EMAIL:
    {
        'actif': False,
        'args': {'short': "-le",
                 'long': "--last-emails"},
        'kwargs': {'nargs': '?',
                   'type': int,
                   'const': 10,
                   'help': "Get last [int] emails received (last 10 by default)"}
    },
    RECEIVED_FROM:
    {
        'actif': True,
        'args': {'short': "-f",
                 'long': "--{}".format(RECEIVED_FROM)},
        'kwargs': {'nargs': 1,
                   'type': str,
                   'help': "Find all emails received from [email address]"}
    },
    SENT_TO:
    {
        'actif': True,
        'args': {'short': "-t",
                 'long': "--{}".format(SENT_TO)},
        'kwargs': {'nargs': 1,
                   'type': str,
                   'help': "Find all emails sent to [email address]"}
    },
    READ_EMAIL:
    {
        'actif': True,
        'args': {'short': "-r",
                 'long': "--{}".format(READ_EMAIL)},
        'kwargs': {'nargs': 1,
                   'type': int,
                   'help': "Display the content of email [email id]"}
    },
    DELETE_ID:
    {
        'actif': True,
        'args': {'short': "-di",
                 'long': "--{}".format(DELETE_ID)},
        'kwargs': {'nargs': "+",
                   'type': int,
                   'help': "Delete an email [email id]"}
    },
    DELETE_FROM:
    {
        'actif': True,
        'args': {'short': "-df",
                 'long': "--{}".format(DELETE_FROM)},
        'kwargs': {'nargs': "+",
                   'type': str,
                   'help': "Delete ALL emails received from [email address]"}
    },
    DELETE_CACHE:
    {
        'actif': True,
        'args': {'short': "-dc",
                 'long': "--{}".format(DELETE_CACHE)},
        'kwargs': {'action': "store_true",
                   'help': "Delete the cache where emails are saved"}
    },
    HELP:
    {
        'actif': True,
        'args': {'short': "-h",
                 'long': "--{}".format(HELP)},
        'kwargs': {'action': "store_true",
                   'help': "Get a description of each actions"}
    },
    LOGOUT:
    {
        'actif': True,
        'args': {'short': "-q",
                 'long': "--{}".format(LOGOUT)},
        'kwargs': {'action': "store_true",
                   'help': "Log out and quit the program"}
    }
}

### CACHE
CACHE_FOLDER = 'temp/'

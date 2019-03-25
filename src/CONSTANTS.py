
PROGRAM_NAME = 'Program'
PROGRAM_USAGE = 'Incorrect.\nUse one of the below options'

### ACTIONS
TOP_SENDERS = 'top-senders'
LIST_BOXES = 'boxes'
RECEIVED_FROM = 'from'
SENT_TO = 'to'
READ_EMAIL = 'read'
DELETE_ID = 'delete-id'
DELETE_FROM = 'delete-from'
LOGOUT = 'quit'

ACTIONS = (
    TOP_SENDERS,
    LIST_BOXES,
    RECEIVED_FROM,
    SENT_TO,
    READ_EMAIL,
    DELETE_ID,
    DELETE_FROM,
    LOGOUT
)

USAGES = {
    TOP_SENDERS:
    {
        'args': {'short': "-ts",
                 'long': "--{}".format(TOP_SENDERS)},
        'kwargs': {'nargs': '?',
                   'type': int,
                   'const': 10,
                   'help': "Summarize all emails per senders"}
    },
    LIST_BOXES:
    {
        'args': {'short': "-b",
                 'long': "--{}".format(LIST_BOXES)},
        'kwargs': {'action': "store_true",
                   'help': "Display all availables inboxes"}
    },
    RECEIVED_FROM:
    {
        'args': {'short': "-f",
                 'long': "--{}".format(RECEIVED_FROM)},
        'kwargs': {'nargs': 1,
                   'type': str,
                   'help': "Find all emails received from [email address]"}
    },
    SENT_TO:
    {
        'args': {'short': "-t",
                 'long': "--{}".format(SENT_TO)},
        'kwargs': {'nargs': 1,
                   'type': str,
                   'help': "Find all emails sent to [email address]"}
    },
    READ_EMAIL:
    {
        'args': {'short': "-r",
                 'long': "--{}".format(READ_EMAIL)},
        'kwargs': {'nargs': 1,
                   'type': int,
                   'help': "Display the content of email [id]"}
    },
    DELETE_ID:
    {
        'args': {'short': "-di",
                 'long': "--{}".format(DELETE_ID)},
        'kwargs': {'nargs': "+",
                   'type': int,
                   'help': "Delete an email by [id]"}
    },
    DELETE_FROM:
    {
        'args': {'short': "-df",
                 'long': "--{}".format(DELETE_FROM)},
        'kwargs': {'nargs': 1,
                   'type': str,
                   'help': "Delete ALL emails received from [email address]"}
    },
    LOGOUT:
    {
        'args': {'short': "-q",
                 'long': "--{}".format(LOGOUT)},
        'kwargs': {'action': "store_true",
                   'help': "Log out and quit the program"}
    }
}

### CACHE
CACHE_FOLDER = 'temp/'

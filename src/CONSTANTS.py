
PROGRAM_NAME = 'Program'

### ACTIONS
TOP_SENDERS = 'top_senders'
LIST_BOXES = 'boxes'
RECEIVED_FROM = 'from'
SENT_TO = 'to'
READ_EMAIL = 'read'
DELETE_ID = 'delete_id'
DELETE_FROM = 'delete_from'
DELETE_CACHE = 'delete_cache'
HELP = 'help'
LOGOUT = 'quit'

ACTIONS = (
    TOP_SENDERS,
    LIST_BOXES,
    RECEIVED_FROM,
    SENT_TO,
    READ_EMAIL,
    DELETE_ID,
    DELETE_FROM,
    DELETE_CACHE,
    HELP,
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
                   'help': "Summarize all emails from the top [INT] senders (by default top 10)"}
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
    DELETE_CACHE:
    {
        'args': {'short': "-dc",
                 'long': "--{}".format(DELETE_CACHE)},
        'kwargs': {'action': "store_true",
                   'help': "Delete the cache where emails headers are saved"}
    },
    HELP:
    {
        'args': {'short': "-h",
                 'long': "--{}".format(HELP)},
        'kwargs': {'action': "store_true",
                   'help': "Get a description of each actions"}
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

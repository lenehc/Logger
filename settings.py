DB_PATH = ''
ENABLE_COLOR = True

GUTTER = 3
MARGIN = 2
COLUMNS = {
    'default': [4, 8, 11, 9, 5, 4],
}
WIDTH = {
    'default': 58,
}

RESPONSES_CONFIRM = {'yes', 'y'}
PROMPT_DELETE = 'Delete {}?'

LIMIT_TITLE_LENGTH = 80
LIMIT_AUTHOR_LENGTH = 30
LIMIT_PROMPT_DELETE_TITLE_LENGTH = 30

FORMAT_DATE_INPUT = '%Y-%m-%d'
FORMAT_DATE = {
    'default': '%d/%m/%y',
}

STR_LOG_SINGULAR = 'log'
STR_LOG_PLURAL = 'logs'
STR_BOOK_SINGULAR = 'book'
STR_BOOK_PLURAL = 'books'
STR_HOUR_SINGULAR = 'hour'
STR_HOUR_PLURAL = 'hours'
STR_PAGE_SINGULAR = 'page'
STR_PAGE_PLURAL = 'pages'
STR_NO_TITLE = 'Unknown Book'
STR_NO_AUTHOR = 'Unknown Author'

STR_FIELD_TITLE = 'Title'
STR_FIELD_AUTHOR = 'Author'
STR_FIELD_BOOK_ID = 'Book ID'
STR_FIELD_DATE = 'Date'
STR_FIELD_TIME = 'Time'
STR_FIELD_PAGES = 'Pages'
STR_FIELD_DEPTH = 'Depth'
STR_FIELD_USAGE = 'Usage'

ERR_INVALID_COMMAND = 'Invalid Command: add, edit, remove, show, search'
ERR_INVALID_DB_PATH = 'Invalid DB Path'
ERR_INVALID_BOOK_ID = 'Invalid Book ID'
ERR_INVALID_ITEM_ID = 'Invalid Item ID \'{}\''
ERR_LOG_EXISTS = 'Log already exists'
ERR_REQUIRED_FIELD = '{} is required'
ERR_LIMIT = '{} must be less than {}'
ERR_FORMAT = '{} must be of format {}'
ERR_INVALID_TITLE = ERR_LIMIT.format('Title', LIMIT_TITLE_LENGTH)
ERR_INVALID_AUTHOR = ERR_LIMIT.format('Author', LIMIT_AUTHOR_LENGTH)
ERR_INVALID_DATE = ERR_FORMAT.format('Date', 'YYYY-MM-DD')
ERR_INVALID_TIME_SPAN = ERR_FORMAT.format('Time', 'H:M-H:M')
ERR_INVALID_PAGE_SPAN = ERR_FORMAT.format('Pages', 'P-P')
ERR_INVALID_DEPTH = '\"Depth\" must be numerical'

MSG_NO_BOOKS = 'No Books'
MSG_NO_LOGS = 'No Logs'
MSG_NO_RESULTS = 'No Results'

ACTION_ADD = 'Added'
ACTION_EDIT = 'Edited'
ACTION_DELETE = {
    True: 'Deleted', 
    False: 'Canceled'
}

USAGE_ADD = ['add book [<title>] [<author>],', 'add log <bookID> <date> <time> [<pages>] [<depth>]']
USAGE_ADD_BOOK = 'add book [title] [author]'
USAGE_ADD_LOG = 'add log <date> <time> [pages] [depth]'
USAGE_EDIT = 'edit <bookID> [title] [author]'
USAGE_REMOVE = 'remove <itemID> ...'
USAGE_SHOW = 'show [bookID]'
USAGE_SEARCH = 'search <query>'

COLOR_NORMAL = '\x1b[0m'
COLOR_ROW_BACKGROUND = '\x1b[48;2;30;30;30m'
COLOR_FOREGROUND = '\x1b[38;2;255;255;255m'

HEADERS_TABLE_BOOK = {
    'id': {
        'name': '', 
        'span': 1, 
        'align': 'l', 
    }, 
    'title': {
        'name': 'Title', 
        'span': 2, 
        'align': 'l', 
    }, 
    'author': {
        'name': 'Author', 
        'span': 2, 
        'align': 'l', 
    }, 
    'log_count': {
        'name': '', 
        'span': 1, 
        'align': 'l', 
    }
}
HEADERS_TABLE_LOG = {
    'BLANK': {
        'span': 1
    },
    'date': {
        'name': 'Date', 
        'span': 1, 
        'align': 'l', 
    }, 
    'time': {
        'name': 'Time', 
        'span': 1, 
        'align': 'l', 
    }, 
    'pages': {
        'name': 'Pages', 
        'span': 1, 
        'align': 'l', 
    }, 
    'depth': {
        'name': 'Depth', 
        'span': 1, 
        'align': 'r', 
    }, 
}
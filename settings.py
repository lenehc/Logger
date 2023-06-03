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

SPAN_INDENT = 1
SPAN_FIELD_NAME = 1
SPAN_FIELD_VALUE = 4
SPAN_FOOTNOTE = 3

LIMIT_BOOK_TITLE_LENGTH = 80
LIMIT_AUTHOR_NAME_LENGTH = 30
LIMIT_PROMPT_DELETE_BOOK_TITLE_LENGTH = 30
LIMIT_QUERY_PRINT_LENGTH = 20

FORMAT_DATE_INPUT = '%Y-%m-%d'
FORMAT_DATE_FIELD = '%B %d, %Y'
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
STR_MINUTE_SINGULAR = 'minute'
STR_MINUTE_PLURAL = 'minutes'
STR_NO_TITLE_EXPAND = 'Unknown Book'
STR_NO_AUTHOR_EXPAND = 'Unknown Author'
STR_NO_PAGES = ''
STR_NO_TITLE = 'Unknown Book'
STR_NO_AUTHOR = ''
STR_NO_LOGS = ''
STR_NO_DEPTH = ''

ALIGN_FIELD_NAME = 'r'
ALIGN_FIELD_VALUE = 'l'
ALIGN_ERROR = 'l'
ALIGN_ACTION = 'l'
ALIGN_FOOTNOTE = 'l'

ERR_INVALID_DB_PATH = 'Could not find or create a database at the given location.'
ERR_INVALID_COMMAND = 'Enter a valid command: {}.'
ERR_INVALID_BOOK_ID = 'Could not find a book with the provided ID.'
ERR_INVALID_ITEM_ID = 'Could not find a book or log with the provided ID.'
ERR_LOG_EXISTS = 'A log already exists for \'{}\' at \'{}:{}\'.'
ERR_REQUIRED_FIELD = '\"{}\" is required.'
ERR_LIMIT = '\"{}\" must be less than {}.'
ERR_FORMAT = '\"{}\" must be of format \'{}\'.'

MSG_NO_BOOKS = 'No books'
MSG_NO_LOGS = 'No logs'
MSG_NO_RESULTS = 'No results'

ACTION_ADD = 'Added'
ACTION_EDIT = 'Edited'
ACTION_DELETE = {
    True: 'Deleted', 
    False: 'Canceled'
}

COLOR_NORMAL = '\x1b[0m'
COLOR_ROW_BACKGROUND = '\x1b[48;2;30;30;30m'
COLOR_FOREGROUND = '\x1b[38;2;245;245;245m'

HEADERS_TABLE_BOOK = {
    'id': {
        'name': '', 
        'span': 1, 
        'align': 'l', 
        'show': True
    }, 
    'title': {
        'name': 'Title', 
        'span': 2, 
        'align': 'l', 
        'show': True
    }, 
    'author': {
        'name': 'Author', 
        'span': 2, 
        'align': 'l', 
        'show': True
    }, 
    'log_count': {
        'name': 'Logs', 
        'span': 1, 
        'align': 'l', 
        'show': True
    }
}
HEADERS_TABLE_LOG = {
    'BLANK': {
        'span': 1
    },
    'book_id': {
        'name': '', 
        'span': 1, 
        'align': 'l', 
        'show': False
    }, 
    'date': {
        'name': 'Date', 
        'span': 1, 
        'align': 'l', 
        'show': True
    }, 
    'time': {
        'name': 'Time', 
        'span': 1, 
        'align': 'l', 
        'show': True
    }, 
    'pages': {
        'name': 'Pages', 
        'span': 1, 
        'align': 'l', 
        'show': True
    }, 
    'depth': {
        'name': 'Depth', 
        'span': 1, 
        'align': 'r', 
        'show': True
    }, 
}

FIELDS_ADD_EDIT_BOOK = {
    'title': {
        'name': 'Title',
        'error': ERR_LIMIT.format('Title', LIMIT_BOOK_TITLE_LENGTH),
    },
    'author': {
        'name': 'Author',
        'error':  ERR_LIMIT.format('Author', LIMIT_AUTHOR_NAME_LENGTH)
    }
}
FIELDS_ADD_LOG = {
    'date': {
        'name': 'Date',
        'error': ERR_FORMAT.format('Date', 'YYYY-MM-DD'),
    },
    'time': {
        'name': 'Time',
        'error': ERR_FORMAT.format('Time', 'H:M-H:M'),
    },
    'pages': {
        'name': 'Pages',
        'error': ERR_FORMAT.format('Pages', 'P-P'),
    },
    'depth': {
        'name': 'Depth',
        'error': '\"Depth\" must be a numerical value.',
    },
}
FIELDS_USAGE = {
    'Add': 'Run \'add\' to add a book or \'add [book ID]\' to add a log.',
    'Edit': 'Run \'edit [book ID]\'.',
    'Remove': 'Run \'remove [book ID]\' to delete a book or \'remove [date].[start time]\' to delete a log.',
    'Show': 'Run \'show\' to print your library or \'show [book ID]\' to print the details of a book.',
    'Search': 'Run \'search [query]\'.'
}

RESPONSES_CONFIRM = {'yes', 'y', 'delete'}
HEADER_USAGE = 'Usage'
ROWS_BOOK_EXPAND = [
    {
        'id': {
            'name': '',
            'span': SPAN_INDENT, 
            'align': 'l', 
            'show': True
        },
        'title': {
            'name': '',
            'span': 3, 
            'align': 'l', 
            'show': True
        }
    }, 
    {
        'BLANK': {
            'span': SPAN_INDENT
        },
        'author': {
            'name': '',
            'span': 3, 
            'align': 'l', 
            'show': True
        }
    }
]
PROMPT_DELETE = {
    'BLANK': {
        'span': SPAN_INDENT
    },
    'prompt': {
        'name': 'Are you sure you want to delete {}?', 
        'span': 6-SPAN_INDENT, 
        'align': 'l',
        'show': True
    }
}
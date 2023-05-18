ENABLE_COLOR = True

GUTTER = 3

MARGIN = 2

COLUMNS = {
    'default': [4, 8, 11, 9, 5, 8],
    68: [4, 11, 11, 9, 5, 8],
    73: [4, 15, 11, 9, 5, 8]
}

WIDTH = {
    'default': 64,
    68: 68,
    73: 73 
}

INPUT_DATE_FORMAT = '%Y-%m-%d'

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

STR_ADD_BOOK_TITLE_FIELD_NAME = 'Title' 
STR_ADD_BOOK_AUTHOR_FIELD_NAME = 'Author' 
STR_ADD_LOG_DATE_FIELD_NAME = 'Date' 
STR_ADD_LOG_TIME_FIELD_NAME = 'Time' 
STR_ADD_LOG_PAGES_FIELD_NAME = 'Pages' 
STR_ADD_LOG_DEPTH_FIELD_NAME = 'Depth' 
STR_ADD_LOG_COMMENTS_FIELD_NAME = 'Comments' 

STR_EDIT_BOOK_TITLE_FIELD_NAME = {
    'default': 'Title',
    9: 'New title'
}
STR_EDIT_BOOK_AUTHOR_FIELD_NAME = {
    'default': 'Author',
    10: 'New author'
}

FORMAT_DATE = {
    'default': '%d/%m/%y',
    11: '%d %b %Y',
    15: '%a %b %d %Y'
}

SPAN_INDENT = 1
SPAN_FIELD_NAME = 1
SPAN_FIELD_VALUE = 4
SPAN_FOOTNOTE = 3

LIMIT_COMMENTS_LENGTH = 10
LIMIT_BOOK_TITLE_LENGTH = 80
LIMIT_AUTHOR_NAME_LENGTH = 30
LIMIT_PROMPT_DELETE_BOOK_TITLE_LENGTH = 50
LIMIT_QUERY_PRINT_LENGTH = 20

ALIGN_FIELD_NAME = 'r'
ALIGN_FIELD_VALUE = 'l'
ALIGN_ERROR = 'l'
ALIGN_ACTION = 'l'
ALIGN_FOOTNOTE = 'l'

RESPONSES_CONFIRM = {'yes', 'y', 'delete'}

STR_NO_TITLE_EXPAND = 'Unknown Book'
STR_NO_AUTHOR_EXPAND = 'Unknown Author'
STR_NO_COMMENTS_EXPAND = ''
STR_NO_PAGES = ''
STR_NO_TITLE = 'Unknown Book'
STR_NO_AUTHOR = ''
STR_NO_LOGS = ''
STR_NO_DEPTH = ''
STR_NO_COMMENTS = ''
STR_HAS_COMMENTS = '*'

ERR_INVALID_SEARCH_QUERY = 'Enter a valid search.'
ERR_INVALID_COMMAND = 'Enter a valid command: \"add\", \"edit (item ID)\", \"remove (item ID)\", \"show\", \"search (query)\".'
ERR_INVALID_BOOK_ID = 'Could not find a book with the provided ID.'
ERR_INVALID_ITEM_ID = 'Could not find a book or log with the provided ID.'

ERR_LOG_EXISTS = 'A log already exists for \'{}\' at \'{}:{}\'.'
ERR_REQUIRED_FIELD = '\"{}\" is a required field.'
ERR_LIMIT = 'Invalid \"{}\", exceeds limit: {}.'
ERR_FORMAT = 'Invalid \"{}\", format: {}.'

HEADER_ERR_INVALID_SEARCH_QUERY = 'Invalid Search'
HEADER_ERR_INVALID_COMMAND = 'Invalid Command'
HEADER_ERR_INVALID_BOOK_ID = 'Invalid Book ID'
HEADER_ERR_INVALID_ITEM_ID = 'Invalid Item ID'

HEADER_USAGE = 'Usage'
HEADER_REMOVE = 'Delete Items'
HEADER_SEARCH = 'Showing results for \"{}\"'
HEADER_ADD_BOOK = 'Add Book'
HEADER_ADD_LOG = 'Add Log'
HEADER_EDIT_BOOK = 'Edit Book'
HEADER_EDIT_LOG = 'Edit Log'
HEADER_SHOW_ALL_BOOKS = 'All'
HEADER_SHOW_BOOK = 'Book Info'
HEADER_SHOW_LOG = 'Log Info'

MSG_NO_BOOKS = 'No books in library'
MSG_NO_LOGS = 'No logs for this book'
MSG_NO_RESULTS = 'No results'

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

ACTION_ADD = 'Added'
ACTION_EDIT = 'Edited'
ACTION_DELETE = {
    True: 'Deleted', 
    False: 'Canceled'
}

COLOR_NORMAL = '\x1b[0m'
COLOR_ROW_BACKGROUND = '\x1b[48;2;30;30;30m'
COLOR_FOREGROUND = '\x1b[38;2;245;245;245m'

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
    'comments': {
        'name': 'Comments', 
        'span': 1, 
        'align': 'l', 
        'show': True
    }
}

FIELDS_LOG_INFO = {
    'time_read': 'Time',
    'pages_read': 'Pages',
    'comments': 'Comments'
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

FIELDS_ADD_EDIT_LOG = {
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
        'error': 'Invalid \"Depth\", must be a numerical value.',
    },
    'comments': {
        'name': 'Comments',
        'error': ERR_LIMIT.format('Comments', LIMIT_COMMENTS_LENGTH)
    }
}

FIELDS_USAGE = {
    'add': ['Add items', 'Insert a book or log into your database. Run \'logger add [Book-ID]\' to add a log, or \'logger add\' to add a book.'],
    'edit': ['Edit items', 'Change the details of a book or log. Run \'logger edit [Book-ID]\' to edit a book or \'logger edit [Log-Date].[Log-Start-Time]\' to edit a log.'],
    'remove': ['Delete items', 'Remove a book or log from your database. Run \'logger remove [Book-ID]\' to delete a book or \'logger remove [Log-Date].[Log-Start-Time]\' to remove a log.'],
    'show': ['Show items', 'Print the details of a book or log.  Run \'logger show\' to show all books in the database, \'logger show [Book-ID]\' to show the details of a book or \'logger show [Log-Date].[Log-Start-Time]\' to show the details of a log.'],
    'search': ['Search books', 'Search for a book by title or author. Run \'logger search [Query]\'']
}
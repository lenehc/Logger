import os
import logging
import sys
import textwrap
import random

import settings

from itertools import zip_longest
from datetime import datetime, timedelta
from contextlib import contextmanager
from sqlalchemy import create_engine, select, insert, update, and_, or_, Column, ForeignKey, CheckConstraint, Integer, String, Date, Time
from sqlalchemy.orm import relationship, backref, declarative_base, Session


logging.basicConfig(format='%(message)s', level=logging.INFO)


Base = declarative_base()


class Book(Base):
    __tablename__ = "book"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    author = Column(String)

    logs = relationship("Log", backref=backref("book"))


class Log(Base):
    __tablename__ = "log"
    __table_args__ = (
            CheckConstraint("time_start < time_end"),
            CheckConstraint("page_start <= page_end"),
            )

    book_id = Column(Integer, ForeignKey("book.id"), nullable=False)

    date = Column(Date, primary_key=True)
    time_start = Column(Time, primary_key=True)
    time_end = Column(Time, nullable=False)
    page_start = Column(Integer)
    page_end = Column(Integer)
    depth = Column(Integer)


class Printer:
    def __init__(self):
        self.width = self._find_apt_value(settings.WIDTH, os.get_terminal_size().columns)
        self.columns = self._find_apt_value(settings.COLUMNS.copy(), self.width)
        self.indent = ('', 1, 'l')
        self.gutter = ' ' * 3
        self.margin = ' ' * 2

    def _parse_layout_options(self, options, locals=None):
        layout = []

        if not options:
            return [('', 0, 'l')]

        for param, option in options.items():
            if param == 'BLANK':
                layout.append(('', option['span'], 'l'))
            else:
                name = locals[param] if locals else option['name']
                layout.append((name, option['span'], option['align']))

        return layout
  
    def _find_apt_value(self, items, value):
        apt_value = items.get('default')

        for item in items:
            if item != 'default' and value >= item:
                apt_value = items[item]

        return apt_value

    def _truncate(self, string, width, align=None):
        if len(string) > width:
            string = f'{string[:width-3].strip()}...'
            if align and align == 'l':
                return string.ljust(width)
            if align and align == 'r':
                return string.rjust(width)

        return string

    def _format_item(self, string, width, align, wrap):
        items = []

        if not string:
            return [(''.ljust(width), width, align)]

        if isinstance(string, dict):
            string = self._find_apt_value(string, width)

        string = str(string)
        strings = textwrap.wrap(string, width=width) if wrap else [self._truncate(string, width, align)]

        for string in strings:
            if align == 'l':
                string = string.ljust(width)
            if align == 'r':
                string = string.rjust(width)
            items.append((string, width, align))

        return items

    def _format_line(self, items, wrap=False, full_just=False, background_color='', foreground_color=''):
        current_index = 0
        formatted_items = []

        for string, span, align in items:
            if span <= 0:
                continue

            width = (span - 1) * 3 + sum(self.columns[current_index:current_index+span])
            current_index += span

            if isinstance(string, list):
                ins_str = []
                for item in string:
                    ins_str.extend(self._format_item(item, width, align, wrap))
                formatted_items.append(ins_str)
            else:
                formatted_items.append(self._format_item(string, width, align, wrap)) 
            
        lines = [list(field) for field in list(zip_longest(*formatted_items, fillvalue=None))]

        line_strings = []

        for line in lines:
            line_fields = []
            for j, sub_f in enumerate(line):
                if not sub_f:
                    width = lines[0][j][1]
                    line_fields.append(''.ljust(width))
                else:
                    line_fields.append(sub_f[0])
            line_strings.append(line_fields)

        for i, line_string in enumerate(line_strings):
            line_string = self.margin + self.gutter.join(line_string)

            if full_just:
                line_string = line_string.ljust(self.width)

            if settings.ENABLE_COLOR:
                if not foreground_color:
                    foreground_color = '\x1b[38;2;{};{};{}m'.format(*settings.COLOR_FOREGROUND)
                line_string = f'{foreground_color}{background_color}{line_string}\x1b[0m'

            line_strings[i] = line_string
        
        return line_strings
    
    def _format_count(self, count, name):
        string = name if count == 1 else name + 's'
        return f'{count} {string}'

    def _format_count_log(self, log_count):
        return self._format_count(log_count, 'log')

    def _format_count_book(self, book_count):
        return self._format_count(book_count, 'book')

    def _format_count_page(self, page_count):
        return self._format_count(page_count, 'page')

    def _format_count_hour(self, hour_count):
        return self._format_count(hour_count, 'hour')

    def print_line(self, items, print_method=logging.info, new_line_before=False, new_line_after=False, **kwargs):
        line_strings = self._format_line(items, **kwargs)

        if new_line_before:
            print_method('')

        for line_string in line_strings:
            print_method(line_string)

        if new_line_after:
            print_method('')

    def print_empty_line(self):
        self.print_line([('', 1, 'l')])

    def print_item_count(self, book_count=None, log_count=None, page_count=None, hour_count=None, **kwargs):
        fields = []
        log_count_string = self._format_count_log(log_count)
        book_count_string = self._format_count_book(book_count)
        page_count_string = self._format_count_page(page_count)
        hour_count_string = self._format_count_hour(hour_count)

        if book_count is not None:
            fields.append(book_count_string)

        if log_count is not None:
            fields.append(log_count_string)

        if page_count is not None:
            fields.append(page_count_string)

        if hour_count is not None:
            fields.append(hour_count_string)

        string = ', '.join(fields)
        items = [self.indent, (string, 5, 'l')]
        self.print_line(items, **kwargs)

    def print_field(self, name, value):
        items = [self.indent, (name, 1, 'r'), (value, 4, 'l')] 
        self.print_line(items, wrap=True)

    def print_action(self, action, **kwargs):
        items = [self.indent, (action, 5, 'l')]
        self.print_line(items, **kwargs)

    def print_error(self, error, exit=False, **kwargs):
        items = [self.indent, (error, 5, 'l')]
        self.print_line(items, wrap=True, print_method=logging.error, **kwargs)

        if exit:
            sys.exit(1)

    def print_usage(self, usage):
        self.print_field('Usage', usage)
        sys.exit(1)

    def print_table_headers(self, headers, **kwargs):
        items = self._parse_layout_options(headers)
        self.print_line(items, **kwargs)

    def print_table_book(self, books, show_count=True, new_line_before=False, new_line_after=False):
        headers = {
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
        highlight = True
        total_log_count = 0

        if new_line_before:
            self.print_empty_line()

        for book in books:
            id = book.id
            author = book.author
            log_count = len(book.logs) if book.logs else ''
            title = book.title if book.title else ''
            total_log_count += len(book.logs)
            items = self._parse_layout_options(headers, locals=locals())

            if settings.ENABLE_COLOR and highlight:
                self.print_line(items, background_color='\x1b[48;2;{};{};{}m'.format(*settings.COLOR_ROW_BACKGROUND), full_just=True)
                highlight = False
            else:
                self.print_line(items)
                highlight = True

        self.print_table_headers(headers)

        if show_count:
            self.print_item_count(len(books), total_log_count, new_line_before=True)

        if new_line_after:
            self.print_empty_line()

    def print_table_log(self, logs, show_count=True, new_line_before=False, new_line_after=False):
        headers = {
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
        highlight=True

        logs.sort(key=lambda r: r.date)

        if new_line_before:
            self.print_empty_line()
        
        for log in logs:
            date = settings.FORMAT_DATE.copy()
            time = f'{log.time_start.strftime("%H:%M")} {log.time_end.strftime("%H:%M")}'
            depth = log.depth
            pages = ''

            if log.page_start and log.page_end:
                pages = f'{str(log.page_start).ljust(4)} {str(log.page_end).ljust(4)}'

            for item in date:
                date[item] = log.date.strftime(date[item])

            items = self._parse_layout_options(headers, locals=locals())

            if settings.ENABLE_COLOR and highlight:
                self.print_line(items, background_color='\x1b[48;2;{};{};{}m'.format(*settings.COLOR_ROW_BACKGROUND), full_just=True)
                highlight = False
            else:
                self.print_line(items)
                highlight = True

        self.print_table_headers(headers)

        if show_count:
            self.print_item_count(log_count=len(logs), new_line_before=True)

        if new_line_after:
            self.print_empty_line()
    
    def print_books(self, books, empty_message):
        if not books:
            self.print_error(empty_message)
        else:
            self.print_table_book(books)
        
    def print_book_expand(self, book, new_line_before=False, new_line_after=False):
        id = book.id
        title = 'Unknown Book' if not book.title else book.title
        author = 'Unknown Author' if not book.author else book.author

        row1_items = [(id, 1, 'l'), (title, 5, 'l')]
        row2_items = [self.indent, (author, 5, 'l')]

        if new_line_before:
            self.print_empty_line()

        self.print_line(row1_items, wrap=True)
        self.print_line(row2_items, wrap=True)

        if new_line_after:
            self.print_empty_line()

    def get_book_stats(self, book):
        total_page_count, total_hour_count = 0, 0

        for log in book.logs:
            if log.page_end and log.page_start:
                if log.page_end == log.page_start:
                    total_page_count += 1
                else:
                    total_page_count += log.page_end - log.page_start
            total_hour_count += delta_from_time(log.time_start, log.time_end) / 3600

        return total_page_count, round(total_hour_count, 1)

    def print_book_info(self, book):
        empty_message = 'No Logs'
        
        if not book.logs:
            self.print_error(empty_message)
            self.print_book_expand(book, new_line_before=True)
        else:
            page_count, hour_count = self.get_book_stats(book)
            self.print_table_log(book.logs, show_count=False, new_line_after=True)
            self.print_book_expand(book, new_line_after=True)
            self.print_item_count(log_count=len(book.logs), page_count=page_count, hour_count=hour_count)

    def confirm_delete(self, books, logs):
        input_field = ''.join(self._format_line([self.indent, self.indent]) + [self.gutter])
        log_count = self._format_count_log(len(logs))
        book_count = self._format_count_book(len(books))

        if books:
            if len(books) == 1:
                book = next(iter(books))
                if book.title:
                    book_title = self._truncate(book.title, 35)
                    text = f'\"{book_title}\"'
                else:
                    text = book_count
            else:
                text = book_count
            if logs:
                text += f' and {log_count}'
        else:
            text = log_count

        prompt = f'Delete {text}?'
        items = [self.indent, (prompt, 5, 'l')]

        self.print_line(items, wrap=True)

        confirm = input(input_field)

        return confirm in {'yes', 'y', 'delete'}


db_path = os.path.abspath(os.path.expanduser(settings.DB_PATH)) if settings.DB_PATH else '.logger.db'
engine = create_engine(f"sqlite:///{db_path}?foreign_keys=1")


try:
    Base.metadata.create_all(engine)
except:
    Printer().print_error('Invalid DB Path', exit=True)


session = Session(engine)


@contextmanager
def session_scope():
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class DB:
    def __init__(self):
        pass

    def _generate_book_id(self):
        while True:
            book_id = random.randint(1000,9999)
            if not self._is_valid_book_id(book_id):
                return book_id

    def _is_valid_book_id(self, book_id):
        return bool(self.book_obj(book_id))

    def _is_valid_log_id(self, date, time_start):
        return bool(self.log_obj(date, time_start))

    def _log_id(self, date, time_start):
        return and_(Log.date == date, Log.time_start == time_start)

    def search(self, query):
        query = select(Book).where(or_(Book.id.contains(query), Book.title.contains(query), Book.author.contains(query)))
        return session.scalars(query).all()

    def book_obj(self, book_id):
        query = select(Book).where(Book.id == book_id)
        return session.scalar(query)

    def log_obj(self, date, time_start):
        query = select(Log).where(self._log_id(date, time_start))
        return session.scalar(query)
    
    def get_all_books(self):
        query = select(Book).order_by(Book.title)
        return session.scalars(query).all()

    def update_book(self, book_id, **info):
        with session_scope() as session:
            query = update(Book).where(Book.id == book_id).values(**info)
            session.execute(query)

    def insert_log(self, **info):
        with session_scope() as session:
            query = insert(Log).values(**info)
            session.execute(query)

    def insert_book(self, **info):
        with session_scope() as session:
            query = insert(Book).values(id=self._generate_book_id(), **info)
            session.execute(query)

    def delete_items(self, items):
        with session_scope() as session:
            for item in items:
                session.delete(item)


def delta_from_time(start_time, end_time):
    start_time_delta = timedelta(hours=start_time.hour, minutes=start_time.minute)
    end_time_delta = timedelta(hours=end_time.hour, minutes=end_time.minute)
    return (end_time_delta - start_time_delta).seconds


def get_book(book_id):
    db = DB()
    try:
        book_id = int(book_id)
        if db._is_valid_book_id(book_id):
            return db.book_obj(book_id)
    except ValueError:
        pass
    return


def get_item(item_id):
    db = DB()
    book = get_book(item_id)

    if book:
        return book

    try:
        id = datetime.strptime(item_id, '%Y-%m-%d.%H:%M')
        date = id.date()
        time_start = id.time()
        if db._is_valid_log_id(date, time_start):
            return db.log_obj(date, time_start)
    except ValueError:
        pass

    return


def is_valid_title(title):
    if len(title) > 100:
        return False

    return title 


def is_valid_author(name):
    if len(name) > 50:
        return False

    return name


def is_valid_date(date):
    try:
        date = datetime.strptime(date, '%Y-%m-%d')
        return date.date()
    except ValueError:
        return False


def is_valid_time_span(time_span):
    try:
        start, end = [datetime.strptime(t, '%H:%M').time() for t in time_span.split('-')]
        if start > end:
            return False
        return start, end
    except ValueError:
        return False


def is_valid_page_span(page_span):
    try:
        start, end = map(int, page_span.split('-'))
        if start > end:
            return False
        return start, end
    except ValueError:
        return False


def is_valid_depth(depth):
    try:
        depth = int(depth)
        return depth
    except ValueError:
        return False


def parse_args(fields, args, usage):
    printer = Printer()
    args = (*args, *('',) * (len(fields) - len(args)))
    arg_fields = dict()

    for value, params in zip(args, fields):
        name, metavar, required, check, error = params.values()

        if not value:
            if required:
                printer.print_error(f'{metavar} is required', exit=True)

        elif check:
            res = check(value)
            if res == False:
                if error:
                    printer.print_error(error, exit=True)
                printer.print_usage(usage)
            elif res != True:
                arg_fields[name] = res
                continue

        arg_fields[name] = value

    return arg_fields




ERR_INVALID_COMMAND = 'Invalid Command: add, edit, remove, show, search'


class Add:
    def __init__(self):
        self.db = DB()
        self.printer = Printer()

        self.fields_book = [
            {
                'name': 'title',
                'metavar': 'Title',
                'required': False,
                'check': is_valid_title,
                'error': 'Title must be less than 100'
            },
            {
                'name': 'author',
                'metavar': 'Author',
                'required': False,
                'check': is_valid_author,
                'error': 'Author must be less than 50'
            }
        ]
        self.fields_log = [
            {
                'name': 'book_id',
                'metavar': 'Book ID',
                'required': True,
                'check': self.db._is_valid_book_id,
                'error': 'Invalid Book ID'
            },
            {
                'name': 'date',
                'metavar': 'Date',
                'required': True,
                'check': is_valid_date,
                'error': 'Date must be of format YYYY-MM-DD'
            },
            {
                'name': 'time',
                'metavar': 'Time',
                'required': True,
                'check': is_valid_time_span,
                'error': 'Time must be of format H:M-H:M'
            },
            {
                'name': 'pages',
                'metavar': 'Pages',
                'required': False,
                'check': is_valid_page_span,
                'error': 'Pages must be of format P-P'
            },
            {
                'name': 'depth',
                'metavar': 'Depth',
                'required': False,
                'check': is_valid_depth,
                'error': 'Depth must be numerical'
            },
        ]

        self.usage = ['add book [<title>] [<author>],', 'add log <bookID> <date> <time> [<pages>] [<depth>]']
        self.usage_log = 'add log <date> <time> [pages] [depth]'
        self.usage_book = 'add book [title] [author]'

        self.action = 'Added'

    def run(self, args):
        if len(args) < 1:
            self.printer.print_usage(self.usage)
        
        command = args[0]
        args = args[1:]

        if command == 'book':
            if not args or len(args) > 2:
                self.printer.print_usage(self.usage_book)

            args = parse_args(self.fields_book, args, self.usage_book)

            self.db.insert_book(**args)
            self.printer.print_action('Added')

        elif command == 'log':
            if not args or len(args) > 4:
                self.printer.print_usage(self.usage_log)

            args = parse_args(self.fields_log, args, self.usage_log)

            args = {
                'book_id': args['book_id'], 
                'date': args['date'], 
                'time_start': args['time'][0], 
                'time_end': args['time'][1], 
                'page_start': args['pages'][0] if args['pages'] else None, 
                'page_end': args['pages'][1] if args['pages'] else None,
                'depth': args['depth'], 
            }

            if self.db._is_valid_log_id(args['date'], args['time_start']):
                self.printer.print_error('Log already exists', exit=True)

            self.db.insert_log(**args)
            self.printer.print_action(self.usage)

        else:
            self.printer.print_usage(self.usage)


class Edit:
    def __init__(self):
        self.db = DB()
        self.printer = Printer()

        self.fields = [
            {
                'name': 'book_id',
                'metavar': 'Book ID',
                'required': True,
                'check': self.db._is_valid_book_id,
                'error': 'Invalid Book ID'
            },
            {
                'name': 'title',
                'metavar': 'Title',
                'required': False,
                'check': is_valid_title,
                'error': 'Title must be less than 100'
            },
            {
                'name': 'author',
                'metavar': 'Author',
                'required': False,
                'check': is_valid_author,
                'error': 'Author must be less than 50'
            }
        ]
            
        self.usage = 'edit <bookID> [title] [author]'

        self.action = 'Edited'

    def run(self, args):
        if not args or len(args) > 3:
            self.printer.print_usage(self.usage)

        args = parse_args(self.fields, args, self.usage)

        self.db.update_book(**args)
        self.printer.print_action(self.action)


class Remove:
    def __init__(self):
        self.db = DB()
        self.printer = Printer()

        self.usage = 'remove <itemID> ...'

        self.action = {True: 'Deleted', False: 'Canceled'}

    def run(self, args):
        if len(args) < 1:
            self.printer.print_usage(self.usage)
        
        books, logs = set(), set()

        for arg in args:
            item = get_item(arg)

            if not item:
                self.printer.print_error(f'Invalid Item ID \'{self.printer._truncate(arg, 20)}\'', exit=True)
            
            if isinstance(item, Log):
                logs.add(item)

            elif isinstance(item, Book):
                books.add(item)
                for log in item.logs:
                    logs.add(log)

        confirm = self.printer.confirm_delete(books, logs)

        if confirm:
            self.db.delete_items(logs | books)
        
        self.printer.print_action(self.action[confirm], new_line_before=True)


class Show:
    def __init__(self):
        self.db = DB()
        self.printer = Printer()

        self.usage = 'show [bookID]'

    def run(self, args):
        if len(args) > 1:
            self.printer.print_usage(self.usage)

        if args:
            book = self.db.book_obj(args[0])

            if not book:
                self.printer.print_error('Invalid Book ID', exit=True)
        
            if len(args) == 1:
                self.printer.print_book_info(book)

        else:
            books = self.db.get_all_books()
            self.printer.print_books(books, 'No Books')


class Search:
    def __init__(self):
        self.db = DB()
        self.printer = Printer()

        self.usage = 'search <query>'


    def run(self, args):
        if len(args) == 1:
            results = self.db.search(args[0])

            self.printer.print_books(results, 'No Results')

        else:
            self.printer.print_usage(self.usage)


def main():
    printer = Printer()
    commands = {
        'add': Add,
        'edit': Edit,
        'remove': Remove,
        'show': Show,
        'search': Search
    }

    if len(sys.argv[1:]) == 0:
        printer.print_error(ERR_INVALID_COMMAND, exit=True)

    args = sys.argv[2:]

    try:
        command = commands[sys.argv[1]]
    except KeyError:
        printer.print_error(ERR_INVALID_COMMAND, exit=True)

    command().run(args)
    
    engine.dispose()
        

if __name__ == "__main__":
    main()
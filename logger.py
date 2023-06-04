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

        self._indent = ('', 1, 'l')
        self._gutter = ' ' * settings.GUTTER
        self._margin = ' ' * settings.MARGIN

        self.str_log_singular = settings.STR_LOG_SINGULAR
        self.str_log_plural = settings.STR_LOG_PLURAL
        self.str_book_singular = settings.STR_BOOK_SINGULAR
        self.str_book_plural = settings.STR_BOOK_PLURAL
        self.str_hour_singular = settings.STR_HOUR_SINGULAR
        self.str_hour_plural = settings.STR_HOUR_PLURAL
        self.str_page_singular = settings.STR_PAGE_SINGULAR
        self.str_page_plural = settings.STR_PAGE_PLURAL
        self.str_no_author = settings.STR_NO_AUTHOR
        self.str_no_title = settings.STR_NO_TITLE

        self.fields_usage = settings.FIELDS_USAGE

        self.header_usage = settings.HEADER_USAGE

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
            string = f'{string[:width-2].strip()}..'
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
                items.append((string.ljust(width), width, align))
            if align == 'r':
                items.append((string.rjust(width), width, align))

        return items

    def _format_line(self, items, wrap=False, full_just=False, background_color='', foreground_color=''):
        current_index = 0

        formatted_items = []

        for string, span, align in items:
            if span <= 0:
                continue

            width = (span - 1) * settings.GUTTER + sum(self.columns[current_index:current_index+span])
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
            line_string = self._margin + self._gutter.join(line_string)

            if full_just:
                line_string = line_string.ljust(self.width)

            if settings.ENABLE_COLOR:
                if not foreground_color:
                    foreground_color = settings.COLOR_FOREGROUND
                line_string = f'{foreground_color}{background_color}{line_string}{settings.COLOR_NORMAL}'

            line_strings[i] = line_string
        
        return line_strings
    
    def _format_count(self, count, plural_name, singular_name):
        name = singular_name if count == 1 else plural_name
        return f'{count} {name}'

    def _format_count_log(self, log_count):
        return self._format_count(log_count, self.str_log_plural, self.str_log_singular)

    def _format_count_book(self, book_count):
        return self._format_count(book_count, self.str_book_plural, self.str_book_singular)

    def _format_count_page(self, page_count):
        return self._format_count(page_count, self.str_page_plural, self.str_page_singular)

    def _format_count_hour(self, hour_count):
        return self._format_count(hour_count, self.str_hour_plural, self.str_hour_singular)

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
        items = [self._indent, (string, 5, 'l')]
        self.print_line(items, **kwargs)

    def print_header(self, header):
        items = [self._indent, (header, 5, 'l')]
        self.print_line(items, new_line_after=True)

    def print_field(self, name, value):
        items = [self._indent, (name, 1, 'r'), (value, 4, 'l')] 
        self.print_line(items, wrap=True)

    def print_action(self, action, **kwargs):
        items = [self._indent, (action, 5, 'l')]
        self.print_line(items, **kwargs)

    def print_error(self, error, exit=False, **kwargs):
        items = [self._indent, (error, 5, 'l')]
        self.print_line(items, wrap=True, print_method=logging.error, **kwargs)

        if exit:
            sys.exit(1)

    def print_table_headers(self, headers, **kwargs):
        items = self._parse_layout_options(headers)
        self.print_line(items, **kwargs)

    def print_table_book(self, books, show_count=True, new_line_before=False, new_line_after=False):
        headers = settings.HEADERS_TABLE_BOOK
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
                self.print_line(items, background_color=settings.COLOR_ROW_BACKGROUND, full_just=True)
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
        headers = settings.HEADERS_TABLE_LOG 
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
                self.print_line(items, background_color=settings.COLOR_ROW_BACKGROUND, full_just=True)
                highlight = False
            else:
                self.print_line(items)
                highlight = True

        self.print_table_headers(headers)

        if show_count:
            self.print_item_count(log_count=len(logs), new_line_before=True)

        if new_line_after:
            self.print_empty_line()
    
    def print_books(self, books, empty_message, header=None):
        if header:
            self.print_header(header)

        if not books:
            self.print_error(empty_message)
        else:
            self.print_table_book(books)
        
    def print_book_expand(self, book, new_line_before=False, new_line_after=False):
        id = book.id
        title = self.str_no_title if not book.title else book.title
        author = self.str_no_author if not book.author else book.author

        row1_items = [(id, 1, 'l'), (title, 5, 'l')]
        row2_items = [self._indent, (author, 5, 'l')]

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
        empty_message = settings.MSG_NO_LOGS
        
        if not book.logs:
            self.print_error(empty_message)
            self.print_book_expand(book, new_line_before=True)
        else:
            page_count, hour_count = self.get_book_stats(book)
            self.print_table_log(book.logs, show_count=False, new_line_after=True)
            self.print_book_expand(book, new_line_after=True)
            self.print_item_count(log_count=len(book.logs), page_count=page_count, hour_count=hour_count)

    def print_err_invalid_item_id(self, id):
        error = settings.ERR_INVALID_ITEM_ID.format(id)
        self.print_error(error, exit=True)

    def print_err_invalid_book_id(self):
        error = settings.ERR_INVALID_BOOK_ID
        self.print_error(error, exit=True)

    def print_err_log_exists(self):
        error = settings.ERR_LOG_EXISTS
        self.print_error(error, exit=True)

    def print_err_required_field(self, name):
        error = settings.ERR_REQUIRED_FIELD.format(name)
        self.print_error(error, exit=True)

    def print_err_invalid_db_path(self):
        error = settings.ERR_INVALID_DB_PATH
        self.print_error(error, exit=True)

    def print_action_delete(self, response):
        action = settings.ACTION_DELETE[response]
        self.print_action(action)

    def print_action_add(self):
        action = settings.ACTION_ADD
        self.print_action(action)

    def print_action_edit(self):
        action = settings.ACTION_EDIT
        self.print_action(action)

    def print_usage(self):
        self.print_header(settings.HEADER_USAGE)
        for name, value in self.fields_usage.items():
            self.print_field(name,value)

    def print_usage_field(self, usage):
        self.print_field(settings.STR_FIELD_USAGE, usage)

    def print_all_books(self, books):
        empty_message = settings.MSG_NO_BOOKS
        self.print_books(books, empty_message)
    
    def print_search_results(self, results):
        empty_message = settings.MSG_NO_RESULTS
        self.print_books(results, empty_message)
    
    def input(self, name, accepted_responses={}, required=False, check_response=None, error='', bool=False, exit_on_error=False, error_on_empty=True):
        fields = [self._indent, (name, 1, 'r')]
        line = self._format_line(fields)
        response = input(f'{line[0]}{self._gutter}').strip()

        if not response and required:
            if error_on_empty:
                error = settings.ERR_REQUIRED_FIELD.format(name)

        elif not response and not required:
            return

        elif accepted_responses and response.lower() in accepted_responses:
            if bool:
                return True
            return response

        elif check_response:
            response = check_response(response)
            if response is not False:
                if bool:
                    return True
                return response

        if error:
            self.print_error(error, new_line_before=True)

        if exit_on_error:
            sys.exit(1)

        if bool:
            return False

        return response

    def confirm_delete(self, books, logs):
        book_title = ''

        if books:
            book = next(iter(books))
            if book.title:
                book_title = self._truncate(book.title, settings.LIMIT_PROMPT_DELETE_TITLE_LENGTH)

        log_count = self._format_count_log(len(logs))
        book_count = self._format_count_book(len(books))
        text = ''

        if len(books) == 1:
            if book_title:
                if logs:
                    text += f'\"{book_title}\" and {log_count}'
                else:
                    text += f'\"{book_title}\"'
        else:
            if books and logs:
                text += f'{book_count} and {log_count}'
            elif not books:
                text = log_count
            elif not logs:
                text = book_count

        prompt = settings.PROMPT_DELETE.format(text)
        items = [self._indent, (prompt, 5, 'l')]

        self.print_line(items, wrap=True)

        input = self.input('', accepted_responses=settings.RESPONSES_CONFIRM, bool=True, required=True, error_on_empty=False)

        return input


db_path = os.path.abspath(os.path.expanduser(settings.DB_PATH)) if settings.DB_PATH else '.logger.db'
engine = create_engine(f"sqlite:///{db_path}?foreign_keys=1")


try:
    Base.metadata.create_all(engine)
except:
    Printer().print_err_invalid_db_path()


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
    if len(title) > settings.LIMIT_TITLE_LENGTH:
        return False

    return title 


def is_valid_author(name):
    if len(name) > settings.LIMIT_AUTHOR_LENGTH:
        return False

    return name


def is_valid_date(date):
    try:
        date = datetime.strptime(date, settings.FORMAT_DATE_INPUT)
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
                printer.print_err_required_field(metavar)

        elif check:
            res = check(value)
            if res == False:
                if error:
                    printer.print_error(error, exit=True)
                printer.print_usage_field(usage)
                sys.exit(1)
            elif res != True:
                arg_fields[name] = res
                continue

        arg_fields[name] = value

    return arg_fields


class Add:
    def __init__(self):
        self.db = DB()
        self.printer = Printer()

        self.fields_book = [
            {
                'name': 'title',
                'metavar': settings.STR_FIELD_TITLE,
                'required': False,
                'check': is_valid_title,
                'error': settings.ERR_INVALID_TITLE
            },
            {
                'name': 'author',
                'metavar': settings.STR_FIELD_AUTHOR,
                'required': False,
                'check': is_valid_author,
                'error': settings.ERR_INVALID_AUTHOR
            }
        ]
        self.fields_log = [
            {
                'name': 'book_id',
                'metavar': settings.STR_FIELD_BOOK_ID,
                'required': True,
                'check': self.db._is_valid_book_id,
                'error': settings.ERR_INVALID_BOOK_ID
            },
            {
                'name': 'date',
                'metavar': settings.STR_FIELD_DATE,
                'required': True,
                'check': is_valid_date,
                'error': settings.ERR_INVALID_DATE
            },
            {
                'name': 'time',
                'metavar': settings.STR_FIELD_TIME,
                'required': True,
                'check': is_valid_time_span,
                'error': settings.ERR_INVALID_TIME_SPAN
            },
            {
                'name': 'pages',
                'metavar': settings.STR_FIELD_PAGES,
                'required': False,
                'check': is_valid_page_span,
                'error': settings.ERR_INVALID_PAGE_SPAN
            },
            {
                'name': 'depth',
                'metavar': settings.STR_FIELD_DEPTH,
                'required': False,
                'check': is_valid_depth,
                'error': settings.ERR_INVALID_DEPTH
            },
        ]

    def run(self, args):
        if len(args) < 1:
            self.printer.print_usage_field(settings.USAGE_ADD)
            sys.exit(1)
        
        command = args[0]
        args = args[1:]

        if command == 'book':
            if not args or len(args) > 2:
                self.printer.print_usage_field(settings.USAGE_ADD_BOOK)
                sys.exit(1)

            args = parse_args(self.fields_book, args, settings.USAGE_ADD_BOOK)

            self.db.insert_book(**args)
            self.printer.print_action_add()

            return True

        elif command == 'log':
            if not args or len(args) > 4:
                self.printer.print_usage_field(settings.USAGE_ADD_LOG)
                sys.exit(1)

            args = parse_args(self.fields_log, args, settings.USAGE_ADD_LOG)

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
                self.printer.print_err_log_exists()

            self.db.insert_log(**args)
            self.printer.print_action_add()

            return True
        
        return False


class Edit:
    def __init__(self):
        self.db = DB()
        self.printer = Printer()

        self.fields = [
            {
                'name': 'book_id',
                'metavar': settings.STR_FIELD_BOOK_ID,
                'required': True,
                'check': self.db._is_valid_book_id,
                'error': settings.ERR_INVALID_BOOK_ID
            },
            {
                'name': 'title',
                'metavar': settings.STR_FIELD_TITLE,
                'required': False,
                'check': is_valid_title,
                'error': settings.ERR_INVALID_TITLE
            },
            {
                'name': 'author',
                'metavar': settings.STR_FIELD_AUTHOR,
                'required': False,
                'check': is_valid_author,
                'error': settings.ERR_INVALID_AUTHOR
            }
        ]

    def run(self, args):
        if not args or len(args) > 3:
            self.printer.print_usage_field(settings.USAGE_EDIT)
            sys.exit(1)

        args = parse_args(self.fields, args, settings.USAGE_EDIT)

        self.db.update_book(**args)
        self.printer.print_action_edit()

        return True


class Remove:
    def __init__(self):
        self.db = DB()
        self.printer = Printer()

    def run(self, args):
        if len(args) < 1:
            self.printer.print_usage_field(settings.USAGE_REMOVE)
            sys.exit(1)
        
        books, logs = set(), set()

        for arg in args:
            item = get_item(arg)

            if not item:
                self.printer.print_err_invalid_item_id(self.printer._truncate(arg, 20))
            
            if isinstance(item, Log):
                logs.add(item)

            elif isinstance(item, Book):
                books.add(item)
                for log in item.logs:
                    logs.add(log)

        confirm = self.printer.confirm_delete(books, logs)

        if confirm:
            self.db.delete_items(logs | books)

        return True


class Show:
    def __init__(self):
        self.db = DB()
        self.printer = Printer()

    def run(self, args):
        if len(args) > 1:
            self.printer.print_usage_field(settings.USAGE_SHOW)
            sys.exit(1)

        if not args:
            books = self.db.get_all_books()
            self.printer.print_all_books(books)

            return True

        book = self.db.book_obj(args[0])

        if not book:
            self.printer.print_err_invalid_book_id()
        
        if len(args) == 1:
            self.printer.print_book_info(book)

            return True

        return False


class Search:
    def __init__(self):
        self.db = DB()
        self.printer = Printer()


    def run(self, args):
        if len(args) == 1:
            results = self.db.search(args[0])

            self.printer.print_search_results(results)

            return True
            
        return False


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
        printer.print_usage()
        sys.exit(1)

    args = sys.argv[2:]

    try:
        command = commands[sys.argv[1]]
    except KeyError:
        printer.print_usage()
        sys.exit(1)

    if not command().run(args):
        printer.print_usage()
        sys.exit(1)
    
    engine.dispose()
        

if __name__ == "__main__":
    main()
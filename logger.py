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
            CheckConstraint("page_start < page_end"),
            )

    book_id = Column(Integer, ForeignKey("book.id"), nullable=False)

    date = Column(Date, primary_key=True)
    time_start = Column(Time, primary_key=True)
    time_end = Column(Time, nullable=False)
    page_start = Column(Integer)
    page_end = Column(Integer)
    depth = Column(Integer)
    comments = Column(String)


class Printer:
    def __init__(self):
        self.width = self._find_apt_value(settings.WIDTH, os.get_terminal_size().columns)
        self.columns = self._find_apt_value(settings.COLUMNS.copy(), self.width)

        self.margin = settings.MARGIN
        self.gutter = settings.GUTTER

        self.span_indent = settings.SPAN_INDENT
        self.span_footnote = settings.SPAN_FOOTNOTE

        self.span_field_name = settings.SPAN_FIELD_NAME
        self.span_field_value = settings.SPAN_FIELD_VALUE

        self.align_field_name = settings.ALIGN_FIELD_NAME
        self.align_field_value = settings.ALIGN_FIELD_VALUE
        self.align_footnote = settings.ALIGN_FOOTNOTE

        self._margin = ' ' * self.margin
        self._gutter = ' ' * self.gutter
        self._indent = ('', self.span_indent, 'l')

        self.format_date = settings.FORMAT_DATE

        self.enable_color = settings.ENABLE_COLOR

        self.color_row_background = settings.COLOR_ROW_BACKGROUND
        self.color_foreground = settings.COLOR_FOREGROUND
        self.color_normal = settings.COLOR_NORMAL
        
        self.headers_table_book = settings.HEADERS_TABLE_BOOK
        self.headers_table_log = settings.HEADERS_TABLE_LOG

        self.str_log_singular = settings.STR_LOG_SINGULAR
        self.str_log_plural = settings.STR_LOG_PLURAL

        self.str_book_singular = settings.STR_BOOK_SINGULAR
        self.str_book_plural = settings.STR_BOOK_PLURAL

        self.str_hour_singular = settings.STR_HOUR_SINGULAR
        self.str_hour_plural = settings.STR_HOUR_PLURAL

        self.str_page_singular = settings.STR_PAGE_SINGULAR
        self.str_page_plural = settings.STR_PAGE_PLURAL

        self.str_minute_singular = settings.STR_MINUTE_SINGULAR
        self.str_minute_plural = settings.STR_MINUTE_PLURAL

        self.str_has_comments = settings.STR_HAS_COMMENTS

        self.str_no_pages = settings.STR_NO_PAGES
        self.str_no_author = settings.STR_NO_AUTHOR
        self.str_no_title = settings.STR_NO_TITLE
        self.str_no_logs = settings.STR_NO_LOGS
        self.str_no_depth = settings.STR_NO_DEPTH
        self.str_no_comments = settings.STR_NO_COMMENTS

        self.str_no_author_expand = settings.STR_NO_AUTHOR_EXPAND
        self.str_no_title_expand = settings.STR_NO_TITLE_EXPAND
        self.str_no_comments_expand = settings.STR_NO_COMMENTS_EXPAND

        self.action_delete = settings.ACTION_DELETE
        self.action_add = settings.ACTION_ADD
        self.action_edit = settings.ACTION_EDIT

        self.rows_book_expand = settings.ROWS_BOOK_EXPAND

        self.fields_log_info = settings.FIELDS_LOG_INFO
        self.fields_add_edit_book = settings.FIELDS_ADD_EDIT_BOOK
        self.fields_add_edit_log = settings.FIELDS_ADD_EDIT_LOG
        self.fields_usage = settings.FIELDS_USAGE

        self.header_usage = settings.HEADER_USAGE
        self.header_add_book = settings.HEADER_ADD_BOOK
        self.header_add_log = settings.HEADER_ADD_LOG
        self.header_edit_book = settings.HEADER_EDIT_BOOK
        self.header_edit_log = settings.HEADER_EDIT_LOG
        self.header_search = settings.HEADER_SEARCH
        self.header_remove = settings.HEADER_REMOVE
        self.header_show_all_books = settings.HEADER_SHOW_ALL_BOOKS
        self.header_show_book = settings.HEADER_SHOW_BOOK
        self.header_show_log = settings.HEADER_SHOW_LOG
        self.header_err_invalid_item_id = settings.HEADER_ERR_INVALID_ITEM_ID
        self.header_err_invalid_book_id = settings.HEADER_ERR_INVALID_BOOK_ID
        self.header_err_invalid_command = settings.HEADER_ERR_INVALID_COMMAND
        self.header_err_invalid_db_path = settings.HEADER_ERR_INVALID_DB_PATH

        self.err_invalid_item_id = settings.ERR_INVALID_ITEM_ID
        self.err_invalid_book_id = settings.ERR_INVALID_BOOK_ID
        self.err_required_field = settings.ERR_REQUIRED_FIELD
        self.err_log_exists = settings.ERR_LOG_EXISTS
        self.err_invalid_command = settings.ERR_INVALID_COMMAND
        self.err_invalid_db_path = settings.ERR_INVALID_DB_PATH

        self.msg_no_books = settings.MSG_NO_BOOKS
        self.msg_no_results = settings.MSG_NO_RESULTS
        self.msg_no_logs = settings.MSG_NO_LOGS

        self.limit_prompt_delete_book_title_length = settings.LIMIT_PROMPT_DELETE_BOOK_TITLE_LENGTH
        self.limit_query_print_length = settings.LIMIT_QUERY_PRINT_LENGTH

        self.prompt_delete = settings.PROMPT_DELETE

        self.responses_confirm = settings.RESPONSES_CONFIRM
      
    def _parse_layout_options(self, options, locals=None):
        layout = []

        if not options:
            return [('', 0, 'l')]

        for param, option in options.items():
            if param == 'BLANK':
                layout.append(('', option['span'], 'l'))
            else:
                if not option['show']:
                    continue
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
                items.append((string.ljust(width), width, align))
            if align == 'r':
                items.append((string.rjust(width), width, align))

        return items

    def _format_line(self, items, wrap=False, full_just=False, background_color=''):
        current_index = 0

        formatted_items = []

        for string, span, align in items:
            if span <= 0:
                continue

            width = (span - 1) * self.gutter + sum(self.columns[current_index:current_index+span])
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

            if self.enable_color:
                line_string = f'{self.color_foreground}{background_color}{line_string}{self.color_normal}'

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

    def _format_count_minute(self, minute_count):
        return self._format_count(minute_count, self.str_minute_plural, self.str_minute_singular)

    def _format_time(self, hours, minutes):
        hours_fmt = self._format_count_hour(hours)
        minutes_fmt = self._format_count_minute(minutes)
        if hours == 0:
            return minutes_fmt
        elif minutes == 0:
            return hours_fmt
        return f'{hours_fmt}, {minutes_fmt}'

    def print_line(self, items, wrap=False, new_line_before=False, new_line_after=False, full_just=False, background_color='', print_method=logging.info):
        line_strings = self._format_line(items, wrap, full_just, background_color)

        if new_line_before:
            print_method('')

        for line_string in line_strings:
            print_method(line_string)

        if new_line_after:
            print_method('')

    def print_empty_line(self):
        self.print_line([('', 1, 'l')])

    def print_item_count(self, book_count=None, log_count=None):
        string = ''

        log_count_string = self._format_count_log(log_count)
        book_count_string = self._format_count_book(book_count)

        if book_count is not None and log_count is not None:
            string = f'{book_count_string}, {log_count_string}'

        elif book_count is not None:
            string = book_count_string

        elif log_count is not None:
            string = log_count_string

        items = [self._indent, (string, self.span_footnote, 'l')]
        self.print_line(items, new_line_before=True)

    def print_header(self, header):
        items = [self._indent, (header, 6-self.span_indent, 'l')]
        self.print_line(items, new_line_after=True)

    def print_field(self, name, value):
        items = [self._indent, (name, self.span_field_name, self.align_field_name), (value, self.span_field_value, self.align_field_value)] 
        self.print_line(items, wrap=True)

    def print_action(self, action, **kwargs):
        items = [self._indent, (action, self.span_footnote, self.align_footnote)]
        self.print_line(items, **kwargs)

    def print_error(self, error, header=None, exit=False, **kwargs):
        if header:
            self.print_header(header)

        items = [self._indent, (error, self.span_footnote, self.align_footnote)]
        self.print_line(items, wrap=True, print_method=logging.error, **kwargs)

        if exit:
            sys.exit(1)

    def print_table_headers(self, headers, **kwargs):
        items = self._parse_layout_options(headers)
        self.print_line(items, **kwargs)

    def print_table_book(self, books, show_count=True):
        headers = self.headers_table_book
        highlight = True
        total_log_count = 0

        self.print_table_headers(headers)

        for book in books:
            id = book.id
            author = self.str_no_author if not book.author else book.author
            log_count = self.str_no_logs if not book.logs else len(book.logs)
            title = self.str_no_title if not book.title else book.title

            total_log_count += len(book.logs)

            items = self._parse_layout_options(headers, locals=locals())

            if self.enable_color and highlight:
                self.print_line(items, background_color=self.color_row_background, full_just=True)
                highlight = False
            else:
                self.print_line(items)
                highlight = True

        if show_count:
            self.print_item_count(len(books), total_log_count)

    def print_table_log(self, logs, show_count=True):
        headers = self.headers_table_log 
        highlight=True

        logs.sort(key=lambda r: r.date, reverse=True)

        self.print_table_headers(headers, new_line_before=True)

        for log in logs:
            book_id = log.book_id
            date = self.format_date.copy()
            time = f'{log.time_start.strftime("%H:%M")} {log.time_end.strftime("%H:%M")}'
            depth = log.depth if log.depth else self.str_no_depth
            comments = self.str_has_comments if log.comments else self.str_no_comments

            if log.page_start and log.page_end:
                pages = f'{str(log.page_start).ljust(4)} {str(log.page_end).ljust(4)}'
            else:
                pages = self.str_no_pages

            for item in date:
                date[item] = log.date.strftime(date[item])

            items = self._parse_layout_options(headers, locals=locals())

            if self.enable_color and highlight:
                self.print_line(items, background_color=self.color_row_background, full_just=True)
                highlight = False
            else:
                self.print_line(items)
                highlight = True

        if show_count:
            self.print_item_count(log_count=len(logs))
    
    def print_books(self, header, books, empty_message):
        self.print_header(header)

        if not books:
            self.print_error(empty_message)
        else:
            self.print_table_book(books)
        
    def print_book_expand(self, book, new_line_before=False, new_line_after=False):
        rows = self.rows_book_expand

        id = book.id
        title = self.str_no_title_expand if not book.title else book.title
        author = self.str_no_author_expand if not book.author else book.author

        if new_line_before:
            self.print_empty_line()

        for row in rows:
            items = self._parse_layout_options(row, locals=locals())
            self.print_line(items, wrap=True)

        if new_line_after:
            self.print_empty_line()

    def print_book_stats(self, book):
        total_page_count, total_hour_count = 0, 0

        for log in book.logs:
            if log.page_end and log.page_start:
                total_page_count += log.page_end - log.page_start
            total_hour_count += delta_from_time(log.time_start, log.time_end) / 3600

        items = [self._indent, (f'{self._format_count_page(total_page_count)}, {self._format_count_hour(round(total_hour_count, 1))}', 6-self.span_indent, 'l')]

        self.print_line(items, new_line_before=True)

    def print_book_info(self, book):
        header = self.header_show_book
        empty_message = self.msg_no_logs
        self.print_header(header)

        self.print_book_expand(book)
        
        if not book.logs:
            self.print_error(empty_message, new_line_before=True)
        else:
            self.print_book_stats(book)
            self.print_table_log(book.logs)
    
    def print_err_invalid_item_id(self):
        header = self.header_err_invalid_item_id
        error = self.err_invalid_item_id
        self.print_error(error, header=header, exit=True)

    def print_err_invalid_book_id(self):
        header = self.header_err_invalid_book_id
        error = self.err_invalid_book_id
        self.print_error(error, header=header, exit=True)

    def print_err_log_exists(self, hour, time_start):
        error = self.err_log_exists.format(hour, time_start)
        self.print_error(error, exit=True, new_line_before=True)

    def print_err_invalid_command(self):
        header = self.header_err_invalid_command
        error = self.err_invalid_command
        self.print_error(error, header=header, exit=True)

    def print_err_invalid_db_path(self):
        header = self.header_err_invalid_db_path
        error = self.err_invalid_db_path
        self.print_error(error, header=header, exit=True)

    def print_action_delete(self, response):
        action = self.action_delete[response]
        self.print_action(action, new_line_before=True)

    def print_action_add(self):
        action = self.action_add
        self.print_action(action, new_line_before=True)

    def print_action_edit(self):
        action = self.action_edit
        self.print_action(action, new_line_before=True)

    def print_usage(self):
        self.print_header(self.header_usage)
        for name, value in self.fields_usage.items():
            self.print_field(name,value)

    def print_all_books(self, books):
        header = self.header_show_all_books
        empty_message = self.msg_no_books
        self.print_books(header, books, empty_message)
    
    def print_search_results(self, query, results):
        query = self._truncate(query, self.limit_query_print_length)
        header = self.header_search.format(query)
        empty_message = self.msg_no_results
        self.print_books(header, results, empty_message)
    
    def print_log_info(self, book, log):
        header = self.header_show_log
        fields = self.fields_log_info

        time_read = delta_from_time(log.time_start, log.time_end)
        time_read = self._format_time(time_read // 3600, (time_read // 60)%60)
        pages_read = self.str_no_pages if not log.page_end or not log.page_start else log.page_end - log.page_start
        comments = self.str_no_comments_expand if not log.comments else log.comments

        self.print_header(header)
        self.print_book_expand(book, new_line_after=True)
        
        for var_name, name in fields.items():
            value = locals()[var_name]
            self.print_field(name, value)

        self.print_table_log([log])

    def input(self, name, accepted_responses={}, required=False, check_response=None, error='', bool=False, exit_on_error=False, error_on_empty=True):
        fields = [self._indent, (name, self.span_field_name, self.align_field_name)]
        line = self._format_line(fields)
        response = input(f'{line[0]}{self._gutter}')

        if not response and required:
            if error_on_empty:
                error = self.err_required_field.format(name) 

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
        header = self.header_remove
        prompt = self.prompt_delete

        if books:
            book_title = self._truncate(next(iter(books)).title, self.limit_prompt_delete_book_title_length)

        log_count = self._format_count_log(len(logs))
        book_count = self._format_count_book(len(books))
        text = ''

        if len(books) == 1 and logs:
            text += f'\"{book_title}\" and {log_count}'
        
        elif len(books) == 1 and not logs:
            text += f'\"{book_title}\"'
        
        elif books and logs:
            text += f'{book_count} and {log_count}'
        
        elif not books:
            text = log_count
        
        elif not logs:
            text = book_count

        prompt['prompt']['name'] = prompt['prompt']['name'].format(text)
        items = self._parse_layout_options(prompt)

        self.print_header(header)
        self.print_line(items, wrap=True)

        input = self.input('', accepted_responses=self.responses_confirm, bool=True, required=True, error_on_empty=False)

        return input

    def add_edit_item(self, header, fields, book=None):
        self.print_header(header)

        if book:
            self.print_book_expand(book, new_line_after=True)

        response = {} 

        for field in fields:
            name = fields[field]['name']
            check = fields[field]['check']
            error = fields[field]['error']
            required = fields[field]['required']

            response[field] = self.input(name, check_response=check, error=error, required=required, exit_on_error=True)

        return response

    def add_edit_book(self, header, check_fields, book=None):
        fields = self.fields_add_edit_book.copy()

        for field in fields:
            fields[field].update(check_fields[field])

        response = self.add_edit_item(header, fields, book=book)

        return response
    
    def add_edit_log(self, header, check_fields, book):
        fields = self.fields_add_edit_log.copy()

        for field in fields:
            fields[field].update(check_fields[field])

        response = self.add_edit_item(header, fields, book=book)

        return response

    def add_book(self, check_fields):
        header = self.header_add_book
        response = self.add_edit_book(header, check_fields)

        return response

    def add_log(self, check_fields, book):
        header = self.header_add_log
        response = self.add_edit_log(header, check_fields, book)

        return response

    def edit_book(self, check_fields, book):
        header = self.header_edit_book
        response = self.add_edit_book(header, check_fields, book=book)

        return response

    def edit_log(self, check_fields, book):
        header = self.header_edit_log
        response = self.add_edit_log(header, check_fields, book)

        return response


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
        query = select(Book).where(or_(Book.title.contains(query), Book.author.contains(query)))
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

    def update_book(self, book_id, info):
        with session_scope() as session:
            query = update(Book).where(Book.id == book_id).values(**info)
            session.execute(query)

    def update_log(self, date, time_start, info):
        with session_scope() as session:
            query = update(Log).where(self._log_id(date, time_start)).values(**info)
            session.execute(query)

    def insert_log(self, info):
        with session_scope() as session:
            query = insert(Log).values(**info)
            session.execute(query)

    def insert_book(self, info):
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


def is_valid_book_title(title):
    if len(title) > settings.LIMIT_BOOK_TITLE_LENGTH:
        return False

    return title 


def is_valid_author_name(name):
    if len(name) > settings.LIMIT_AUTHOR_NAME_LENGTH:
        return False

    return name


def is_valid_date(date):
    try:
        date = datetime.strptime(date, settings.INPUT_DATE_FORMAT)
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


def is_valid_comments(comments):
    if len(comments) > settings.LIMIT_COMMENTS_LENGTH:
        return False

    return comments


def is_valid_depth(depth):
    try:
        depth = int(depth)
        return depth
    except ValueError:
        return False


class Add:
    def __init__(self):
        self.db = DB()
        self.printer = Printer()

        self.fields_add_book = {
            'title': {
                'required': False,
                'check': is_valid_book_title
            },
            'author': {
                'required': False,
                'check': is_valid_author_name
            }
        }
        self.fields_add_log = {
            'date': {
                'required': True,
                'check': is_valid_date
            },
            'time': {
                'required': True,
                'check': is_valid_time_span
            },
            'pages': {
                'required': False,
                'check': is_valid_page_span,
            },
            'depth': {
                'required': False,
                'check': is_valid_depth,
            },
            'comments': {
                'required': False,
                'check': is_valid_comments
            }
        }

    def run(self, args):
        if args == []:
            response = self.printer.add_book(self.fields_add_book)
            self.db.insert_book(response)
            self.printer.print_action_add()

            return True

        book = get_book(args[0])

        if not book:
            self.printer.print_err_invalid_book_id()

        elif len(args) == 1:
            response  = self.printer.add_log(self.fields_add_log, book)
            response = {
                'book_id': book.id, 
                'date': response['date'], 
                'time_start': response['time'][0], 
                'time_end': response['time'][1], 
                'page_start': response['pages'][0] if response['pages'] else None, 
                'page_end': response['pages'][1] if response['pages'] else None,
                'depth': response['depth'], 
                'comments': response['comments']
            }

            log_id = (response['date'], response['time_start'])

            if self.db._is_valid_log_id(*log_id):
                self.printer.print_err_log_exists(*log_id)

            self.db.insert_log(response)
            self.printer.print_action_add()

            return True

        return False


class Edit:
    def __init__(self):
        self.db = DB()
        self.printer = Printer()

        self.fields_edit_book = {
            'title': {
                'required': False,
                'check': is_valid_book_title
            },
            'author': {
                'required': False,
                'check': is_valid_author_name
            }
        }
        self.fields_edit_log = {
            'date': {
                'required': True,
                'check': is_valid_date
            },
            'time': {
                'required': True,
                'check': is_valid_time_span
            },
            'pages': {
                'required': False,
                'check': is_valid_page_span,
            },
            'depth': {
                'required': False,
                'check': is_valid_depth,
            },
            'comments': {
                'required': False,
                'check': is_valid_comments
            }
        }

    def run(self, args):
        if len(args) != 1:
            return False

        item = get_item(args[0])

        if not item:
            self.printer.print_err_invalid_item_id()

        if isinstance(item, Log):
            response = self.printer.edit_log(self.fields_edit_log, item.book)
            response = {
                'date': response['date'], 
                'time_start': response['time'][0], 
                'time_end': response['time'][1], 
                'page_start': response['pages'][0] if response['pages'] else None, 
                'page_end': response['pages'][1] if response['pages'] else None,
                'depth': response['depth'], 
                'comments': response['comments']
            }

            self.db.update_log(item.date, item.time_start, response)
            self.printer.print_action_edit()
            pass

        elif isinstance(item, Book):
            response = self.printer.edit_book(self.fields_edit_book, item)
            self.db.update_book(item.id, response)
            self.printer.print_action_edit()

        return True


class Remove:
    def __init__(self):
        self.db = DB()
        self.printer = Printer()

    def run(self, args):
        if len(args) < 1:
            return False
        
        books, logs = set(), set()

        for arg in args:
            item = get_item(arg)

            if not item:
                self.printer.print_err_invalid_item_id()
            
            if isinstance(item, Log):
                logs.add(item)

            elif isinstance(item, Book):
                books.add(item)
                for log in item.logs:
                    logs.add(log)

        confirm = self.printer.confirm_delete(books, logs)

        if confirm:
            self.db.delete_items(logs | books)

        self.printer.print_action_delete(confirm)

        return True


class Show:
    def __init__(self):
        self.db = DB()
        self.printer = Printer()

    def run(self, args):
        if args == []:
            books = self.db.get_all_books()
            self.printer.print_all_books(books)

            return True

        item = get_item(args[0])

        if not item:
            self.printer.print_err_invalid_item_id()
        
        if len(args) == 1 and item:
            if isinstance(item, Log):
                book = self.db.book_obj(item.book_id)
                self.printer.print_log_info(book, item)

            elif isinstance(item, Book):
                self.printer.print_book_info(item)

            return True

        return False


class Search:
    def __init__(self):
        self.db = DB()
        self.printer = Printer()


    def run(self, args):
        if len(args) == 1:
            results = self.db.search(args[0])

            self.printer.print_search_results(args[0], results)

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
        command = command()
    except KeyError:
        printer.print_err_invalid_command()

    if not command.run(args):
        printer.print_usage()
        sys.exit(1)
    
    engine.dispose()
        

if __name__ == "__main__":
    main()
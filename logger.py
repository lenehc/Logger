import argparse
import sqlite3
import logging

from datetime import datetime
from random import randint


WIDTH = [6, 38, 15, 10]

def _FORMAT_STR(fields):
    fmt_fields = []
    for i,x in enumerate(fields):
        colw = WIDTH[i]
        if len(x) > colw:
            x = f'{x[:colw-2]}..'
        fmt_fields.append(x.ljust(colw))
    return "   ".join(fmt_fields)

LOG_TABLE_HEADERS = ['log-id', 'date         time-span', 'page-span', 'depth']
BOOK_TABLE_HEADERS = ['id', 'title', 'tag', 'log-count']

LOG_TABLE_HEADERS_STR = _FORMAT_STR(LOG_TABLE_HEADERS)
BOOK_TABLE_HEADERS_STR = _FORMAT_STR(BOOK_TABLE_HEADERS)


class ParseArgs():
    '''
    Main class for argument parsing.
    '''
    def __init__(self, cursor):
        self.cursor = cursor
        self.args = self._parse_args()

    def _log_id(self, log_id):
        '''
        argparse argument type for log-ids.
        '''
        if log_id == 'all':
            return log_id

        try:
            query = "SELECT EXISTS (SELECT 1 FROM logs WHERE id = ?)"
            if self.cursor.execute(query, (log_id,)).fetchone()[0]:
                return int(log_id)

        except:
            pass

        raise argparse.ArgumentTypeError('invalid log id.') 

    def _book_id(self, book_id):
        '''
        argparse argument type for book-ids.
        '''
        if book_id == 'all':
            return book_id

        try:
            query = "SELECT EXISTS (SELECT 1 FROM books WHERE id = ?)"
            if self.cursor.execute(query, (book_id,)).fetchone()[0]:
                return int(book_id)
            
        except:
            pass

        raise argparse.ArgumentTypeError('invalid book id.') 

    def _parse_args(self):
        '''
        Run the parsing process.
        '''
        parser = argparse.ArgumentParser(
            prog='logger',
            usage='logger [-h] <command> <options> [<args>]',
            epilog='expected log format: \'<date> <time-span> <page-span> <depth>\' (ex: \'2023-01-01 12:00-12:30 123-456 1\'), depth value is numerical.')

        subparsers = parser.add_subparsers(dest='command', required=True)

        add = subparsers.add_parser('add', allow_abbrev=False)
        add_group = add.add_mutually_exclusive_group(required=True)
        add_group.add_argument('-l', '--log', type=self._book_id)
        add_group.add_argument('-b', '--book')

        change = subparsers.add_parser('change', allow_abbrev=False)
        change_group = change.add_mutually_exclusive_group(required=True)
        change_group.add_argument('-l', '--log', type=self._log_id)
        change_group.add_argument('-b', '--book', type=self._book_id)

        delete = subparsers.add_parser('delete', allow_abbrev=False)
        delete_group = delete.add_mutually_exclusive_group(required=True)
        delete_group.add_argument('-l', '--log', type=self._log_id)
        delete_group.add_argument('-b', '--book', type=self._book_id)

        show = subparsers.add_parser('show', allow_abbrev=False)
        show_group = show.add_mutually_exclusive_group(required=True)
        show_group.add_argument('-l', '--log', type=self._log_id, nargs='?', const='all')
        show_group.add_argument('-b', '--book', nargs='?', const='all', type=self._book_id)

        search = subparsers.add_parser('search', allow_abbrev=False)
        search_group = search.add_mutually_exclusive_group(required=True)
        search_group.add_argument('-t', '--title')
        search_group.add_argument('-g', '--tag')

        return parser.parse_args()


class Logger():
    def __init__(self, conn):
        '''
        Main class for logging.
        '''
        self.conn = conn 
        self.cursor = self.conn.cursor()
        self.args = ParseArgs(self.cursor).args
    
    def _setup_db(self):
        '''
        Create 'books' and 'logs' table in database if they don't
        already exist.
        '''
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS books (
                    id  INT  PRIMARY KEY,
                    title  TEXT  NOT NULL,
                    tag  TEXT
                )''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
                    id  INT  PRIMARY KEY,
                    book_id  INT  NOT NULL,
                    date  DATE  NOT NULL,
                    time_start  TIME  NOT NULL,
                    time_end  TIME  NOT NULL,
                    page_start  INT  NOT NULL,
                    page_end  INT  NOT NULL,
                    depth  INT  NOT NULL,
                    CONSTRAINT log_fk
                        FOREIGN KEY (book_id)
                        REFERENCES books(id) ON DELETE CASCADE
                )''')
        
    def _get_id(self, type):
        '''
        Generate a random book-id or log-id that doesn't already
        exist.
        '''
        while True:
            id = randint(100, 999)

            if type == 'log':
                query = "SELECT 1 FROM logs WHERE id = ?"
                
            elif type == 'book':
                query = "SELECT 1 FROM books WHERE id = ?"
                
            if not self.cursor.execute(query, (id,)).fetchone():
                return id

    def _get_log(self, prompt):
        '''
        Prompt user for log and report invalid entries.
        '''
        log = input(prompt)
        details = log.split()

        if len(details) != 4:
            logging.error('\ninvalid log.')
            return

        try:
            date = str(datetime.strptime(details[0], '%Y-%m-%d').date())
            time_start, time_end = (str(datetime.strptime(x, '%H:%M').time())[:-3] for x in details[1].split('-'))
            page_start, page_end = (abs(int(x)) for x in details[2].split('-'))
            depth = abs(int(details[3]))

            if time_start > time_end or page_start > page_end:
                logging.error('\ninvalid log.')

                return

            return (date, (time_start,time_end), (page_start,page_end), depth)

        except:
            logging.error('\ninvalid log.')
            return
            
    def _get_title_from_log_id(self, log_id):
        '''
        Fetch the associated book title, given a log-id.
        '''
        query = """
            SELECT books.title
            FROM logs
            INNER JOIN books ON logs.book_id = books.id
            WHERE logs.id = ?
            """
        title = self.cursor.execute(query, (log_id,)).fetchone()[0]
        return title

    def _get_title_from_book_id(self, book_id):
        '''
        Fetch the associated book title, given a book-id.
        '''
        query = "SELECT title FROM books WHERE id = ?"
        title = self.cursor.execute(query, (book_id,)).fetchone()[0]
        return title
            
    def _get_log_count(self, book_id):
        '''
        Fetch the total number of logs associated, given a book-id.
        '''
        query = "SELECT COUNT(*) FROM logs WHERE book_id = ?"
        log_count = self.cursor.execute(query, (book_id,)).fetchone()[0]
        return log_count
 
    def _confirm(self, prompt):
        '''
        Loop until user responds with 'y' or 'n', return the
        corresponding boolean value.
        '''
        valid_responses = {'y', 'n'}
        
        while True:
            conf = input(prompt).lower()

            if conf in valid_responses:
                return conf == 'y'
 
    def _format_title(self, book_id):
        '''
        Return a correctly formatted string containing a book's title
        and id, given a book-id.
        '''
        query = "SELECT title, tag FROM books WHERE id = ?"
        title, tag = self.cursor.execute(query, (book_id,)).fetchone()
        log_count = self._get_log_count(book_id)

        fields = [str(book_id), title, tag, str(log_count)]

        return _FORMAT_STR(fields)

    def _format_log(self, log_id):
        '''
        Return a correctly formatted string containing a log's: id,
        date, time-span, page-span and depth, given a log-id.
        '''
        query = "SELECT * FROM logs WHERE id = ?"
        log = self.cursor.execute(query, (log_id,)).fetchone()

        page_span = f'{log[5]}-{log[6]}'
        date_time = f'{log[2]}   {log[3]}-{log[4]}'

        fields = [str(log_id), date_time, f'pp.{page_span}', str(log[7])]

        return _FORMAT_STR(fields)
                
    def print_log(self, log_id=None):
        '''
        Print the corresponding information, if given a log-id,
        otherwise print all logs.
        '''
        if log_id:
            title = self._get_title_from_log_id(log_id)
            logging.info(f'log for \'{title}\'.\n\n{LOG_TABLE_HEADERS_STR}\n{self._format_log(log_id)}')

        else:
            query = "SELECT id FROM logs ORDER BY date ASC"
            log_ids = self.cursor.execute(query).fetchall()
            logging.info(f'found {len(log_ids)} log(s).\n\n{LOG_TABLE_HEADERS_STR}')

            for log_id in log_ids:
                logging.info(self._format_log(log_id[0]))

    def print_book(self, book_id=None):
        '''
        Print a book's: information and all corresponding logs,
        otherwise print all books.
        '''
        if book_id:
            query = "SELECT id FROM logs WHERE book_id = ? ORDER BY date ASC"
            log_ids = self.cursor.execute(query, (book_id,)).fetchall()
            logging.info(f'{BOOK_TABLE_HEADERS_STR}\n{self._format_title(book_id)}\n\n{LOG_TABLE_HEADERS_STR}')

            for log_id in log_ids:
                logging.info(self._format_log(log_id[0]))

        else:
            query = "SELECT id FROM books ORDER BY title ASC"
            book_ids = self.cursor.execute(query).fetchall()
            logging.info(f'found {len(book_ids)} book(s).\n\n{BOOK_TABLE_HEADERS_STR}')

            for book_id in book_ids:
                logging.info(self._format_title(book_id[0]))
       
    def add_log(self):
        '''
        Prompt the user for log information, ask for confirmation, and
        insert into the database accordingly. 
        '''
        title = self._get_title_from_book_id(self.args.log)

        logging.info(f'inserting log for \'{title}\'.\n')

        log = self._get_log('(enter log) ')

        if not log:
            return

        if self._confirm(f'(confirm insertion of log [Y/n]) '):
            id = int(str(self.args.log) + str(self._get_id('log')))
            query = "INSERT INTO logs (id, book_id, date, time_start, time_end, page_start, page_end, depth) VALUES(?,?,?,?,?,?,?,?)"
            self.cursor.execute(query, (id, self.args.log, log[0], log[1][0], log[1][1], log[2][0], log[2][1], log[3]))

            logging.info(f'\n{LOG_TABLE_HEADERS_STR}\n{self._format_log(id)}\n\ninserted log.')
            return

        logging.info('\naborted.')
        return
   
    def add_book(self):
        '''
        Prompt the user for confirmation of book insertion, and insert
        into the database accordingly. 
        '''
        logging.info(f'inserting \'{self.args.book}\'.\n')

        tag = input('(enter tag) ')

        if self._confirm(f'(confirm insertion [Y/n]) '):
            id = self._get_id('book')
            query = "INSERT INTO books (id, title, tag) VALUES(?,?,?)"
            self.cursor.execute(query, (id, self.args.book, tag))

            logging.info(f'\n{BOOK_TABLE_HEADERS_STR}\n{self._format_title(id)}\n\ninserted book.')
            return

        logging.info('\naborted.')
        return
    
    def change_log(self):
        '''
        Prompt the user for new log information, ask for confirmation,
        and insert into the database accordingly. 
        '''
        title = self._get_title_from_log_id(self.args.log)

        logging.info(f'changing log for \'{title}\'.\n\n{LOG_TABLE_HEADERS_STR}\n{self._format_log(self.args.log)}\n')

        log = self._get_log('(enter new log) ')

        if not log:
            return

        if self._confirm(f'(confirm changes [Y/n]) '):
            query = "UPDATE logs SET date = ?, time_start = ?, time_end = ?, page_start = ?, page_end = ?, depth = ? WHERE log_id = ?"
            self.cursor.execute(INSERT_LOG_QUERY, (log[0], log[1][0], log[1][1], log[2][0], log[2][1], log[3], self.args.log))
            logging.info(f'\n{self._format_log(self.args.log)}\n\nchanged log.')
            return

        logging.info('\naborted.')
        return

    def change_book(self):
        '''
        Prompt the user for new book title, ask for confirmation,
        and insert into the database accordingly. 
        '''
        title = self._get_title_from_book_id(self.args.book)
        
        logging.info(f'changing \'{title}\'.\n')

        new_title = input('(enter new title) ')
        new_tag = input('(enter new tag) ')

        if self._confirm(f'(confirm changes [Y/n]) '):
            query = "UPDATE books SET title = ?, tag = ? WHERE id = ?"
            self.cursor.execute(query, (new_title, new_tag, self.args.book))

            logging.info(f'\n{BOOK_TABLE_HEADERS_STR}\n{self._format_title(self.args.book)}\n\nchanged book.')
            return

        logging.info('\naborted.')
        return
        
    
    def delete_log(self):
        '''
        Prompt the user for confirmation of log deletion, and delete
        from the database accordingly.
        '''
        title = self._get_title_from_log_id(self.args.log)

        logging.info(f'deleting log for \'{title}\'.\n\n{LOG_TABLE_HEADERS_STR}\n{self._format_log(self.args.log)}')

        if self._confirm(f'\n(confirm deletion [Y/n]) '):
            query = "DELETE FROM logs WHERE id = ?"
            self.cursor.execute(query, (self.args.log,))

            logging.info(f'\ndeleted log.')
            return

        logging.info('\naborted.')
        return

    def delete_book(self):
        '''
        Prompt the user for confirmation of book deletion, and delete
        from the database accordingly.
        '''
        title = self._get_title_from_book_id(self.args.book)
        log_count = self._get_log_count(self.args.book)

        logging.info(f'deleting \'{title}\' and {log_count} log(s).\n')

        if self._confirm(f'(confirm deletion [Y/n]) '):
            query = "DELETE FROM books WHERE id = ?"
            self.cursor.execute(query, (self.args.book,))
            logging.info(f'\ndeleted book.')
            return

        logging.info('\naborted.')
        return
    
    def show_log(self):
        '''
        If the user provided a log-id print the corresponding log
        information, otherwise print all logs.
        '''
        if self.args.log == 'all':
            self.print_log()
            return

        self.print_log(self.args.log)
        return

    def show_book(self):
        '''
        If the user provided a book-id print the corresponding book
        information, otherwise print all logs.
        '''
        if self.args.book == 'all':
            self.print_book()
            return

        self.print_book(self.args.book)
        return
    
    def search_title(self):
        query = f"SELECT id FROM books WHERE title LIKE '%' || ? || '%'"
        results = self.cursor.execute(query, (self.args.title,)).fetchall()

        logging.info(f'{len(results)} result(s) for title \'{self.args.title}\'.\n\n{BOOK_TABLE_HEADERS_STR}')

        for book in results:
            logging.info(self._format_title(book[0]))

    def search_tag(self):
        query = f"SELECT id FROM books WHERE tag LIKE '%' || ? || '%'"
        results = self.cursor.execute(query, (self.args.tag,)).fetchall()

        logging.info(f'{len(results)} result(s) for tag \'{self.args.tag}\'.\n\n{BOOK_TABLE_HEADERS_STR}')

        for book in results:
            logging.info(self._format_title(book[0]))

   
    def run(self):
        '''
        Run the logging process.
        '''
        with self.conn:
            self._setup_db()

            if self.args.command == 'add':
                if self.args.log:
                    self.add_log()

                elif self.args.book:
                    self.add_book()

            elif self.args.command == 'change':
                if self.args.log:
                    self.change_log()

                elif self.args.book:
                    self.change_book()

            elif self.args.command == 'delete':
                if self.args.log:
                    self.delete_log()
                
                elif self.args.book:
                    self.delete_book()

            elif self.args.command == 'show':
                if self.args.log:
                    self.show_log()

                elif self.args.book:
                    self.show_book()

            elif self.args.command == 'search':
                if self.args.title:
                    self.search_title()

                elif self.args.tag:
                    self.search_tag()


def main():
    '''
    Configure logging, connect to database and create a new 'Logger'
    instance.
    '''
    logging.basicConfig(format='%(message)s', level=logging.INFO)
    conn = sqlite3.Connection('.logger.db')
    conn.execute("PRAGMA foreign_keys = 1")
    Logger(conn).run()


if __name__ == '__main__':
    main()

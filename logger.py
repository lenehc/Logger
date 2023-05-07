import argparse
import sqlite3
import logging

from datetime import datetime
from random import randint


TITLE_PRINT_LIMIT = 38
LOG_TABLE_HEADERS = 'log-id   date        time-span     page-span      depth'
BOOK_TABLE_HEADERS = 'id       title'
INSERT_LOG_QUERY = "INSERT INTO logs (id, book_id, date, time_start, time_end, page_start, page_end, depth) VALUES(?,?,?,?,?,?,?,?)"

        
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
            epilog='expected log format: \'<date> <time-span> <page-span> <depth>\' (ex: \'2023-01-01 12:00-12:30 123-456 1\'), the depth value is numerical.',
            allow_abbrev=False)

        subparsers = parser.add_subparsers(dest='command', required=True)

        add = subparsers.add_parser('add')
        add_group = add.add_mutually_exclusive_group(required=True)
        add_group.add_argument('--log', type=self._book_id)
        add_group.add_argument('--book')

        change = subparsers.add_parser('change')
        change_group = change.add_mutually_exclusive_group(required=True)
        change_group.add_argument('--log', type=self._log_id)
        change_group.add_argument('--book', type=self._book_id)

        delete = subparsers.add_parser('delete')
        delete_group = delete.add_mutually_exclusive_group(required=True)
        delete_group.add_argument('--log', type=self._log_id)
        delete_group.add_argument('--book', type=self._book_id)

        show = subparsers.add_parser('show')
        show_group = show.add_mutually_exclusive_group(required=True)
        show_group.add_argument('--log', type=self._log_id, nargs='?', const='all')
        show_group.add_argument('--book', nargs='?', const='all', type=self._book_id)

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
                    ID  INT  PRIMARY KEY,
                    TITLE  TEXT
                )''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
                    ID  INT  PRIMARY KEY,
                    BOOK_ID  INT  NOT NULL,
                    DATE  DATE  NOT NULL,
                    TIME_START  TIME  NOT NULL,
                    TIME_END  TIME  NOT NULL,
                    PAGE_START  INT  NOT NULL,
                    PAGE_END  INT  NOT NULL,
                    DEPTH  INT  NOT NULL
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
            JOIN books ON logs.book_id = books.id
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
        title = self._get_title_from_book_id(book_id)
        log_count = self._get_log_count(book_id)

        title = (title[:TITLE_PRINT_LIMIT-2] + '..') if len(title) > TITLE_PRINT_LIMIT else title
        base_str = f'{book_id}      {title.ljust(TITLE_PRINT_LIMIT)}' 
        
        if log_count > 0:
            return f'{base_str}   [{log_count} log(s)]'

        return base_str

    def _format_log(self, log_id):
        '''
        Return a correctly formatted string containing a log's: id,
        date, time-span, page-span and depth, given a log-id.
        '''
        query = "SELECT * FROM logs WHERE id = ?"
        log = self.cursor.execute(query, (log_id,)).fetchone()

        time_span = f'{log[3]}-{log[4]}'
        page_span = f'{log[5]}-{log[6]}'

        return f'{log[0]}   {log[2]}  {time_span}   pp.{page_span.ljust(9)}   {log[7]}'
                
    def print_log(self, log_id=None):
        '''
        Print the corresponding information, if given a log-id,
        otherwise print all logs.
        '''
        if log_id:
            title = self._get_title_from_log_id(log_id)
            logging.info(f'log for \'{title}\'.\n\n{LOG_TABLE_HEADERS}\n{self._format_log(log_id)}')

        else:
            query = "SELECT id FROM logs ORDER BY date ASC"
            log_ids = self.cursor.execute(query).fetchall()
            logging.info(f'found {len(log_ids)} log(s).\n\n{LOG_TABLE_HEADERS}')

            for log_id in log_ids:
                logging.info(self._format_log(log_id[0]))

    def print_book(self, book_id=None):
        '''
        Print a book's:  information and all corresponding logs,
        otherwise print all books.
        '''
        if book_id:
            query = "SELECT id FROM logs WHERE book_id = ? ORDER BY date ASC"
            log_ids = self.cursor.execute(query, (book_id,)).fetchall()
            logging.info(f'{BOOK_TABLE_HEADERS}\n{self._format_title(book_id)}\n\n{LOG_TABLE_HEADERS}')

            for log_id in log_ids:
                logging.info(self._format_log(log_id[0]))

        else:
            book_ids = self.cursor.execute("SELECT id FROM books ORDER BY title ASC").fetchall()
            logging.info(f'found {len(book_ids)} book(s).\n\n{BOOK_TABLE_HEADERS}')

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
            self.cursor.execute(INSERT_LOG_QUERY, (id, self.args.log, log[0], log[1][0], log[1][1], log[2][0], log[2][1], log[3]))
            self.conn.commit()

            logging.info(f'\n{LOG_TABLE_HEADERS}\n{self._format_log(id)}\n\ninserted log.')
            return

        logging.info('\naborted.')
        return
   
    def add_book(self):
        '''
        Prompt the user for confirmation of book insertion, and insert
        into the database accordingly. 
        '''
        logging.info(f'inserting \'{self.args.book}\'.\n')

        if self._confirm(f'(confirm insertion [Y/n]) '):
            id = self._get_id('book')
            self.cursor.execute("INSERT INTO books (id, title) VALUES(?,?)", (id, self.args.book))
            self.conn.commit()

            logging.info(f'\n{BOOK_TABLE_HEADERS}\n{self._format_title(id)}\n\ninserted book.')
            return

        logging.info('\naborted.')
        return
    
    def change_log(self):
        '''
        Prompt the user for new log information, ask for confirmation,
        and insert into the database accordingly. 
        '''
        title = self._get_title_from_log_id(self.args.log)

        logging.info(f'changing log for \'{title}\'.\n\n{LOG_TABLE_HEADERS}\n{self._format_log(self.args.log)}\n')

        log = self._get_log('(enter new log) ')

        if not log:
            return

        if self._confirm(f'(confirm change [Y/n]) '):
            self.cursor.execute("DELETE FROM logs WHERE id = ?", (self.args.log,))
            self.cursor.execute(INSERT_LOG_QUERY, (self.args.log, book_id, log[0], log[1][0], log[1][1], log[2][0], log[2][1], log[3]))
            self.conn.commit()
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

        if self._confirm(f'(confirm change [Y/n]) '):
            self.cursor.execute("DELETE FROM books WHERE id = ?", (self.args.book,))
            self.cursor.execute("INSERT INTO books (id, title) VALUES(?,?)", (self.args.book, new_title))
            self.conn.commit()

            logging.info(f'\n{BOOK_TABLE_HEADERS}\n{self._format_title(self.args.book)}\n\nchanged book.')
            return

        logging.info('\naborted.')
        return
        
    
    def delete_log(self):
        '''
        Prompt the user for confirmation of log deletion, and delete
        from the database accordingly.
        '''
        title = self._get_title_from_log_id(self.args.log)

        logging.info(f'deleting log for \'{title}\'.\n\n{LOG_TABLE_HEADERS}\n{self._format_log(self.args.log)}')

        if self._confirm(f'\n(confirm deletion [Y/n]) '):
            self.cursor.execute("DELETE FROM logs WHERE id = ?", (self.args.log,))
            self.conn.commit()

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
            self.cursor.execute("DELETE FROM books WHERE id = ?", (self.args.book,))
            self.conn.commit()
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


def main():
    '''
    Configure logging, instantiate a conection with the 'books.db'
    file, and create a new 'Logger' instance.
    '''
    logging.basicConfig(format='%(message)s', level=logging.INFO)
    conn = sqlite3.Connection('.logger.db')
    Logger(conn).run()


if __name__ == '__main__':
    main()

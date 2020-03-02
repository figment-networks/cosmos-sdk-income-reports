from sqlite3 import connect, PARSE_DECLTYPES, PARSE_COLNAMES, Row
from collections import namedtuple


class Db():
    def __init__(self, path, denom, scale, debug=False):
        self.debug = debug
        self.__conn = connect(path, detect_types=PARSE_DECLTYPES|PARSE_COLNAMES)
        self.__conn.row_factory = Row
        self.__migrate_schema()

        self.denom = denom
        self.scale = scale

    def commit(self):
        self.__conn.commit()

    def get_accounts(self):
        c = self.__conn.cursor()
        r = c.execute('''
            SELECT * FROM accounts;
        ''')
        return [
            namedtuple('Account', ' '.join(r.keys()))(**r) \
            for r in c.fetchall()
        ]

    def add_account(self, address, height):
        c = self.__conn.cursor()
        c.execute('''
            INSERT OR IGNORE INTO accounts (address, first_seen_height)
            VALUES (?, ?);
        ''', (address, height))

    def get_latest_report_height_for(self, address):
        c = self.__conn.cursor()
        r = c.execute('''
            SELECT * FROM reports
            WHERE address = ? AND denom = ?
            ORDER BY height DESC
            LIMIT 1;
        ''', (address, self.denom))
        row = r.fetchone()
        if row is None: return 0
        return row['height']

    def insert_report(self, address, run, values):
        self.__conn.execute('''
            INSERT INTO reports(timestamp, height, address, denom,
                                pending_rewards, pending_commission, withdrawals)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        ''', (
            run.target_timestamp,
            run.height,
            address,
            self.denom,
            values['pending_rewards'],
            values['pending_commission'],
            values['withdrawals'],
        ))

    def get_full_report(self, address):
        c = self.__conn.cursor()
        r = c.execute('''
            SELECT * FROM reports
            WHERE address = ? AND denom = ?
            ORDER BY timestamp ASC;
        ''', (address, self.denom))
        rows = r.fetchall()

        def process(i, row):
            row = dict(row)
            last_state = rows and (i-1 >= 0) and rows[i-1] or {
                'pending_commission': 0,
                'pending_rewards': 0
            }

            # to calculate income:
            #   total withdrawals +
            #   today's pending rewards - yesterday's pending rewards -
            #   today's pending commission - yesterday's pending commission
            income = row['withdrawals'] + \
                     row['pending_commission'] - last_state['pending_commission'] + \
                     row['pending_rewards'] - last_state['pending_rewards']

            scale = lambda amount: round(amount * 10**-self.scale, 3)
            row['income'] = scale(income)
            row['withdrawals'] = scale(row['withdrawals'])
            row['pending_commission'] = scale(row['pending_commission'])
            row['pending_rewards'] = scale(row['pending_rewards'])

            return namedtuple('ReportLine', ' '.join(row.keys()))(**row)

        return [process(i, row) for (i, row) in enumerate(rows)]

    def create_run(self, height, target_time):
        c = self.__conn.cursor()
        c.execute('''
            INSERT OR IGNORE INTO runs(target_timestamp, height, denom)
            VALUES (?, ?, ?)
        ''', (target_time, height, self.denom))
        run_id = c.lastrowid

        c.execute('''
            UPDATE runs
            SET status = 'RUNNING'
            WHERE rowid = ?;
        ''', (run_id,))
        self.commit()

        return run_id

    def get_runs(self, after=None):
        c = self.__conn.cursor()
        extra_timestamp_filter = " AND target_timestamp > ? " if after else ''
        args = (self.denom,)

        if after: args += (after.target_timestamp,)

        r = c.execute(f'''
            SELECT rowid, * FROM runs
            WHERE denom = ? {extra_timestamp_filter}
            ORDER BY height ASC;
        ''', args)

        return [
            namedtuple('Run', ' '.join(r.keys()))(**r) \
            for r in c.fetchall()
        ]

    def get_latest_run(self):
        c = self.__conn.cursor()
        r = c.execute('''
            SELECT rowid, * FROM runs
            WHERE denom = ? AND status = 'OK'
            ORDER BY height DESC
            LIMIT 1;
        ''', (self.denom,))
        row = r.fetchone()
        if row is None: return None
        return namedtuple('Run', ' '.join(row.keys()))(**row)

    def get_previous_run(self, run):
        c = self.__conn.cursor()
        r = c.execute('''
            SELECT rowid, * FROM runs
            WHERE denom = ? AND height < ?
            ORDER BY height DESC
            LIMIT 1;
        ''', (self.denom, run.height))
        row = r.fetchone()
        if row is None: return None
        return namedtuple('Run', ' '.join(row.keys()))(**row)

    def run_for_target_time(self, target_time):
        c = self.__conn.cursor()
        r = c.execute('''
            SELECT rowid, * FROM runs
            WHERE denom = ? AND target_timestamp = ?
            ORDER BY height DESC
            LIMIT 1;
        ''', (self.denom, target_time))
        row = r.fetchone()
        if row is None: return None
        return namedtuple('Run', ' '.join(row.keys()))(**row)

    def run_ok(self, run):
        self.__conn.execute('''
            UPDATE runs
            SET status = 'OK'
            WHERE rowid = ?;
        ''', (run.rowid,))
        self.commit()

    def run_error(self, run):
        self.__conn.execute('''
            UPDATE runs
            SET status = 'ERROR'
            WHERE rowid = ?;
        ''', (run.rowid,))
        self.commit()

    def __migrate_schema(self):
        self.__conn.execute('''
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                timestamp TIMESTAMP
            );
        ''')

        # check current version
        c = self.__conn.cursor()
        c.execute('''
            SELECT MAX(version)
            AS current_version
            FROM schema_version
        ''')
        version = c.fetchone()['current_version'] or 0

        if self.debug:
            print("\tSCHEMA VERSION: %s, LATEST %s" % (version, 1))

        # initial version
        if version < 1:
            if self.debug:
                print("\t\tMIGRATING TO SCHEMA VERSION 1...")

            self.__conn.execute('''
                CREATE TABLE IF NOT EXISTS reports (
                    timestamp TIMESTAMP,
                    height INTEGER,
                    address TEXT,
                    denom TEXT,
                    pending_rewards INTEGER,
                    pending_commission INTEGER,
                    withdrawals INTEGER
                );
            ''')
            self.__conn.execute('''
                CREATE TABLE IF NOT EXISTS runs (
                    target_timestamp TIMESTAMP,
                    height INTEGER,
                    denom TEXT,
                    status TEXT
                );
            ''')
            self.__conn.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    address TEXT,
                    first_seen_height INTEGER
                );
            ''')

            self.__conn.execute('''
                CREATE INDEX IF NOT EXISTS reports_addr_denom
                ON reports (address, denom);
            ''')
            self.__conn.execute('''
                CREATE UNIQUE INDEX IF NOT EXISTS runs_height_denom
                ON runs (height, denom);
            ''')
            self.__conn.execute('''
                CREATE INDEX IF NOT EXISTS runs_denom
                ON runs (denom);
            ''')
            self.__conn.execute('''
                CREATE UNIQUE INDEX IF NOT EXISTS accounts_addr
                ON accounts (address);
            ''')
            self.commit()

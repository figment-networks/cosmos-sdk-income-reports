from argparse import ArgumentParser, SUPPRESS
from os.path import join, dirname, abspath
from os import makedirs
from signal import signal, SIGINT
from sys import exit, argv

from csir import Api, Db
from csir.config import settings
from .reporter import Reporter
from .utils import account_discoverer, accounts_to_run, \
                   setup_runs, export_csvs


def main(args=None):
    if args is None: args = argv[1:]

    signal(SIGINT, lambda sig, frame: exit(0))

    default_db_path = abspath(join(dirname(__file__), '..', '..', 'db'))
    default_lcd_url = 'http://localhost:1317'
    default_scale = 6
    valid_networks = (
        'cosmos',
        'terra',
        'kava',
    )

    parser = ArgumentParser(prog='cosmos-sdk-income-reports', description='Cosmos-SDK Income Reports CLI')
    parser.add_argument('--network', required=True, choices=valid_networks, help=f"Type of network")
    parser.add_argument('--denom', required=True, help='Token denomination to calculate rewards for')
    parser.add_argument('--scale', default=default_scale, help=f"Power of 10 to scale the numbers in reports by (default {default_scale})")
    parser.add_argument('--db-path', default=default_db_path, help=f"Directory for sqlite3 db (default {default_db_path})")
    parser.add_argument('--csv-path', default=None, help='Path to export CSVs, omit to skip generating CSV reports')
    parser.add_argument('--lcd-url', default=default_lcd_url, help=f"Accessible light client daemon (default {default_lcd_url})")
    parser.add_argument('--account', dest='whitelist', metavar='ADDRESS', action='append', default=None, help='Accounts to exclusively run reports for')
    parser.add_argument('--skip', dest='blacklist', metavar='ADDRESS', action='append', default=[], help='Accounts to never run reports for')
    parser.add_argument('--start-at', choices=('genesis', 'latest-run'), default='latest-run', help='Consider every report window from genesis, or just from the latest completed run')
    parser.add_argument('--force-account-discovery', action='store_true', default=False, help='Account discovery is skipped on subsequent runs, force with this flag')
    parser.add_argument('--debug', action='store_true', default=False, help='Development mode (default false)')
    args = parser.parse_args()

    settings.configure({'debug': args.debug})

    api = Api(args.lcd_url)
    chain = api.get_chain()

    makedirs(args.db_path, exist_ok=True)
    db = Db(join(args.db_path, f"{chain}.db"), args.denom, args.scale)

    reporter = Reporter(db, api, args.network, args.denom)
    discoverer = account_discoverer(api, args.force_account_discovery, args.whitelist)

    latest_run = setup_runs(db, api, args.start_at, discoverer)
    accounts = list(filter(
        accounts_to_run(args.whitelist, args.blacklist),
        db.get_accounts()
    ))

    reporter.calculate_income_for(accounts, db.get_runs(after=latest_run))

    if args.csv_path:
        csv_path = join(args.csv_path, chain)
        makedirs(csv_path, exist_ok=True)
        export_csvs(db, csv_path, args.denom, accounts)


if __name__ == '__main__': main()

from datetime import timedelta, datetime
from re import sub
from os.path import join
from csv import DictWriter, QUOTE_MINIMAL


def report_days(start_time, end_time):
    start_time += timedelta(1)
    for n in range(int((end_time - start_time).days) + 1):
        next_time = start_time + timedelta(n)
        if next_time > datetime.now(): break
        yield start_time + timedelta(n)


def blocks_per_day(start_height, start_time, end_height, end_time):
    return int(timedelta(1) / ((end_time - start_time) / \
                               (end_height - start_height)))


def accounts_to_run(whitelist, blacklist):
    def f(account):
        # specifically excluded
        if account.address in blacklist:
            return False

        # whitelist of accounts, and this account is not on it
        if whitelist and account.address not in whitelist:
            return False

        return True

    return f


def account_discoverer(api, force=False, whitelist=None):
    def wrapped(height, existing_run):
        # ensure accounts on whitelist are in the database
        for address in (whitelist or []):
            yield address, 1

        # you can run for every account in existence or just for
        # specific accounts you want. if you specify specific accounts
        # there's no need to detect/discover all accounts on the chain
        if force or (existing_run is None and whitelist is None):
            print(f"\tRetrieve all validators & delegations at height {height}...", flush=True)
            for delegator_address in api.discover_delegators_at_height(height):
                yield delegator_address, height

    return wrapped


def setup_runs(db, api, runs_start_at, account_discoverer, debug=False):
    print("Determining runs & detecting accounts...", flush=True)

    head = api.get_block('latest')

    # decide when to start reporting
    latest_run = db.get_latest_run()
    if latest_run is None or runs_start_at == 'genesis':
        latest_run = None
        latest_block = api.get_block(1)
        latest_height = latest_block.height
        latest_time = latest_block.timestamp
    elif runs_start_at == 'latest-run':
        latest_block = api.get_block(latest_run.height)
        latest_height = latest_block.height
        latest_time = latest_run.target_timestamp

    blocks_rate = blocks_per_day(
        head.height, head.timestamp,
        latest_height, latest_time
    )

    for target_time in report_days(latest_time, head.timestamp):
        # find an existing report run so we don't have
        # to find an appropriate block for this target timestamp
        existing_run = db.run_for_target_time(target_time)

        if existing_run:
            if debug:
                print(f"\tDecided on block {existing_run.height} {target_time} from existing run log!", flush=True)
            report_height = existing_run.height
            report_time = existing_run.target_timestamp
        else:
            print(f"\tDetermine appropriate report block for {target_time}... ", end='', flush=True)
            if debug: print('', flush=True)

            # find appropriate block for this day
            guess_height = latest_height + blocks_rate

            report_block = api.get_block_closest_to(target_time, guess_height)
            report_height = report_block.height
            report_time = report_block.timestamp
            print(report_height, flush=True)

        for address, height in account_discoverer(report_height, existing_run):
            db.add_account(address, height)

        db.create_run(report_height, target_time)

        # calculate new blocks_per_day based on average for next round
        blocks_rate = blocks_per_day(
            latest_height, latest_time,
            report_height, report_time
        )
        latest_height = report_height
        latest_time = report_time

    return latest_run


def export_csvs(db, csv_path, denom, accounts):
    if csv_path is None: return

    print("\nGenerating CSV reports...", flush=True)

    fields = (
        'timestamp',
        'height',
        'pending_rewards',
        'pending_commission',
        'withdrawals',
        'income',
    )
    header = dict([(field, sub('_', ' ', field).title()) for field in fields])

    count = len(accounts)
    for index, account in enumerate(accounts):
        print(f"\r{account.address} ({str(index+1).rjust(len(str(count)))}/{count})", end='', flush=True)
        lines = db.get_full_report(account.address)

        report_path = join(csv_path, f"{account.address}-{denom}.csv")
        with open(report_path, 'w', newline='') as csvfile:
            writer = DictWriter(
                csvfile,
                fieldnames=fields,
                extrasaction='ignore',
                quoting=QUOTE_MINIMAL
            )
            writer.writerow(header)
            writer.writerows(map(lambda line: line._asdict(), lines))

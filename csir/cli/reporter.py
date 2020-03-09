from re import search
from itertools import chain
from datetime import datetime

from csir.utils import encode_bech32, decode_bech32


class Reporter():
    operator_prefix_by_network = {
        'cosmos': 'cosmosvaloper',
        'kava': 'kavavaloper',
        'terra': 'terravaloper',
    }

    def __init__(self, db, api, network, denom, debug=False):
        self.debug = debug

        self.db = db
        self.api = api
        self.network = network
        self.denom = denom

    def calculate_income_for(self, accounts, runs):
        for run in runs:
            try:
                start_time = datetime.now()
                print(f"\nReport run for {run.target_timestamp} (height {run.height})...", flush=True)

                # get the accounts we should run a report for
                accounts_for_run = self._filter_accounts_for_run(accounts, run)
                count = len(accounts_for_run)

                for index, account in enumerate(accounts_for_run):
                    status_line = f"\r{account.address} ({str(index+1).rjust(len(str(count)))}/{count})"
                    print(f"{status_line} ", end='', flush=True)

                    prev_run = self.db.get_previous_run(run)

                    def step_callback(x):
                        if self.debug: return
                        print(
                            f"{status_line} {'.' * x}{' ' * (len('DONE')-x)}",
                            end='', flush=True
                        )

                    report = self._generate_for(
                        account.address,
                        run,
                        prev_run,
                        step_callback=step_callback
                    )

                    self.db.insert_report(account.address, run, report)
                    print(f"{status_line} DONE", end='', flush=True)

                if self.debug:
                    cache_info = self.api.get_transactions.cache_info()
                    print(f"\nCache Info: {cache_info.hits} hits, {cache_info.currsize} entries.")
                self.db.run_ok(run)

                if count > 0:
                    print(f"\nRun complete in {datetime.now() - start_time}", flush=True)
                else:
                    print("Nothing to do...", flush=True)

            except:
                self.db.run_error(run)
                raise

    def _filter_accounts_for_run(self, accounts, run):
        def f(account):
            # this address was first seen after this report height
            if run and account.first_seen_height > run.height:
                return False

            # already have a report at this height
            if run and self.db.get_latest_report_height_for(account.address) >= run.height:
                return False

            return True

        return list(filter(f, accounts))

    def _generate_for(self, address, run, prev_run, step_callback=None):
        if not self.debug and step_callback: step_callback(1)
        pending = self._get_pending_rewards(address, run)
        if not self.debug and step_callback: step_callback(2)
        commission = self._get_pending_commission(address, run)
        if not self.debug and step_callback: step_callback(3)
        withdrawals = self._get_withdrawals(address, run, prev_run)
        if not self.debug and step_callback: step_callback(4)

        if self.debug:
            print(f"\t\tPRew: {pending}, PCom: {commission}, W: {withdrawals}", end='', flush=True)
        return {
            'pending_rewards': pending,
            'pending_commission': commission,
            'withdrawals': withdrawals
        }

    def _get_pending_rewards(self, address, run):
        reward_info = self.api.get_pending_rewards(address, run.height)
        reward_info = reward_info or [{ 'amount': 0, 'denom': self.denom }]

        relevant_reward = list(filter(
            lambda bal: bal['denom'] == self.denom,
            reward_info
        ))[0]

        if relevant_reward is None: return 0
        return int(relevant_reward['amount'])

    def _get_pending_commission(self, address, run):
        prefix = self.__class__.operator_prefix_by_network[self.network]
        operator = encode_bech32(prefix, decode_bech32(address)[1])
        validator_info = self.api.get_validator_distribution_info(operator, run.height)
        if validator_info is None or validator_info.get('val_commission') is None: return 0

        relevant_commission = list(filter(
            lambda bal: bal['denom'] == self.denom,
            validator_info['val_commission']
        ))[0]
        if relevant_commission is None: return 0

        return int(search(r'\d+', relevant_commission['amount']).group())

    def _get_withdrawals(self, address, run, prev_run):
        start_height = prev_run.height + 1 if prev_run else 1

        # TODO, when cosmos-sdk supports this, it's going to make
        #       processing accounts with a lot of transactions a LOT easier
        #       ** also, remove the cache on api.get_transactions!
        txs = self.api.get_transactions({
            'transfer.recipient': address,
            # 'tx.minheight': start_height,
            # 'tx.maxheight': run.height
        })

        txs = filter(
            lambda tx: tx.succeeded and \
                       tx.is_between(start_height, run.height) and \
                       tx.is_reward_disbursement_type(self.network),
            txs
        )

        return sum(map(lambda tx: tx.disbursement(address, self.denom), txs))

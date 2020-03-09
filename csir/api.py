from itertools import chain
from functools import lru_cache
from json import loads
from re import sub
from urllib.parse import urljoin
from datetime import datetime

from requests import get

from csir.domain import Block, Transaction
from csir.utils import with_retries


class Api():
    def __init__(self, lcd_base_url, debug=False):
        self.debug = debug
        self.lcd_base_url = sub('//$', '/', lcd_base_url+'/')

    def _get(self, path, params=None, retries=5, handle_error_key=True):
        def f():
            if self.debug:
                print(f"REQ: {urljoin(self.lcd_base_url, path)} {params}", end='', flush=True)
                pass

            start_time = datetime.now()
            url = urljoin(self.lcd_base_url, path)
            response = get(url, params, timeout=(3.1, 15))
            json = loads(response.content)

            if handle_error_key and 'error' in json:
                raise RuntimeError(f"ERROR making request: {url} with params {params} -> {json}")

            if self.debug:
                print(f" (took {datetime.now() - start_time})", flush=True)
                pass

            return json

        return with_retries(f, retries)

    def get_chain(self):
        return self._get('node_info')['node_info']['network']

    def get_block(self, height_or_latest='latest'):
        data = self._get(f"blocks/{height_or_latest}")
        return Block(data)

    def get_block_closest_to(self, target_time, start_height):
        offset = 0
        direction = None

        while True:
            current_block = self.get_block(start_height + offset)

            # went past head or something else went wrong?
            if current_block is None: raise

            if direction is None:
                direction = +1 if current_block.timestamp < target_time else -1

            if current_block.timestamp == target_time or \
               (current_block.timestamp > target_time and direction == +1) or \
               (current_block.timestamp < target_time and direction == -1):
                if self.debug:
                    print(f"\tFound block {current_block.height} after checking {offset} from starting point", flush=True)
                return current_block
            else:
                if self.debug:
                    print(f"\t{current_block.height}'s time of {current_block.timestamp} !~ {target_time}", flush=True)
                pass

            offset += direction

    def get_transactions(self, query):
        txs = []
        page = 1

        while True:
            query['page'] = page
            txsr = self._get('txs', query)
            txs.extend(txsr['txs'])
            if int(txsr['page_number']) >= int(txsr['page_total']): break
            page += 1

        return map(lambda tx: Transaction(tx), txs)

    def discover_delegators_at_height(self, height):
        validators_at_height = self.get_validators_at_height(height)
        for validator in sorted(validators_at_height):
            delegators_at_height = self.get_delegators_at_height(validator, height)
            for delegator in delegators_at_height: yield delegator

    def get_validators_at_height(self, height):
        bonded = self._get('staking/validators', {'status': 'bonded', 'height': height})
        unbonding = self._get('staking/validators', {'status': 'unbonding', 'height': height})
        unbonded = self._get('staking/validators', {'status': 'unbonded', 'height': height})

        flattened = chain(*map(lambda r: r['result'], [bonded, unbonding, unbonded]))
        return set(map(lambda v: v['operator_address'], flattened))

    def get_delegators_at_height(self, validator, height):
        bonded = self._get(f"staking/validators/{validator}/delegations", {'height': height})
        unbonding = self._get(f"staking/validators/{validator}/unbonding_delegations", {'height': height})
        flattened = chain(*map(lambda r: r['result'] or [], [bonded, unbonding]))
        return set(map(lambda d: d['delegator_address'], flattened))

    def get_pending_rewards(self, address, height):
        r = self._get(f"distribution/delegators/{address}/rewards", {'height': height}, handle_error_key=False)
        if 'error' in r: return None

        # this endpoint needs some normalisation
        cleaned = list(map(
            lambda r: {'denom': r['denom'], 'amount': int(float(r['amount']))},
            r['result']['total'] or []
        ))

        return cleaned if len(cleaned) > 0 else None

    def get_validator_distribution_info(self, operator_address, height):
        r = self._get(f"distribution/validators/{operator_address}", {'height': height}, handle_error_key=False)
        if 'error' in r: return None
        return r['result']

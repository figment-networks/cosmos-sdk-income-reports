from itertools import chain
from json import loads
from re import sub
from urllib.parse import urljoin
from datetime import datetime

from requests import get

from csir.domain import Block, Transaction
from csir.config import settings


class Api():
    def __init__(self, lcd_base_url):
        self.lcd_base_url = sub('//$', '/', lcd_base_url+'/')

    def _get(self, path, params=None):
        if settings.debug:
            print(f"REQ: {urljoin(self.lcd_base_url, path)} {params}", end='')
            pass

        start_time = datetime.now()
        response = get(urljoin(self.lcd_base_url, path), params)
        json = loads(response.content)

        if settings.debug:
            print(f" (took {datetime.now() - start_time})")
            pass

        return json

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
                if settings.debug:
                    print(f"\tFound block {current_block.height} after checking {offset} from starting point")
                return current_block
            else:
                # print(f"\t{current_block.height}'s time of {current_block.timestamp} is not close enough")
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
        r = self._get(f"distribution/delegators/{address}/rewards", {'height': height})

        # this endpoint needs some normalisation
        cleaned = list(map(
            lambda r: {'denom': r['denom'], 'amount': int(float(r['amount']))},
            r['result']['total'] or []
        ))

        return cleaned if len(cleaned) > 0 else None

    def get_validator_distribution_info(self, operator_address, height):
        r = self._get(f"distribution/validators/{operator_address}", {'height': height})
        if 'error' in r: return None
        return r['result']

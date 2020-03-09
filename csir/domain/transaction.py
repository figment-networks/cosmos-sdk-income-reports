from itertools import chain
from re import search


class Transaction():
    msg_types_by_network = {
        'cosmos': frozenset((
            'cosmos-sdk/MsgDelegate',
            'cosmos-sdk/MsgBeginRedelegate',
            'cosmos-sdk/MsgUndelegate',
            'cosmos-sdk/MsgWithdrawDelegationReward',
            'cosmos-sdk/MsgWithdrawValidatorCommission',
            'cosmos-sdk/CommunityPoolSpendProposal',
        )),
        'kava': frozenset((
            'cosmos-sdk/MsgDelegate',
            'cosmos-sdk/MsgBeginRedelegate',
            'cosmos-sdk/MsgUndelegate',
            'cosmos-sdk/MsgWithdrawDelegationReward',
            'cosmos-sdk/MsgWithdrawValidatorCommission',
            'cosmos-sdk/CommunityPoolSpendProposal',
        )),
        'terra': frozenset((
            'staking/MsgDelegate',
            'staking/MsgBeginRedelegate',
            'staking/MsgUndelegate',
            'distribution/MsgWithdrawDelegationReward',
            'distribution/MsgWithdrawValidatorCommission',
        )),
    }

    def __init__(self, data):
        self.__data = data
        self.height = int(data['height'])
        self.txhash = data['txhash']
        self.events = data['events']
        self.succeeded = data['logs'][0]['success']
        self.msg_types = set(map(lambda msg: msg['type'], data['tx']['value']['msg']))

    def is_between(self, start_height, end_height):
        return self.height >= start_height and \
               self.height <= end_height

    def is_reward_disbursement_type(self, network):
        network_types = self.__class__.msg_types_by_network.get(network)
        return len(self.msg_types & network_types) > 0

    def disbursement(self, to_address, denom):
        events = chain(*map(
            lambda ev: ev['attributes'],
            filter(lambda ev: ev['type'] == 'transfer', self.events)
        ))

        total = 0

        latest_recipient = None
        for event in events:
            if event['key'] == 'recipient':
                latest_recipient = event['value']
            elif event['key'] == 'amount' and \
                 latest_recipient == to_address and \
                 event['value'].endswith(denom):
                total += int(search(r'\d+', event['value']).group())

        return total

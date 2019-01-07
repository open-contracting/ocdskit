import hashlib
import json
import logging
from collections import OrderedDict
from copy import deepcopy

from ocdskit.cli.commands.base import BaseCommand
from ocdskit.exceptions import CommandError

logger = logging.getLogger('ocdskit')

'''
Script to transform JSON releases in OCDS schema v1.0 to v1.1
'''


def generate_party(parties, org, role=None):
    """
    Update the parties array, returning an updated organisation
    reference block to use.
    """
    identifier = ''
    if role is None:
        role = []
    if 'identifier' in org and 'id' in org['identifier']:
        org_id = org['identifier']['id']
        if 'scheme' in org['identifier'] and 2 < len(org['identifier']['scheme']) < 20:
            scheme = org['identifier']['scheme']
            identifier = scheme + '-' + org_id
    else:
        if 'id' in org:
            identifier = org['id']
        else:
            identifier = hashlib.md5(json.dumps(org).encode('utf8')).hexdigest()

    if parties.get(identifier, False):
        name = parties.get(identifier).get('name', '')
        contact = parties.get(identifier).get('contactPoint', '')
        if not (name == org.get('name', '')) \
                or not (contact == org.get('contactPoint', '')):
            n = json.dumps(org.get('name', '')).encode('utf8')
            c = json.dumps(org.get('contactPoint', '')).encode('utf8')
            identifier += '-' + hashlib.md5(n + c).hexdigest()

    roles = parties.get(identifier, {}).get('roles', [])
    org['roles'] = list(set(roles + role))
    org['id'] = identifier
    parties[identifier] = deepcopy(org)
    return {'id': identifier, 'name': org.get('name', '')}


def upgrade_parties(release):
    parties = {}

    if 'buyer' in release:
        release['buyer'] = generate_party(parties, release['buyer'], ['buyer'])

    if 'tender' in release:
        if 'procuringEntity' in release['tender']:
            release['tender']['procuringEntity'] = \
                generate_party(parties, release['tender']['procuringEntity'],
                               ['procuringEntity'])
        if 'tenderers' in release['tender']:
            for num, tenderer in enumerate(release['tender']['tenderers']):
                release['tender']['tenderers'][num] = \
                    generate_party(parties, tenderer, ['tenderer'])

    if 'awards' in release:
        for anum, award in enumerate(release['awards']):
            if 'suppliers' in release['awards'][anum]:
                suppliers = release['awards'][anum]['suppliers']
                for snum, supplier in enumerate(suppliers):
                    release['awards'][anum]['suppliers'][snum] = \
                        generate_party(parties, supplier, ['supplier'])

    if 'contracts' in release:
        for anum, award in enumerate(release['contracts']):
            if 'suppliers' in release['contracts'][anum]:
                suppliers = release['contracts'][anum]['suppliers']
                for snum, supplier in enumerate(suppliers):
                    release['contracts'][anum]['suppliers'][snum] = \
                        generate_party(parties, supplier, ['supplier'])
            if 'implementation' in release['contracts'][anum] and 'transactions' in \
                    release['contracts'][anum]['implementation']:
                transactions = release['contracts'][anum]['implementation']['transactions']
                for tnum, transaction in enumerate(transactions):
                    if 'providerOrganization' in transaction:
                        release['contracts'][anum]['implementation']['transactions'][tnum]['payer'] = \
                            generate_party(parties, transaction['providerOrganization'], ['payer'])
                        del (transaction['providerOrganization'])
                    if 'receiverOrganization' in transaction:
                        release['contracts'][anum]['implementation']['transactions'][tnum]['payee'] = \
                            generate_party(parties, transaction['receiverOrganization'], ['payee'])
                        del (transaction['receiverOrganization'])

    release['parties'] = []
    for key in parties:
        release['parties'].append(parties[key])
    if not release['parties']:
        del release['parties']

    return release


def upgrade_transactions(release):

    for contract in release['contracts']:
        if 'implementation' in contract and 'transactions' in contract['implementation']:
            for transaction in contract['implementation']['transactions']:
                transaction['value'] = transaction['amount']
                del (transaction['amount'])
    return release


def upgrade_amendments(release):

    if 'tender' in release:
        release['tender'] = upgrade_amendment(release['tender'])
    if 'awards' in release:
        for award in release['awards']:
            upgrade_amendment(award)
    if 'contracts' in release:
        for contract in release['contracts']:
            upgrade_amendment(contract)

    return release


def upgrade_amendment(parent):
    try:
        amendment = {'date': parent['amendment']['date'], 'rationale': parent['amendment']['rationale']}
        parent['amendments'] = []
        parent['amendments'].append(amendment)
    except KeyError:
        pass
    return parent


def remove_empty_arrays(data, keys=None):
    """
    Drill doesn't cope well with empty arrays. Remove them.
    """
    if not keys:
        keys = data.keys()
    keys_to_remove = []
    for key in keys:
        if isinstance(data[key], dict):
            remove_empty_arrays(data[key])
        else:
            if isinstance(data[key], list) and len(data[key]) == 0:
                keys_to_remove.append(key)
    for key in keys_to_remove:
        del data[key]
    return data


def upgrade(release):
    release = OrderedDict(release)
    release = upgrade_amendments(release)
    release = upgrade_parties(release)
    if 'contracts' in release:
        release = upgrade_transactions(release)
    for section in ['parties', 'initiationType', 'tag', 'language', 'date', 'id', 'ocid']:
        if section in release:
            release.move_to_end(section, last=False)
    return release


def convert_10_11(data):
        data = remove_empty_arrays(data)
        data = OrderedDict(data)
        data.update({'version': '1.1'})
        if 'records' in data:
            # Handle record packages.
            for record in data['records']:
                if 'compiledRelease' in record:
                    record['compiledRelease'] = \
                        upgrade(record['compiledRelease'])
        else:
            # Handle release packages.
            if 'releases' in data:
                releases = []
                for release in data['releases']:
                    releases.append(upgrade(release))
                data['releases'] = releases
            else:
                # Handle releases.
                data = upgrade(data)
        return data


class Command(BaseCommand):
    name = 'upgrade'
    help = 'transform a version of OCDS json into a another version of it'

    def add_arguments(self):
        self.add_argument('--version', help='the version from:to',
                          default='1.0:1.1')

    def handle(self):

        version_to, version_from = self.args.version.split(':')

        if version_to != '1.0' or version_from != '1.1':
            raise CommandError('Currently only upgrade from version 1.0 to 1.1 is supported')

        for line in self.buffer():
            data = json.loads(line)
            self.print(convert_10_11(data))

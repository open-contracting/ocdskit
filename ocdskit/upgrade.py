import json
import logging
from collections import OrderedDict
from copy import deepcopy
from hashlib import md5

from ocdskit.util import get_ocds_minor_version, is_package, is_record, is_record_package, is_release_package

logger = logging.getLogger('ocdskit')

# See https://standard.open-contracting.org/1.0/en/schema/reference/#identifier
organization_identification_1_0 = (
    (None, ('name',)),
    ('identifier', ('scheme', 'id', 'legalName', 'uri')),
    ('address', ('streetAddress', 'locality', 'region', 'postalCode', 'countryName')),
    ('contactPoint', ('name', 'email', 'telephone', 'faxNumber', 'url')),
)


def _move_to_top(data, fields):
    for field in reversed(fields):
        if field in data:
            data.move_to_end(field, last=False)


def _in(obj, field):
    return field in obj and obj[field] is not None


def upgrade_10_10(data):
    """
    Upgrades a record package, release package, record or release from 1.0 to 1.0 (no-op).
    """
    return data


def upgrade_11_11(data):
    """
    Upgrades a record package, release package, record or release from 1.1 to 1.1 (no-op).
    """
    return data


def upgrade_10_11(data):
    """
    Upgrades a record package, release package, record or release from 1.0 to 1.1.

    Retains the deprecated Amendment.changes, Budget.source and Milestone.documents fields.

    ``data`` must be an ``OrderedDict``. If you have only the parsed JSON, re-parse it with:

    ``upgrade_10_11(json.loads(json.dumps(data), object_pairs_hook=OrderedDict))``
    """
    version = get_ocds_minor_version(data)
    if version != '1.0':
        return data

    if is_package(data):
        data['version'] = '1.1'
        _move_to_top(data, ('uri', 'version'))

    if is_record_package(data):
        for record in data['records']:
            upgrade_record_10_11(record)
    elif is_release_package(data):
        for release in data['releases']:
            upgrade_release_10_11(release)
    elif is_record(data):
        upgrade_record_10_11(data)
    else:  # release
        upgrade_release_10_11(data)

    return data


def upgrade_record_10_11(record):
    """
    Upgrades a record from 1.0 to 1.1.
    """
    if 'releases' in record:
        for release in record['releases']:
            upgrade_release_10_11(release)
    if 'compiledRelease' in record:
        upgrade_release_10_11(record['compiledRelease'])


def upgrade_release_10_11(release):
    """
    Applies upgrades for organization handling, amendment handling and transactions terminology.
    """
    upgrade_parties_10_to_11(release)
    upgrade_amendments_10_11(release)
    upgrade_transactions_10_11(release)


def upgrade_parties_10_to_11(release):
    """
    Converts organizations to organization references and fills in the ``parties`` array.
    """
    parties = _get_parties(release)

    if _in(release, 'buyer'):
        buyer = release['buyer']
        release['buyer'] = _add_party(parties, buyer, 'buyer')

    if _in(release, 'tender'):
        if _in(release['tender'], 'procuringEntity'):
            procuring_entity = release['tender']['procuringEntity']
            release['tender']['procuringEntity'] = _add_party(parties, procuring_entity, 'procuringEntity')
        if _in(release['tender'], 'tenderers'):
            for i, tenderer in enumerate(release['tender']['tenderers']):
                release['tender']['tenderers'][i] = _add_party(parties, tenderer, 'tenderer')

    if _in(release, 'awards'):
        for award in release['awards']:
            if _in(award, 'suppliers'):
                for i, supplier in enumerate(award['suppliers']):
                    award['suppliers'][i] = _add_party(parties, supplier, 'supplier')

    if parties:
        if 'parties' not in release:
            release['parties'] = []
            _move_to_top(release, ('ocid', 'id', 'date', 'tag', 'initiationType', 'parties'))

        for party in parties.values():
            if party not in release['parties']:
                release['parties'].append(party)


def _get_parties(release):
    parties = {}

    if 'parties' in release:
        for party in release['parties']:
            if 'id' in party:
                _id = party['id']
            else:
                _id = _create_party_id(party)
            parties[_id] = party

    return parties


def _add_party(parties, party, role):
    """
    Adds an ``id`` to the party, adds the party to the ``parties`` array, sets the party's role, and returns an
    OrganizationReference. Warns if there is any data loss from differences in non-identifying fields.
    """
    party = deepcopy(party)

    if 'id' not in party:
        party['id'] = _create_party_id(party)
        _move_to_top(party, ('id'))

    _id = party['id']

    if _id not in parties:
        parties[_id] = party
    else:
        # Warn about data loss.
        other = deepcopy(parties[_id])
        roles = other.pop('roles')
        if dict(party) != dict(other):
            logger.warning('party differs in "{}" role than in "{}" roles:\n{}\n{}'.format(
                role, ', '.join(roles), json.dumps(party), json.dumps(other)))

    if 'roles' not in parties[_id]:
        parties[_id]['roles'] = []
        _move_to_top(parties[_id], ('id', 'roles'))

    if role not in parties[_id]['roles']:
        # Update the `roles` of the party in the `parties` array.
        parties[_id]['roles'].append(role)

    # Create the OrganizationReference.
    organization_reference = {'id': _id}

    if 'name' in party:
        organization_reference['name'] = party['name']

    return organization_reference


def _create_party_id(party):
    parts = []
    for parent, fields in organization_identification_1_0:
        if not parent:
            for field in fields:
                parts.append(_get_bytes(party, field))
        elif parent in party:
            for field in fields:
                parts.append(_get_bytes(party[parent], field))

    return md5(b'-'.join(parts)).hexdigest()


def _get_bytes(obj, field):
    # Handle null and integers.
    return str(obj.get(field) or '').encode('utf-8')


def upgrade_amendments_10_11(release):
    """
    Renames ``amendment`` to ``amendments`` under ``tender``, ``awards`` and ``contracts``. If ``amendments`` already
    exists, it appends the ``amendment`` value to the ``amendments`` array, unless it already contains it.
    """
    if _in(release, 'tender'):
        _upgrade_amendment_10_11(release['tender'])
    for field in ('awards', 'contracts'):
        if _in(release, field):
            for block in release[field]:
                _upgrade_amendment_10_11(block)


def _upgrade_amendment_10_11(block):
    if 'amendment' in block:
        block.setdefault('amendments', [])
        if block['amendment'] not in block['amendments']:
            block['amendments'].append(block['amendment'])
        del block['amendment']


def upgrade_transactions_10_11(release):
    """
    Renames ``providerOrganization`` to ``payer``, ``receiverOrganization`` to ``payee``, and ``amount`` to ``value``
    under ``contracts.implementation.transactions``, unless they already exist.

    Converts ``providerOrganization`` and ``receiverOrganization`` from an Identifier to an OrganizationReference and
    fills in the ``parties`` array.
    """
    parties = _get_parties(release)

    if _in(release, 'contracts'):
        for contract in release['contracts']:
            if _in(contract, 'implementation') and _in(contract['implementation'], 'transactions'):
                for transaction in contract['implementation']['transactions']:
                    if 'value' not in transaction:
                        transaction['value'] = transaction['amount']
                        del transaction['amount']

                    for old, new in (('providerOrganization', 'payer'), ('receiverOrganization', 'payee')):
                        if old in transaction and new not in transaction:
                            party = OrderedDict([('identifier', transaction[old])])

                            if 'legalName' in transaction[old]:
                                party['name'] = transaction[old]['legalName']

                            transaction[new] = _add_party(parties, party, new)
                            del transaction[old]

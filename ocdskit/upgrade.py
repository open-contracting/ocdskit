import json
import logging
from collections import OrderedDict
from copy import deepcopy
from hashlib import md5

from ocdskit.util import get_ocds_minor_version, is_package, is_record_package, is_release_package

logger = logging.getLogger('ocdskit')

# See http://standard.open-contracting.org/1.0/en/schema/reference/#identifier
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


def upgrade_10_10(data):
    pass


def upgrade_11_11(data):
    pass


def upgrade_10_11(data):
    """
    Upgrades a record package, release package or release from 1.0 to 1.1.

    Retains the deprecated Amendment.changes, Budget.source and Milestone.documents fields.
    """
    version = get_ocds_minor_version(data)
    if version != '1.0':
        return

    if is_package(data):
        data['version'] = '1.1'
        _move_to_top(data, ('uri', 'version'))

    if is_record_package(data):
        for record in data['records']:
            if 'releases' in record:
                for release in record['releases']:
                    upgrade_release_10_11(release)
            if 'compiledRelease' in record:
                upgrade_release_10_11(record['compiledRelease'])
    elif is_release_package(data):
        for release in data['releases']:
            upgrade_release_10_11(release)
    else:  # release
        upgrade_release_10_11(data)


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

    if 'buyer' in release:
        release['buyer'] = _add_party(parties, release['buyer'], 'buyer')

    if 'tender' in release:
        if 'procuringEntity' in release['tender']:
            release['tender']['procuringEntity'] = _add_party(parties, release['tender']['procuringEntity'], 'procuringEntity')  # noqa: E501
        if 'tenderers' in release['tender']:
            for i, tenderer in enumerate(release['tender']['tenderers']):
                release['tender']['tenderers'][i] = _add_party(parties, tenderer, 'tenderer')

    if 'awards' in release:
        for award in release['awards']:
            if 'suppliers' in award:
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
    parties = OrderedDict()

    if 'parties' in release:
        for party in release['parties']:
            parties[party['id']] = party

    return parties


def _add_party(parties, party, role):
    """
    Adds an ``id`` to the party, adds the party to the ``parties`` array, sets the party's role, and returns an
    OrganizationReference. Warns if there is any data loss from differences in non-identifying fields.
    """
    party = deepcopy(party)

    if 'id' not in party:
        parts = []
        for parent, fields in organization_identification_1_0:
            if not parent:
                for field in fields:
                    parts.append(_get_bytes(party, field))
            elif parent in party:
                for field in fields:
                    parts.append(_get_bytes(party[parent], field))

        party['id'] = md5(b'-'.join(parts)).hexdigest()
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
    organization_reference = OrderedDict([
        ('id', _id),
    ])
    if 'name' in party:
        organization_reference['name'] = party['name']

    return organization_reference


def _get_bytes(obj, field):
    # Handle null and integers.
    return bytes(str(obj.get(field) or ''), 'utf-8')


def upgrade_amendments_10_11(release):
    """
    Renames ``amendment`` to ``amendments`` under ``tender``, ``awards`` and ``contracts``. If ``amendments`` already
    exists, it appends the ``amendment`` value to the ``amendments`` array, unless it already contains it.
    """
    if 'tender' in release:
        _upgrade_amendment_10_11(release['tender'])
    for field in ('awards', 'contracts'):
        if field in release:
            for block in release[field]:
                _upgrade_amendment_10_11(block)


def _upgrade_amendment_10_11(block):
    if 'amendment' in block:
        if 'amendments' not in block:
            block['amendments'] = []
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

    if 'contracts' in release:
        for contract in release['contracts']:
            if 'implementation' in contract and 'transactions' in contract['implementation']:
                for transaction in contract['implementation']['transactions']:
                    if 'value' not in transaction:
                        transaction['value'] = transaction['amount']
                        del transaction['amount']

                    for old, new in (('providerOrganization', 'payer'), ('receiverOrganization', 'payee')):
                        if old in transaction and new not in transaction:
                            party = OrderedDict([
                                ('identifier', transaction[old]),
                            ])
                            if 'legalName' in transaction[old]:
                                party['name'] = transaction[old]['legalName']

                            transaction[new] = _add_party(parties, party, new)
                            del transaction[old]

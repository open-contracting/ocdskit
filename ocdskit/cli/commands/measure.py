"""
Assumptions:
- All awards/suppliers/identifier/id appear in tender/tenderers/identifier/id
"""

import json

from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta
from statistics import median

import ocdsmerge
import pytz
from dateutil import parser

from .base import BaseCommand


class Command(BaseCommand):
    name = 'measure'
    help = 'measure indicators in OCDS data'

    def add_arguments(self):
        self.add_argument('--currency', help='the expected currency')

    def handle(self):
        data = json.load(self.buffer())

        compiled_releases_by_buyer = defaultdict(list)
        min_date_by_buyer = {}

        # Global indicators.

        b2_procurement_method_count = defaultdict(int)
        b3_procurement_method_amount = defaultdict(int)
        b9_number_of_tenderers = OrderedDict([
            ('by `tender/numberOfTenderers`', []),
            ('by unique `tender/tenderers/identifier/id`', []),
        ])

        b3_no_data = []
        b9_no_data = 0

        for release_package in data:
            releases = release_package['releases']
            compiled_release = ocdsmerge.merge(releases)

            try:
                # Read the data.

                ocid = compiled_release['ocid']
                # We use buyer names as keys, because buyer IDs are reused. We can make this optional.
                buyer = str(compiled_release['buyer']['name'])
                tender = compiled_release['tender']
                procurementMethod = tender['procurementMethod']
                numberOfTenderers = tender['numberOfTenderers']
                tenderers = tender['tenderers']
                amount = tender['value']['amount']
                currency = tender['value']['currency']

                # Prepare data for per-buyer indicators.

                compiled_releases_by_buyer[buyer].append(compiled_release)
                compiled_release['date'] = min(release['date'] for release in releases)
                if buyer not in min_date_by_buyer or compiled_release['date'] < min_date_by_buyer[buyer]:
                    min_date_by_buyer[buyer] = compiled_release['date']

                # Calculate global indicators.

                b2_procurement_method_count[str(procurementMethod)] += 1  # if null

                if procurementMethod and amount:
                    if self.args.currency:
                        # Ensure we sum a single currency.
                        assert currency == self.args.currency, '{} uses {}'.format(ocid, currency)
                    b3_procurement_method_amount[procurementMethod] += amount
                else:
                    b3_no_data.append(amount)

                if numberOfTenderers or tenderers:
                    # Perform basic data validation.
                    assert numberOfTenderers == len(tenderers), ocid
                    b9_number_of_tenderers['by `tender/numberOfTenderers`'].append(numberOfTenderers)
                    # There may be double counting of tenderers.
                    value = len(set([tenderer['identifier']['id'] for tenderer in tenderers]))
                    b9_number_of_tenderers['by unique `tender/tenderers/identifier/id`'].append(value)
                else:
                    b9_no_data += 1
            except KeyError as e:
                raise Exception('{}: {}'.format(e, ocid))

        # Per-buyer indicators.

        b0_compiled_releases = {}
        b1_tenderers = {}
        b4_suppliers_count = {}
        b5_suppliers_amount = {}
        b5_other_currencies = defaultdict(int)
        b8_tenderers_to_suppliers = {}
        b8_tenderers_never_suppliers = {}

        today = datetime.now(pytz.utc)
        threshold = today - timedelta(days=180)  # 6 months

        for buyer, compiled_releases in compiled_releases_by_buyer.items():
            min_date = parser.parse(min_date_by_buyer[buyer])
            if len(compiled_releases) >= 10 and min_date <= threshold:
                # Determine the before/after periods.

                if min_date + timedelta(days=730) <= today:  # 2 years
                    pivot = today - timedelta(days=365)  # 1 year
                else:
                    pivot = today - (today - min_date) / 2

                b0_compiled_releases_all = 0
                b0_compiled_releases_new = 0
                b1_tenderers_before = set()
                b1_tenderers_after = set()
                b4_suppliers_count_before = set()
                b4_suppliers_count_after = set()
                b8_tenderers_count = 0
                b8_suppliers_count = 0

                # Calculate per-buyer indicators.

                for compiled_release in compiled_releases:
                    tender = compiled_release['tender']
                    awards = compiled_release['awards']
                    tenderers = tender['tenderers']

                    b1 = [tenderer['identifier']['id'] for tenderer in tenderers]
                    b4 = [supplier['identifier']['id'] for award in awards for supplier in award['suppliers']]
                    b8_tenderers_count += len(b1)
                    b8_suppliers_count += len(b4)

                    b0_compiled_releases_all += 1
                    if parser.parse(compiled_release['date']) < pivot:
                        b1_tenderers_before.update(b1)
                        b4_suppliers_count_before.update(b4)
                    else:
                        b1_tenderers_after.update(b1)
                        b4_suppliers_count_after.update(b4)
                        b0_compiled_releases_new += 1

                b0_compiled_releases[buyer] = b0_compiled_releases_new / b0_compiled_releases_all

                b1_tenderers_all = b1_tenderers_before | b1_tenderers_after
                if b1_tenderers_all:
                    b1_tenderers_new = b1_tenderers_after - b1_tenderers_before
                    b1_tenderers[buyer] = len(b1_tenderers_new) / len(b1_tenderers_all)

                b4_suppliers_count_all = b4_suppliers_count_before | b4_suppliers_count_after
                if b4_suppliers_count_all:
                    b4_suppliers_count_new = b4_suppliers_count_after - b4_suppliers_count_before
                    b4_suppliers_count[buyer] = len(b4_suppliers_count_new) / len(b4_suppliers_count_all)

                    b5_suppliers_amount_all = 0
                    b5_suppliers_amount_new = 0

                    for compiled_release in compiled_releases:
                        ocid = compiled_release['ocid']
                        awards = compiled_release['awards']

                        for award in awards:
                            amount = award['value']['amount']
                            currency = award['value']['currency']

                            # Ensure we sum a single currency.
                            if not self.args.currency or currency == self.args.currency:
                                b5_suppliers_amount_all += amount
                                if any(supplier['identifier']['id'] in b4_suppliers_count_new for supplier in award['suppliers']):  # noqa
                                    b5_suppliers_amount_new += amount
                            else:
                                b5_other_currencies[str(currency)] += amount  # if null

                    b5_suppliers_amount[buyer] = b5_suppliers_amount_new / b5_suppliers_amount_all

                if b8_tenderers_count:
                    b8_tenderers_to_suppliers[buyer] = b8_tenderers_count / b8_suppliers_count

                if b1_tenderers_all:
                    b8_tenderers_never_suppliers[buyer] = (len(b1_tenderers_all - b4_suppliers_count_all) /
                                                           len(b1_tenderers_all))

        # Report indicators.

        def report_by_label(message, data, fmt='{1:-3.0%} {0}'):
            fmt = '  ' + fmt
            print(message)
            print(repr(data))
            for label, value in sorted(data.items()):
                print(fmt.format(label, value))
            print()

        def report_percentage_of_total(message, data, indicator, fmt='{}'):
            print(message)

            total = sum(data.values())
            data_format = '  {}: {:.0%} (' + fmt + ')'
            for label, count in sorted(data.items()):
                print(data_format.format(label, count / total, count))
            print()

        report_by_label('B0. % of new compiled releases:', b0_compiled_releases)
        report_by_label('B1. % of new bidders to all bidders:', b1_tenderers)
        report_percentage_of_total('B2. % of contracts assigned under each of the awarding procedures:',
                                   b2_procurement_method_count, 'B2')
        report_percentage_of_total('B3. % of total tender value assigned under each of the awarding procedures:',
                                   b3_procurement_method_amount, 'B3', fmt='${:,.2f}')
        print('B3. No data: {} (${:,.2f})'.format(len(b3_no_data), sum(b3_no_data)))
        report_by_label('B4. % of new winners to all winners:', b4_suppliers_count)
        report_by_label('B5. % of total contracting value awarded to new winners:', b5_suppliers_amount)
        report_by_label('B5.1. Excluded currencies:', b5_other_currencies, fmt='{0}: ${1:,.2f}')
        report_by_label('B8. Average number of bids to win:', b8_tenderers_to_suppliers, fmt='{1:,.2f} {0}')
        report_by_label('B8.1. % of bidders who never win:', b8_tenderers_never_suppliers)

        print('B9. Median number of bidders per tender:')
        for label, values in b9_number_of_tenderers.items():
            print('  {}: {}'.format(label, median(values)))
        print('B9. No data: {}\n'.format(b9_no_data))

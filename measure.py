#!/usr/bin/env python

import argparse
import json
import os.path
from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta
from statistics import median

import requests
import ocdsmerge
from dateutil import parser

# Parse the arguments.

parser = argparse.ArgumentParser(description='Measure indicators in OCDS data.')
parser.add_argument('url_or_path', help='a URL or a path to a file')
parser.add_argument('--encoding', help='the file encoding')
parser.add_argument('--currency', help='the expected currency')

args = parser.parse_args()

if os.path.isfile(args.url_or_path):
    with open(args.url_or_path, 'r', encoding=args.encoding) as f:
        release_packages = json.loads(f.read())
else:
    release_packages = requests.get(args.url_or_path).json()

# Initialize the variables.

releases_by_buyer = defaultdict(list)
min_date_by_buyer = {}

b2_procurement_method_count = defaultdict(int)
b3_procurement_method_amount = defaultdict(int)
b9_number_of_tenderers = OrderedDict([
    ('by `tender/numberOfTenderers`', []),
    ('by unique `tender/tenderers/identifier/id`', []),
    ('by unique `tender/tenderers/name`', []),
])

b2_no_data = 0
b3_no_data = []
b9_no_data = 0

# Calculate global indicators.

for release_package in release_packages:
    releases = release_package['releases']
    release = ocdsmerge.merge(releases)

    try:
        ocid = release['ocid']
        buyer = release['buyer']['name']
        tender = release['tender']
        procurementMethod = tender['procurementMethod']
        numberOfTenderers = tender['numberOfTenderers']
        tenderers = tender['tenderers']
        amount = tender['value']['amount']
        currency = tender['value']['currency']

        # We use buyer names as keys, because buyer IDs are reused. We can make this behavior optional.
        releases_by_buyer[buyer].append(release)
        min_date = min(release['date'] for release in releases)
        if buyer not in min_date_by_buyer or min_date < min_date_by_buyer[buyer]:
            min_date_by_buyer[buyer] = min_date

        if procurementMethod:
            b2_procurement_method_count[procurementMethod] += 1
        else:
            b2_no_data += 1

        if procurementMethod and amount:
            if args.currency:
                # Ensure we sum a single currency.
                assert currency == args.currency, ocid
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
            value = len(set([tenderer['name'] for tenderer in tenderers]))
            b9_number_of_tenderers['by unique `tender/tenderers/name`'].append(value)
        else:
            b9_no_data += 1
    except KeyError as e:
        raise Exception('{}: {}'.format(e, ocid))

# Calculate per-buyer indicators.

today = datetime.today()
threshold = today - timedelta(days=180)  # 6 months
for buyer, releases in releases_by_buyer.items():
    min_date = parser.parse(min_date_by_buyer[buyer])
    if len(releases) >= 10 and min_date <= threshold:
        if min_date + timedelta(days=730) <= today:  # 2 years
            pivot = today - timedelta(days=365)  # 1 year
        else:
            pivot = today - (today - min_date) / 2

        before = set()
        after = set()

        for release in releases:
            tender = release['tender']
            tenderers = tender['tenderers']

            # We use tenderer names as keys, because tenderer IDs are reused. We can make this behavior optional.
            values = [tenderer['name'] for tenderer in tenderers]
            if parser.parse(release['date']) < pivot:
                before.update(values)
            else:
                after.update(values)

            # B1, B4, B5, B6, B7, B8
            # TODO

            pass

# Report indicators.

total = sum(b2_procurement_method_count.values())

print('B2. % of contracts assigned under each of the awarding procedures:')
for label, count in b2_procurement_method_count.items():
    print('  {}: {:.0%} ({})'.format(label, count / total, count))
print('B2. No data: {}\n'.format(b2_no_data))

total = sum(b3_procurement_method_amount.values())

print('B3. % of total tender value assigned under each of the awarding procedures:')
for label, count in b3_procurement_method_amount.items():
    print('  {}: {:.0%} (${:,.2f})'.format(label, count / total, count))
print('B3. No data: {} (${:,.2f})\n'.format(len(b3_no_data), sum(b3_no_data)))

print('B9. Median number of bidders per tender:')
for label, values in b9_number_of_tenderers.items():
    print('  {}: {}'.format(label, median(values)))
print('B9. No data: {}\n'.format(b9_no_data))

#!/usr/bin/env python
"""
FOO
"""
from __future__ import annotations

import argparse
import json
import re
import urllib
from typing import List, Tuple
from urllib.parse import urljoin
from urllib.request import urlopen

THIS_SCRIPT_VERSION = (1, 0, 0)
THIS_SCRIPT_VERSION_STR = '.'.join([str(d) for d in THIS_SCRIPT_VERSION])
URL = 'https://curlbus.app/'
BUS_NUM_AND_ETA_REGEX = re.compile(r'│(?P<bus_number>\d+).*│(?P<eta>[\d m,]+)')


# noinspection PyShadowingNames
def main(args):

    def normalize_output(station_info: List[Tuple[str, str]], output_format: str) -> str:
        """
        Foo what is alfred format?
        :param output_format:
        :param station_info:
        :return:
        """
        etas = []
        output_format_2_obj = {
            'alfred': dict(title='', valid=False, field_name='title'),
            'ulauncher': dict(name='', field_name='name')}

        obj = output_format_2_obj[output_format]
        field_name = obj.pop('field_name')
        if not station_info:
            obj[field_name] = 'No buses in the next 30 minutes'
            etas.append(obj)

        for info in station_info:
            bus_number, eta = info
            obj[field_name] = f'{bus_number.strip()}: {eta.strip()}'
            etas.append(obj)

        if output_format == 'alfred':
            etas = dict(items=etas)

        return json.dumps(etas)

    # Function entry point
    station_id = args.station_id
    url = urljoin(URL, str(station_id))
    try:
        with urlopen(url, timeout=2) as res:
            res_bytes = res.read()
            res_text = res_bytes.decode('utf-8')

            # Match bus number and ETA
            match = BUS_NUM_AND_ETA_REGEX.findall(res_text)
    except urllib.error.HTTPError:
        res_text = f'Invalid station ID "{station_id}"'
        match = [('ERROR', res_text)]

    # Normalize result
    if args.output_format == 'raw':
        print(res_text)
    else:
        normalized_output = normalize_output(match, args.output_format)
        print(normalized_output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A script for getting a bus ETA from Curlbus service', add_help=True)
    parser.add_argument(
        '--version', '-v', '-V', action='version', help='This script version', version=THIS_SCRIPT_VERSION_STR)
    parser.add_argument('--station-id', '-s', help='Bus station ID', required=True)
    parser.add_argument(
        '--output-format', '-o', choices=('alfred', 'ulauncher', 'raw'), default='alfred', help='Output format')
    args = parser.parse_args()
    main(args)

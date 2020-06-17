#!/usr/bin/env python
#
# Written by denpy in 2020.
# https://github.com/denpy
#
"""
This script gets a bus ETA from the https://curlbus.app and outputs the result in a format which Alfred (macOS) or
Ulauncher (Linux) expects. Output is a JSON object printed to the STDOUT, both Alfred and Ulauncher will run this
script and load it's output as a JSON for further processing
"""
from __future__ import annotations

import argparse
import json
import re
from typing import Any, Dict, List, Tuple, Union
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import urlopen

THIS_SCRIPT_VERSION = (1, 0, 0)
THIS_SCRIPT_VERSION_STR = '.'.join([str(d) for d in THIS_SCRIPT_VERSION])

CURLBUS_BASE_URL = 'https://curlbus.app/'
BUS_NUM_AND_ETA_REGEX = re.compile(r'│(?P<bus_number>\d+).*│(?P<eta>[\d m,]+)')


def main(args):

    def get_etas(station_id: str) -> List[Tuple[str, str]]:
        """
        Get ETAs from Curlbus service
        :param station_id: ID of the station user wish to get ETAs for
        :return: Pairs of strings which maybe either bus numbers and ETAs or error messages
        """
        url = urljoin(CURLBUS_BASE_URL, station_id.strip())
        try:
            # Try to get the info from Curlbus
            with urlopen(url, timeout=2) as res:
                res_bytes = res.read()
                res_text = res_bytes.decode('utf-8')

            # Match bus number and ETA and return
            return BUS_NUM_AND_ETA_REGEX.findall(res_text)
        except HTTPError:
            return [('ERROR', f'Invalid station ID "{station_id}"')]
        except URLError:
            return [('ERROR', 'Curlbus does not respond')]

    def make_msg_obj(msg: str, output_format: str) -> Dict[str, Any]:
        """
        Makes a dict with fields that fit Alfred or Ulauncher format
        More about formats:
            https://www.alfredapp.com/help/workflows/inputs/script-filter/json/
            http://docs.ulauncher.io/en/latest/extensions/tutorial.html#main-py
        :param msg: a message that will be presented in Alfred or Ulauncher UI
        :param output_format: the format of the output object ("alfred" or "ulauncher")
        :return: a dict that contains the message in a format that Alfred ot Ulauncher can handle
        """
        # A "template" objects with specific fields per output format
        output_format_2_obj = {
            'alfred': dict(title='', valid=False, field_name='title'),
            'ulauncher': dict(name='', field_name='name')}

        # Get a "template" object according to the output type
        msg_obj = output_format_2_obj[output_format].copy()

        # Get the field name we need to use to create an object that fits the output type
        field_name = msg_obj.pop('field_name')
        msg_obj[field_name] = msg

        return msg_obj

    def normalize_etas(
            etas: List[Tuple[str, str]],
            output_format: str) -> Union[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
        """
        Normalize ETA messages received from Curlbus to objects according to the format of Alfred or Ulauncher
        :param etas: ETA messages or error messages
        :param output_format: format that should be used for messages normalization
        :return: normalized ETA messages or error messages
        """
        eta_objs = []

        if not etas:
            # There is no ETA so we return a message about that
            eta_objs.append(make_msg_obj('No buses in the next 30 minutes', output_format))

        # Normalize result, make objects with the bus number and ETA according to output format
        for info in etas:
            msg = ': '.join([s.strip() for s in info])
            eta_objs.append(make_msg_obj(msg, output_format))

        # Alfred expects to the object which looks like that {"items": [{...}, ...]}
        if output_format == 'alfred':
            return dict(items=eta_objs)

        return eta_objs

    # Function entry point
    # Get bus ETAs from Curlbus
    etas = get_etas(str(args.station_id))

    # Normalize ETA messages according to output format
    eta_objs = normalize_etas(etas, args.output_format)

    # Print the final object so Alfred or Ulauncher could load it and process
    print(json.dumps(eta_objs))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A script for getting a bus ETA from Curlbus service', add_help=True)
    parser.add_argument(
        '--version', '-v', '-V', action='version', help='This script version', version=THIS_SCRIPT_VERSION_STR)
    parser.add_argument(
        '--station-id', '-s', help='Bus station ID', required=True)
    parser.add_argument(
        '--output-format', '-o', choices=('alfred', 'ulauncher'), default='alfred', help='Output format')
    args = parser.parse_args()
    main(args)

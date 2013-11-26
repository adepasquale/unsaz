#!/usr/bin/env python

"""Command line tool for processing Fiddler .saz files"""

import sys
import re
from argparse import ArgumentParser
from datetime import datetime
from zipfile import ZipFile
from xml.etree import ElementTree

import colorama
from netaddr import IPAddress

__author__ = "Andrea De Pasquale"
__email__ = "andrea@de-pasquale.name"


class Unsaz:
    metadata_regexp = re.compile("raw/(?P<id>[0-9]+)_m\.xml")
    metadata_pattern = "raw/{}_m.xml"
    client_pattern = "raw/{}_c.txt"
    server_pattern = "raw/{}_s.txt"

    def __init__(self):
        self._parse_args()
        colorama.init()

    def _parse_args(self):
        arg_parser = ArgumentParser(
            description="Command line tool for processing Fiddler .saz files")
        arg_parser.add_argument(
            "-l", "--list", help="list requests and responses")
        arg_parser.print_help()

    def do_list(self, saz_name):
        with ZipFile(saz_name) as saz_file:
            for saz_element in saz_file.namelist():
                self.metadata_match = self.metadata_regexp.match(saz_element)
                if self.metadata_match is not None:
                    id = self.metadata_match.group("id")

                    metadata_name = self.metadata_pattern.format(id)
                    client_name = self.client_pattern.format(id)
                    server_name = self.server_pattern.format(id)

                    metadata_file = saz_file.open(metadata_name)
                    client_file = saz_file.open(client_name)
                    server_file = saz_file.open(server_name)

                    metadata_tree = ElementTree.fromstring(metadata_file.read())
                    timers = metadata_tree.find("SessionTimers").attrib
                    datetime_fmt = "%Y-%m-%dT%H:%M:%S.%f"  # FIXME timezone
                    client_time = datetime.strptime(
                        timers["ClientBeginRequest"][:-7], datetime_fmt)
                    server_time = datetime.strptime(
                        timers["ServerBeginResponse"][:-7], datetime_fmt)

                    client_ipv6 = metadata_tree.find(
                        "SessionFlags/SessionFlag[@N='x-clientip']").attrib["V"]
                    client_ipv4 = IPAddress(client_ipv6).ipv4()
                    server_ipv6 = metadata_tree.find(
                        "SessionFlags/SessionFlag[@N='x-hostip']").attrib["V"]
                    server_ipv4 = IPAddress(server_ipv6).ipv4()

                    client_data = client_file.readline()
                    server_data = server_file.readline()

                    print colorama.Style.BRIGHT, colorama.Fore.BLUE, "#", id, "C>S",
                    print colorama.Style.RESET_ALL, client_time,
                    print colorama.Style.BRIGHT, colorama.Fore.BLUE, client_ipv4,
                    print colorama.Style.RESET_ALL, client_data,
                    print colorama.Style.BRIGHT, colorama.Fore.GREEN, "#", id, "C<S",
                    print colorama.Style.RESET_ALL, server_time,
                    print colorama.Style.BRIGHT, colorama.Fore.GREEN, server_ipv4,
                    print colorama.Style.RESET_ALL, server_data,

if __name__ == "__main__":
    unsaz = Unsaz()
    unsaz.do_list(sys.argv[1])

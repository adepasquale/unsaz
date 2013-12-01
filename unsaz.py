#!/usr/bin/env python

"""Command line tool for processing Fiddler .saz files"""

import re
from argparse import ArgumentParser
#from datetime import datetime
from zipfile import ZipFile
from xml.etree import ElementTree

import colorama
from netaddr import IPAddress

__author__ = "Andrea De Pasquale"
__email__ = "andrea@de-pasquale.name"


class Unsaz:
    def __init__(self, input_file):
        colorama.init()

        with ZipFile(input_file) as saz_file:

            self.transactions = dict()
            metadata_regexp = re.compile("raw/(?P<id>[0-9]+)_m\.xml")

            for saz_member in saz_file.namelist():
                metadata_match = metadata_regexp.match(saz_member)
                if metadata_match is not None:
                    transaction_id = metadata_match.group("id")
                    self.transactions[int(transaction_id)] = \
                        self._parse_transaction(saz_file, transaction_id)

    def _parse_transaction(self, saz_file, transaction_id):
        metadata_file = saz_file.open("raw/{}_m.xml".format(transaction_id))
        metadata_tree = ElementTree.fromstring(metadata_file.read())
        timers_element = metadata_tree.find("SessionTimers")
        flag_client_ip = metadata_tree.find(
            "SessionFlags/SessionFlag[@N='x-clientip']")
        flag_server_ip = metadata_tree.find(
            "SessionFlags/SessionFlag[@N='x-hostip']")

        #datetime_fmt = "%Y-%m-%dT%H:%M:%S.%f"  # FIXME timezone
        #client_time = datetime.strptime(..., datetime_fmt)
        #server_time = datetime.strptime(..., datetime_fmt)

        client_timestamp = timers_element.attrib["ClientBeginRequest"]
        server_timestamp = timers_element.attrib["ServerBeginResponse"]
        client_address = IPAddress(flag_client_ip.attrib["V"]).ipv4()
        server_address = IPAddress(flag_server_ip.attrib["V"]).ipv4()
        client_message = self._split_message(
            saz_file, "raw/{}_c.txt".format(transaction_id))
        server_message = self._split_message(
            saz_file, "raw/{}_s.txt".format(transaction_id))

        return {
            "client": {
                "timestamp": client_timestamp,
                "address": client_address,
                "message": client_message,
            },
            "server": {
                "timestamp": server_timestamp,
                "address": server_address,
                "message": server_message,
            },
        }

    def _split_message(self, saz_file, message_name):
        message_file = saz_file.open(message_name)

        line = message_file.readline()

        head = ""
        while True:
            data = message_file.readline()
            if data.strip():
                head += data
            else:
                break

        body = message_file.read()

        return {
            "line": line,
            "head": head,
            "body": body,
        }

    def _get_color(self, response):
        colors = {
            "1": colorama.Fore.BLUE,
            "2": colorama.Fore.GREEN,
            "3": colorama.Fore.YELLOW,
            "4": colorama.Fore.RED,
            "5": colorama.Fore.MAGENTA,
        }

        code = response["line"][9]  # FIXME horrible
        return colors.get(code, colorama.Fore.CYAN)

    def list_all(self):
        for t_id in range(1, 1 + len(self.transactions)):
            self.list_client(t_id)
            self.list_server(t_id)

    def list_client(self, t_id):
        client = self.transactions[t_id]["client"]
        print(colorama.Fore.WHITE +
              colorama.Style.NORMAL +
              "{:>4}  ".format(t_id) +
              "{:<33}  ".format(client["timestamp"]) +
              "{:<15}  ".format(client["address"]) +
              client["message"]["line"]),

    def list_server(self, t_id):
        server = self.transactions[t_id]["server"]
        print(self._get_color(server["message"]) +
              colorama.Style.NORMAL +
              "{:>4}  ".format(t_id) +
              "{:<33}  ".format(server["timestamp"]) +
              "{:<15}  ".format(server["address"]) +
              server["message"]["line"]),


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Command line tool for processing Fiddler .saz files")
    parser.add_argument("saz_file", type=file, help="Fiddler input file")
#    parser.add_argument("-4", action="store_true", help="use IPv4 addresses")
#    parser.add_argument("-6", action="store_true", help="use IPv6 addresses")
    group_t = parser.add_argument_group("transaction options")
    group_t = group_t.add_mutually_exclusive_group()
    group_t.add_argument("-i", type=int, help="list a single transaction")
    group_t.add_argument("-c", type=int, help="list a single request")
    group_t.add_argument("-s", type=int, help="list a single response")
    group_m = parser.add_argument_group("message options")
    group_m.add_argument("-l", action="store_false",
                         help="hide request/response line")
    group_m.add_argument("-H", action="store_true",
                         help="show request/response headers")
    group_m.add_argument("-B", action="store_true",
                         help="show request/response body")
#    group_s = parser.add_argument_group("sorting options")
#    group_s.add_argument("-t", action="store_true",
#                         help="sort transactions by timestamp")
#    group_s.add_argument("-a", action="store_true",
#                         help="sort transactions by address")
    arguments = parser.parse_args()

    unsaz = Unsaz(arguments.saz_file)
    unsaz.list_all()

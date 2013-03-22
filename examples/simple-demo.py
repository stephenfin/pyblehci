#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013, Stephen Finucane

# Author: Stephen Finucane <stephenfinucane@hotmail.com>

""" Simple application to build and parse HCI packets from a TI BLE device running HostTestRelease """

import sys
import collections

from pyblehci import BLEBuilder
from pyblehci import BLEParser

def test_builder():
	ble_builder = BLEBuilder()
	print(ble_builder._build_command("fe00"))
	print(ble_builder._build_command("fe31", param_id="\x15"))
	print(ble_builder._build_command("fe04", mode="\x03"))
	print(ble_builder._build_command("fe09", peer_addr="\x57\x6A\xE4\x31\x18\x00"))
	print(ble_builder._build_command("fd8a", conn_handle="\x00\x00", handle="\x27\x00"))
	print(ble_builder._build_command("fe0a", conn_handle="\x00\x00"))

def test_parser():
	ble_parser = BLEParser()
	print(ble_parser._split_response("\x04\xFF\x2C\x00\x06\x00\x06\x30\x85\x31\x18\x00\x1B\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x09\x09\x09\x09\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x09\x09\x09\x09\x00\x00"))
	print(ble_parser._split_response("\x04\xFF\x08\x7F\x06\x00\x31\xFE\x02\xD0\x07"))
	print(ble_parser._split_response("\x04\xFF\x0C\x01\x06\x00\x01\x00\x00\x57\x6A\xE4\x31\x18\x00"))
	print(ble_parser._split_response("\x04\xFF\x14\x01\x06\x00\x01\x00\x00\x57\x6A\xE4\x31\x18\x00\x11\x11\x11\x11\x11\x11\x11\x11"))
	print(ble_parser._split_response("\x04\xFF\x07\x01\x06\x00\x00"))

if __name__ == "__main__":
	test_builder()
	test_parser()
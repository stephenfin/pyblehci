#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@fn ble_parser.py

@author Stephen Finucane, 2013-2014
@email  stephenfinucane@hotmail.com

@about Sample application demonstrating use of pyblehci to write/read
    to/from a serial device.
"""

from __future__ import print_function

import collections
import serial
import time

from pyblehci import BLEBuilder
from pyblehci import BLEParser


def pretty(hex_string, seperator=' '):
    """
    Prettify a hex string.

    >>> pretty("\x01\x02\x03\xff")
    '01 02 03 FF'
    """
    hex_string = hex_string.encode('hex')
    out = ''

    for i in range(len(hex_string)):
        if not i % 2:
            out = out + seperator
        out = out + hex_string[i].capitalize()

    return out


def print_ordered_dict(dictionary):
    result = ""
    for key in dictionary:
        if dictionary[key]:
            #convert e.g. "data_len" -> "Data Len"
            title = ' '.join(key.split("_")).title()
            if isinstance(dictionary[key], list):
                for idx2, _ in enumerate(dictionary[key]):
                    result += "{0} ({1})\n".format(title, idx2)
                    result += print_ordered_dict(dictionary[key][idx2])
            elif isinstance(dictionary[key], type(collections.OrderedDict())):
                result += '{0}\n{1}'.format(title, print_ordered_dict(
                    dictionary[key]))
            else:
                result += "{0:15}\t: {1}\n\t\t  ({2})\n".format(
                    title, pretty(dictionary[key][0], ':'), dictionary[key][1])
        else:
            result += "{0:15}\t: None".format(key)
    return result


def print_output((packet, dictionary)):
    result = print_ordered_dict(dictionary)
    result += 'Dump:\n{0}\n'.format(pretty(packet))
    return result


def analyse_packet((packet, dictionary)):
    print("EVENT: Response received from the device")
    print(print_output((packet, dictionary)))


def main():
    """
    Main function.
    """
    # initialise objects
    serial_port = serial.Serial(port='COM4', baudrate=57600)
    ble_builder = BLEBuilder(serial_port)
    ble_parser = BLEParser(serial_port, callback=analyse_packet)

    # initialise the device
    print("COMMAND: Initialising device")
    print(print_output(ble_builder.send("fe00")))

    # get an operating parameter value
    print("COMMAND: Getting operating parameter value")
    print(print_output(ble_builder.send("fe31", param_id="\x15")))

    # start a device discovery scan
    print("COMMAND: Starting device scan")
    print(print_output(ble_builder.send("fe04", mode="\x03")))

    # sleep main thread for 15 seconds - allow results of device scan to return
    time.sleep(15)

    #close device
    ble_parser.stop()


if __name__ == "__main__":
    main()

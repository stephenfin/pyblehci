pyblehci
========

pyblehci is a library, written in Python, that provides a combined 
parser-builder for TI vendor-specific HCI packets utilised by the 
HostTestRelease application.

.. code-block:: pycon

    >>> p = pyblehci.BLEParser()
    >>> p._split_response("\\x04\\xFF\\x08\\x7F\\x06\\x00\\x31\\xFE\\x02\\xD0\\x07")
    ('\\x04\\xff\\x08\\x7f\\x06\\x00\\x31\\xfe\\x02\\xd0\\x07', OrderedDict(
    [('type', ('\\x04', 'Event')), 
    ('event_code', ('\\xff', 'HCI_LE_ExtEvent')), 
    ('data_len', ('\\x02', '02')), 
    ('event', ('\\x06\\x7f', 'GAP_HCI_ExtensionCommandStatus')), 
    ('status', ('\\x00', '00')), 
    ('op_code', ('\\31\\xfe', 'GAP_GetParam')), 
    ('param_value', ('\\xd0\\x07', '07d0'))]))
    
    >>> b = pyblehci.BLEBuilder()
    >>> b._build_command("fe31", param_id="\x15")
    ('\\x01\\x31\\xfe\\x01\\x15', OrderedDict([
    ('type', ('\\x01', 'Command')), 
    ('op_code', ('\\x31\\xfe', 'GAP_GetParam')), 
    ('data_len', ('\\x01', '01')), 
    ('param_id', ('\\x15', '15'))])
    )
    ...

pyblehci can also be used to read and write to the device found on the serial 
interface. The parser operates asynchronously via a callback method allowing 
asynchronous reading/writing of the device. 
This is possible by use of `pySerial <http://pyserial.sourceforge.net/>`_

.. code-block:: pycon
    
    >>> serial_port = serial.Serial(port='/dev/ttyACM0', baudrate=57600)
    >>> def analyse_packet(packet):
    ...     print packet
    ...
    >>> p = pyblehci.BLEParser(serial_port, callback=analyse_packet)
    >>> b = pyblehci.BLEBuilder(serial_port)
    >>> b.send(cmd="fe31", param_id="\x15")
    ('\x011\xfe\x01\x15', OrderedDict([('type', ('\x01', 'Command')), ('op_code', ('
    1\xfe', 'GAP_GetParam')), ('data_len', ('\x01', '01')), ('param_id', ('\x15', '1
    5'))]))
    ('\x04\xff\x08\x7f\x06\x001\xfe\x02P\x00', OrderedDict([('type', ('\x04', 'E
    vent')), ('event_code', ('\xff', 'HCI_LE_ExtEvent')), ('data_len', ('\x02', '02'
    )), ('event', ('\x06\x7f', 'GAP_HCI_ExtensionCommandStatus')), ('status', ('\x00
    ', '00')), ('op_code', ('1\xfe', 'GAP_GetParam')), ('param_value', ('P\x00', '00
    50'))]))
    >>>
    ...


Features
--------

- Parsing and Building of TI vendor-specific HCI packets
- Monitoring of serial BLE devices using the HostTestRelease application.

Supported Devices
-----------------

The library should support any TI single-mode BLE device that uses the 
HostTestRelease firmware. The below devices are those that have been tested

- TI CC2540DK-MINI Development Kit USB Dongle

Installation
------------

To download pyblehci:

.. code-block:: bash

    $ git clone https://stephenfinucane@code.google.com/p/pyblehci/

To install:

.. code-block:: bash

    $ python setup.py install

Contribute
----------

- While most of the packets structures have been implemented in both the 
  BLEParser and BLEBuilder modules, they are not complete. Additional packets
  can be found in the 'TI Vendor Specific HCI Guide' pdf document that is 
  included in the TI BLE stack download
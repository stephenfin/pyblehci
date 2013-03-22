#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013, Stephen Finucane

# Author: Stephen Finucane <stephenfinucane@hotmail.com>

import collections
import serial
import threading
import time

# Override thread quit exception handler
class ThreadQuitException(Exception):
	pass

class BLEParser(threading.Thread):
	"""
	A parser for event packets as defined by the the Texas Instruments Bluetooth
	Low Energy Host-Controller-Interface (HCI).
	
	Capable of monitoring a serial device, parsing the packets and returning to
	a calling method by callback

	Based heavily on python-xbee library by Paul Malmsten.
	"""
	#dictionaries	
	#opcodes for command packets
	opcodes = 	{"fd8a":'GATT_ReadCharValue',
				 "fd8e":'GATT_ReadMultipleCharValues',
				 "fd92":'GATT_WriteCharValue',
				 "fd96":'GATT_WriteLongCharValue',
				 "fdb2":'GATT_DiscAllChars',
				 "fdb4":'GATT_ReadUsingCharUUID',
				 "fe00":'GAP_DeviceInit',
				 "fe03":'GAP_ConfigureDeviceAddr',
				 "fe04":'GATT_DeviceDiscoveryRequest',
				 "fe05":'GATT_DeviceDiscoveryCancel',
				 "fe09":'GATT_EstablishLinkRequest',
				 "fe0a":'GATT_TerminateLinkRequest',
				 "fe30":'GAP_SetParam',
				 "fe31":'GAP_GetParam',
				}

	#structure of event packets
	hci_events = {"ff":
					{'name':'HCI_LE_ExtEvent',
				 	 'structure':
						[{'name':'ext_event',	'len':None}]},
				}

	#parameter formats for HCI_LE_ExtEvent
	ext_events= {"0501":
					{'name':'ATT_ErrorRsp',
					 'structure':
					 	[{'name':'conn_handle',	'len':2},
					 	 {'name':'pdu_len',		'len':1},
					 	 {'name':'req_op_code',	'len':1},
					 	 {'name':'handle',		'len':2},
					 	 {'name':'error_code',	'len':1}]},
				"0509":
					{'name':'ATT_ReadByTypeRsp',
					 'structure':
					 	[{'name':'conn_handle',	'len':2},
					 	 {'name':'pdu_len',		'len':1},
					 	 {'name':'length',		'len':1},
					 	 {'name':'results',		'len':None}],
					 'parsing': 
					 	[('results', lambda ble, original: 
					 		ble._parse_read_results(original['results']))]},
				"050b":
					{'name':'ATT_ReadRsp',
					 'structure':
					 	[{'name':'conn_handle',	'len':2},
					 	 {'name':'pdu_len',		'len':1},
					 	 {'name':'value',		'len':None}]},
				"050f":
					{'name':'ATT_ReadMultiRsp',
					 'structure':
					 	[{'name':'conn_handle',	'len':2},
					 	 {'name':'pdu_len',		'len':1},
					 	 {'name':'results',		'len':None}]},
				"0513":
					{'name':'ATT_WriteRsp',
					 'structure':
					 	[{'name':'conn_handle',	'len':2},
					 	 {'name':'pdu_len',		'len':1}]},
				"051b":
					{'name':'ATT_HandleValueNotification',
					 'structure':
					 	[{'name':'conn_handle',	'len':2},
					 	 {'name':'pdu_len',		'len':1},
					 	 {'name':'handle',		'len':2},
					 	 {'name':'values',		'len':None}]},
				"0600":
					{'name':'GAP_DeviceInitDone',
					 'structure':
					 	[{'name':'dev_addr',	'len':6},
					 	 {'name':'data_pkt_len','len':2},
					 	 {'name':'num_data_pkts','len':1},
					 	 {'name':'irk',			'len':16},
					 	 {'name':'csrk',		'len':16}]},
				"0601":
					{'name':'GAP_DeviceDiscoveryDone',
					 'structure':
					 	[{'name':'num_devs',	'len':1},
					 	 {'name':'devices',		'len':None}],
					 'parsing': 
					 	[('devices', lambda ble, original: 
					 		ble._parse_devices(original['devices']))]},
				"0605":
					{'name':'GAP_EstablishLink',
					 'structure':
					 	[{'name':'dev_addr_type','len':1},
					 	 {'name':'dev_addr',	'len':6},
					 	 {'name':'conn_handle',	'len':2},
					 	 {'name':'conn_interval','len':2},
					 	 {'name':'conn_latency','len':2},
					 	 {'name':'conn_timeout','len':2},
					 	 {'name':'clock_accuracy','len':1}]},
				"060d":
					{'name':'GAP_DeviceInformation',
					 'structure':
					 	[{'name':'event_type',	'len':1},
					 	 {'name':'addr_type',	'len':1},
					 	 {'name':'addr',		'len':6},
					 	 {'name':'rssi',		'len':1},
					 	 {'name':'data_len',	'len':1},
					 	 {'name':'data_field',	'len':None}]},
				"0606":
					{'name':'GAP_LinkTerminated',
					 'structure':
					 	[{'name':'conn_handle',	'len':2},
					 	 {'name':'reason',		'len':1}]},
				"067f":
					{'name':'GAP_HCI_ExtensionCommandStatus',
					 'structure':
					 	[{'name':'op_code',		'len':2},
					 	 {'name':'data_len',	'len':1},
					 	 {'name':'param_value',	'len':None}],
					 'parsing': 
					 	[('op_code', lambda ble, original: 
					 		ble._parse_opcodes(original['op_code']))]},
				}

	def __init__(self, ser=None, callback=None):
		"""
		Initialises the class

		@param ser: The file like serial port to use
		@type ser: serial.Serial

		@param callback: The callback method
		@type callback: <function>
		"""
		super(BLEParser, self).__init__()
		self.serial_port = ser
		self._callback = None
		self._thread_continue = False
		self._stop = threading.Event()
		
		if callback:
			self._callback = callback
			self._thread_continue = True
			self.start()

	def run(self):
		"""
		Overrides threading.Thread.run() and is automatically
		called when an instance is created with threading enabled
		"""
		while True:
			try:
				self._callback(self.wait_read())
			except ThreadQuitException:
				break

	def stop(self):
		"""
		Stops the thread and closes the serial port
		"""
		self._thread_continue = False
		self.serial_port.close()
		self._stop.set()

	def stopped(self):
		"""
		Getter method for isSet variable

		>>> stopped()
		false
		"""
		return self._stop.isSet()

	def _wait_for_frame(self):
		"""
		Reads from the serial port until a valid HCI packet arrives. It will then 
		return the binary data contained within the packet.

		@return: A byte string of the correct length
		"""
		#loop forever...
		while True:
			#...unless told not to by setting "_thread_continue" to false
			if self._callback and not self._thread_continue:
				raise ThreadQuitException

			#prevent blocking the port by waiting a given time
			#TODO. Remove this? Asynchronous read-write possible
			if self.serial_port.inWaiting() == 0:
				time.sleep(.01)
				continue
			
			#length byte is stored as the third byte in an event packet
			packet = self.serial_port.read(3)
			#convert this to decimal...
			data_len = int(packet[2].encode('hex'), 16)
			
			#...and retrieve that many bytes from the serial port
			for x in range(0,data_len):
				packet += self.serial_port.read()
			
			return packet		

	def _split_response(self, data):
		"""
		Takes a data packet received from a TI BLE device and parses it.

		>>> _split_response("\\x04\\xFF\\x08\\x7F\\x06\\x00\\x31\\xFE\\x02\\xD0\\x07")
		('\\x04\\xff\\x08\\x7f\\x06\\x00\\x31\\xfe\\x02\\xd0\\x07', OrderedDict(
		[('type', ('\\x04', 'Event')), 
		('event_code', ('\\xff', 'HCI_LE_ExtEvent')), 
		('data_len', ('\\x02', '02')), 
		('event', ('\\x06\\x7f', 'GAP_HCI_ExtensionCommandStatus')), 
		('status', ('\\x00', '00')), 
		('op_code', ('\\31\\xfe', 'GAP_GetParam')), 
		('param_value', ('\\xd0\\x07', '07d0'))]))

		@param data: The byte string to split and parse
		@type data: hex

		@return: An ordered dictionary (data order is important) containing binary
			tuples, in which the first piece of data corresponds to the raw byte 
			string value and the second piece corresponds to its parsed 
			"meaning"
		"""
		packet_type = data[0]
		event_code 	= data[1]
		data_len 	= data[2]

		#check for matching event codes in dictionary and store the matching
		# packet format
		try:
			packet = self.hci_events[event_code.encode('hex')]
		except AttributeError:
			raise NotImplementedError("Error with Attribute")
		except KeyError:
			raise KeyError("Unrecognized response packet with event" + 
				" type {0}".format(event_code.encode('hex')))

		packet_type_parsed 	= "Event"
		event_code_parsed 	= packet['name']
		data_len_parsed 	= int(data_len.encode('hex'),16)

		#packet match found, hence start storing result
		parsed_packet = collections.OrderedDict()
		parsed_packet['type'] 		= (packet_type, packet_type_parsed)
		parsed_packet['event_code'] = (event_code, event_code_parsed)
		parsed_packet['data_len'] 	= (data_len, data_len_parsed)

		#store the packet structure for working with in next step
		packet_structure = packet['structure']

		#special handler for HCI_LE_ExtEvent
		if event_code_parsed == 'HCI_LE_ExtEvent':
			#current byte index in the data stream
			index = 6
			#event_subcode is two-bytes given in reverse (endian mismatch?)
			event_subcode 	= data[3:5][::-1]	#reverse byte order [::-1]
			event_status	= data[5]

			try:
				subpacket = self.ext_events[event_subcode.encode('hex')]
			except AttributeError:
				raise NotImplementedError("Error with Attribute")
			except KeyError:
				print data.encode('hex')
				raise KeyError("Unrecognized response packet with event" +
					" type {0}".format(data[3:5][::-1]))

			event_subcode_parsed	= subpacket['name']
			event_status_parsed		= event_status.encode('hex')

			#subpacket match found, hence store result
			parsed_packet['event']	= (event_subcode, event_subcode_parsed)
			parsed_packet['status']	= (event_status, event_status_parsed)

			#store the subpacket structure for working with in next step
			subpacket_structure		= subpacket['structure']

			#parse the subpacket in the order specified, by processing each 
			# required value as needed
			for field in subpacket_structure:
				field_name = field['name']
				#if the data field has a fixed length, process it normally
				if field['len'] is not None:
					#store the number of bytes specified in the dictionary
					field_data = data[index:(index + field['len'])]
					field_data_parsed = field_data[::-1].encode('hex')
					#store result
					parsed_packet[field_name] = (field_data, field_data_parsed)
					#increment index for next field
					index += field['len']
				#if the data field has no length specified, store any leftover
				# bytes and quit
				else:
					field_data = data[index:]
					#were there any remaining bytes?
					if field_data:
						#if so, store them
						field_data_parsed = field_data[::-1].encode('hex')
						parsed_packet[field_name] = (field_data, field_data_parsed)
						index += len(field_data)
					break

			#check if there are remaining bytes. If so, raise an exception
			if index < data_len_parsed:
				raise ValueError("Response packet was longer than expected;" +
					"expected: %d, got: %d bytes" % (index, data_len_parsed))

			#check for parsing rules and apply them if they exist
			if 'parsing' in subpacket:
				for parse_rule in subpacket['parsing']:
					#only apply a rule if relevant (raw data available)
					parse_rule_name = parse_rule[0]
					parse_rule_def = parse_rule[1]
					if parse_rule_name in parsed_packet:
						#apply the parse function to the indicated field 
						# and replace the raw data with the result
						parsed_packet[parse_rule_name] = parse_rule_def(self,parsed_packet)

		return (data, parsed_packet)

	def _parse_opcodes(self, parsed_packet):
		"""
		Functions as a special parsing routine for the "GAP HCI Extention Command 
		Status" HCI LE ExtEvent.

		>>> _parse_opcodes(("\\x04\\xFE", "fe04"))
		("\\x04\\xFE", "GAP_DeviceDiscoveryRequest")

		@param parsed_packet: A tuple of a byte string and the ascii encoded copy
		@type parsed_packet: (hex, string)

		@return:	An ordered dictionary (data order is important) containing binary
			tuples, in which the first piece of data corresponds to the raw 
			byte string value and the second piece corresponds to its parsed 
			"meaning" - the command name sourced by lookup of the command dict

		
		"""
		value = self.opcodes[parsed_packet[1]]
		return (parsed_packet[0], value)

	def _parse_devices(self, orig_devices):
		"""
		Functions as a special parsing routine for the "GAP Device Discovery 
		Done" HCI LE ExtEvent.

		>>> _parse_devices(("\\x00\\x00\\x57\\x6A\\xE4\\x31\\x18\\x00", "0000576AE4311800"))
		[OrderedDict([
		('event_type', ('\\x00', '00')), 
		('addr_type', ('\\x00', '00')), 
		('addr', ('\\x57\\x6a\\xe4\\x31\\x18\\x00', '001831e46a57'))
		])]

		@param orig_devices: A tuple of a byte string and the ascii encoded copy
		@type orig_devices: (hex, string)

		@return: An ordered dictionary (data order is important) containing binary
			tuples, in which the first piece of data corresponds to the raw 
			byte string value and the second piece corresponds to its parsed 
			"meaning" - currently just the hex encoded version of the string

		"""
		parsed_devices = []
		#seperate the byte string containing the devices into groups of eight 
		# bytes
		for idx, device in enumerate([orig_devices[0][i:i+8] for i in 
			range(0, len(orig_devices[0]), 8)]):
			event_type 	= device[0]
			addr_type 	= device[1]
			addr 		= device[2:9]

			event_type_parsed 	= event_type.encode('hex')
			addr_type_parsed 	= addr_type.encode('hex')
			addr_parsed 		= addr[::-1].encode('hex')

			#store the parsed device as an ordered dictionary (order once again
			# important)
			temp_device = collections.OrderedDict()
			temp_device['event_type'] 	= (event_type, event_type_parsed)
			temp_device['addr_type'] 	= (addr_type, addr_type_parsed)
			temp_device['addr'] 		= (addr, addr_parsed)

			#append the ordered dict containing the parsed device to a list
			parsed_devices.append(temp_device)
		#return the resulting list
		return parsed_devices

	def _parse_read_results(self, results):
		"""
		Functions as a special parsing routine for the "ATT Read By Type Rsp" HCI 
		LE ExtEvent.

		>>> _parse_read_results(("\\x00\\x00\\x57\\x6A\\xE4\\x31\\x18\\x00", "0000576AE4311800"))
		TODO

		@param results: A tuple of a byte string and the ascii encoded copy
		@type results: (hex, string)

		@return: An ordered dictionary (data order is important) containing binary
			tuples, in which the first piece of data corresponds to the raw 
			byte string value and the second piece corresponds to its parsed 
			"meaning" - currently just the hex encoded version of the string
		"""
		parsed_results = []
		#seperate the byte string containing the results into groups of eight 
		# bytes
		for idx, result in enumerate([results[0][i:i+8] for i in 
			range(0, len(results[0]), 8)]):
			handle 		= result[0:2]
			data 		= result[2:9]

			handle_parsed 	= handle[::-1].encode('hex')
			data_parsed 	= data[::-1].encode('hex')

			#store the parsed result as an ordered dictionary (order once again
			# important)
			temp_result = collections.OrderedDict()
			temp_result['handle'] 	= (handle, handle_parsed)
			temp_result['data'] 	= (data, data_parsed)

			#append the ordered dict containing the parsed result to a list
			parsed_results.append(temp_result)
		#return the resulting list
		return parsed_results

	
	def wait_read(self):
		"""
		Combines both _wait_for_frame (to read a valid packet) and _split_response 
		(to parse that packet).

		@return: A parsed version of the packet received on the serial port
		"""
		packet = self._wait_for_frame()
		return self._split_response(packet)
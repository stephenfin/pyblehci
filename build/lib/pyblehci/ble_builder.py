"""
@fn 	ti_ble_builder.py

@author	Stephen Finucane, 2013
@email	stephenfinucane@hotmail.com

@about	Based heavily on python-xbee library by Paul Malmsten.
		This class defines data and methods applicable to the Texas Instruments
		Bluetooth Low Energy Host-Controller-Interface (HCI)
"""

import collections
import serial

class BLEBuilder():
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

	#structure of command packets
	hci_cmds = 	{"fd8a":
					[{'name':'conn_handle',	'len':2,	'default':'\x00\x00'},
					 {'name':'handle',		'len':2,	'default':None}],
				"fd8e":
					[{'name':'conn_handle',	'len':2,	'default':'\x00\x00'},
					 {'name':'handles',		'len':None,	'default':None}],
				"fd92":
					[{'name':'conn_handle',	'len':2,	'default':'\x00\x00'},
					 {'name':'handle',		'len':2,	'default':None},
					 {'name':'value',		'len':None,	'default':None}],
				"fd96":
					[{'name':'handle',		'len':2,	'default':'\x00\x00'},
					 {'name':'offset',		'len':1,	'default':None},
					 {'name':'value',		'len':None,	'default':None}],
				"fdb2":
					[{'name':'start_handle','len':2,	'default':'\x00\x00'},
					 {'name':'end_handle',	'len':2,	'default':'\xff\xff'}],
				"fdb4":
					[{'name':'conn_handle',	'len':2,	'default':'\x00\x00'},
					 {'name':'start_handle','len':2,	'default':'\x01\x00'},
					 {'name':'end_handle',	'len':2,	'default':'\xff\xff'},
					 {'name':'read_type',	'len':2,	'default':None}],
				"fe00":
					[{'name':'profile_role','len':1,	'default':'\x08'},
					 {'name':'max_scan_rsps','len':1,	'default':'\x05'},
					 {'name':'irk',			'len':16,	'default':'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'},
					 {'name':'csrk',		'len':16,	'default':'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'},
					 {'name':'sign_counter','len':4,	'default':'\x01\x00\x00\x00'}],
				"fe03":
					[{'name':'addr_type',	'len':1,	'default':None},
					 {'name':'addr',		'len':6,	'default':None}],
				"fe04":
					[{'name':'mode',		'len':1,	'default':None},
					 {'name':'active_scan',	'len':1,	'default':'\x01'},
					 {'name':'white_list',	'len':1,	'default':'\x00'}],
				"fe05":
					[],
				"fe09":
					[{'name':'high_duty_cycle','len':1,	'default':'\x00'},
					 {'name':'white_list',	'len':1,	'default':'\x00'},
					 {'name':'addr_type_peer','len':1,	'default':'\x00'},
					 {'name':'peer_addr',	'len':6,	'default':None}],
				"fe0a":
					[{'name':'conn_handle',	'len':2,	'default':'\x00\x00'}],
				"fe30":
				 	[{'name':'param_id',	'len':1,	'default':None},
				 	 {'name':'param_value',	'len':2,	'default':None}],
				"fe31":
				 	[{'name':'param_id',	'len':1,	'default':None}],
				}

	def __init__(self, ser=None):
		"""
		Constructor Arguments:
			ser:		The file like serial port to use (see PySerial)
			callback:	The callback function to return data to
		"""
		self.serial_port = ser

	def _build_command(self, cmd, **kwargs):
		"""
		_build_command will construct a command packet according to the
		specified command's specification in the TI BLE Vendor Specific HCI 
		Guide. It will expect named arguments for all fields other than those 
		with a default value or length of 'None'.
	
		Each field will be written out in the order they are defined in the 
		command definition.

		Input:


		Returns:
			
		Example Packet:
		
		"""
		packet_type = "\x01"
		op_code 	= cmd.decode('hex')[::-1]	#command code was human-readable
		data_len 	= "\x00"	#insert dummy value for length

		#check for matching command codes in dictionary and store the matching
		# packet format
		try:
			packet_structure = self.hci_cmds[cmd]
		except AttributeError:
			raise NotImplementedError("Command spec could not be found")

		packet_type_parsed 	= "Command"
		op_code_parsed 	= self.opcodes[cmd]
		data_len_parsed 	= "0"	#insert dummy value for length

		#command match found, hence start storing result
		built_packet = collections.OrderedDict()
		built_packet['type'] 		= (packet_type, packet_type_parsed)
		built_packet['op_code'] 	= (op_code, op_code_parsed)
		built_packet['data_len'] 	= (data_len, data_len_parsed)

		packet = ''
		packet += packet_type
		packet += op_code
		packet += data_len

		#build the packet in the order specified, by processing each 
		# required value as needed
		for field in packet_structure:
			field_name = field['name']
			field_len = field['len']
			#try to read this field's name from the function arguments dict
			try:
				field_data = kwargs[field_name]
			#data wasn't given
			except KeyError:
				#only a problem is the field has a specific length...
				if field_len is not None:
					#...or a default value
					default_value = field['default']
					if default_value:
						#if it has a default value, use it
						field_data = default_value
					else:
						#otherwise fail
						raise KeyError("The data provided for '%s' was not %d bytes long"
							% (field_name, field_len))
				#no specific length, hence ignore it
				else:
					field_data = None

			#ensure that the correct number of elements will be written
			if field_len and len(field_data) != field_len:
				raise ValueError("The data provided for '%s' was not %d bytes long"
					% (field_name, field_len))

			#add the data to the packet if it has been specified (otherwise the
			# parameter was of variable length and not given)
			if field_data:
				packet += field_data
				built_packet[field_name] = (field_data, field_data.encode('hex'))

		#finally, replace the dummy length value 
		#in the string
		length = hex(len(packet) - 4)	#get length of bytes after 4th (length)
		data_len = length[2:].zfill(2).decode('hex')	#change 0x2 -> \x02
		modified_packet = list(packet)
		modified_packet[3] = data_len
		packet = "".join(modified_packet)
		#and the dictionary
		data_len_parsed = data_len.encode('hex')
		built_packet['data_len'] = (data_len, data_len_parsed)

		return (packet, built_packet)

	def send(self, cmd, **kwargs):
		"""
		send: string param=binary data ... -> None
		
		When send is called with the proper arguments, an HCI command
		will be written to the serial port for this BLE device
		containing the proper instructions and data
		
		This method must be called with the named arguments in accordance 
		with the HCI specification. Arguments matching all field names 
		other than those in the reserved_names (like 'id' and 'order')
		should be given, unless they are of variable length (of 'None' in
		the specification. These are optional).

		Example Usage:
			>>> print self.send(cmd="fe31", param_id="\x15")
			01:31:FE:01:15	#<-- also writes this to serial port
		"""
		packet, built_packet = self._build_command(cmd, **kwargs)
		self.serial_port.write(packet)
		return (packet, built_packet)
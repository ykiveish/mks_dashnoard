import os
import json
import time
import _thread

from core import co_common
from core import co_application
from classes import sensordb
from classes import translator

class Application(co_application.ApplicationLayer):
	def __init__(self):
		co_application.ApplicationLayer.__init__(self)
		# NODE BASIC
		self.WSHandlers["system_info"] 				= self.SystemInfoHandler
		self.WSHandlers["gateway_info"] 			= self.GatewayInfoHandler
		self.WSHandlers["list"] 					= self.SerialListHandler
		self.WSHandlers["connect"] 					= self.ConnectHandler
		self.WSHandlers["disconnect"] 				= self.DisconnectHandler
		# NODE UART CONNECTED
		self.WSHandlers["setworkingport"] 			= self.SetWorkingPortHandler
		self.WSHandlers["getdevicetype"] 			= self.GetDeviceTypeHandler
		self.WSHandlers["getdeviceadditional"] 		= self.GetDeviceAdditionalHandler
		self.WSHandlers["setnodeaddress"] 			= self.SetNodeAddressHandler
		self.WSHandlers["getnodeaddress"] 			= self.GetNodeAddressHandler
		self.WSHandlers["getnodeinfo"] 				= self.GetNodeInfoHandler
		self.WSHandlers["listnodes"] 				= self.GetNodeListHandler
		self.WSHandlers["getnodesmap"] 				= self.GetNodesMapHandler
		self.WSHandlers["addnodeindex"] 			= self.AddNodeIndexHandler
		self.WSHandlers["delnodeindex"] 			= self.DelNodeIndexHandler
		self.WSHandlers["getavailableindexes"] 		= self.GetAvailableIndexesHandler
		# NODE REMOTE CONNECTED
		self.WSHandlers["getnodeinfo_r"] 			= self.GetRemoteNodeInfoHandler
		self.WSHandlers["getnodedata_r"] 			= self.GetRemoteNodeDataHandler
		self.WSHandlers["setnodedata_r"] 			= self.SetRemoteNodeDataHandler
		self.WSHandlers["setnodeaddress_r"] 		= self.SetRemoteNodeAddressHandler
		self.WSHandlers["getnodeaddress_r"] 		= self.GetRemoteNodeAddressHandler
		# DB REQUESTS
		self.WSHandlers["select_sensors"] 			= self.SelectSensorsHandler
		self.WSHandlers["select_sensor_history"] 	= self.SelectSensorHistoryHandler
		self.WSHandlers["select_sensors_by_device"] = self.SelectSensorsByDeviceHandler
		self.WSHandlers["update_sensor_info"] 		= self.UpdateSensorInfoHandler
		self.WSHandlers["select_devices"] 			= self.SelectDevicesHandler
		self.WSHandlers["insert_device"] 			= self.InsertDeviceHandler
		self.WSHandlers["delete_device"] 			= self.DeleteDeviceHandler

		self.HW 			= None
		self.DB 			= sensordb.SensorDB("sensors.db")
		self.Translator 	= translator.BasicTranslator()

		self.WorkingPort = ""
		self.LocalUsbDb = {
			"comports": [],
			"device_id_list": [],
			"gateways": {},
			"nodes": {}
		}

		self.Working = False
	
	def Start(self):
		_thread.start_new_thread(self.Worker, ())
	
	def Worker(self):
		self.Working = True
		while self.Working is True:
			try:
				added, removed = self.CheckSerialConnections()
				if removed is not None:
					self.RemoveDisconnected(removed)
				if added is not None:
					self.ConnectNewComDevices(added)
				
				ans = self.HW.GetNodeList(self.WorkingPort)
				if ans is not None:
					for node in ans["list"]:
						self.LocalUsbDb["gateways"][self.WorkingPort]["remotes"][node["device_id"]]["status"] = node["status"]
					self.EmitEvent({
						"event": "GetNodeListHandler",
						"data": ans
					})
				else:
					self.EmitEvent({
						"event": "GetNodeListHandler",
						"data": {
							"list": []
						}
					})

				time.sleep(5)
			except Exception as e:
				print("Worker Exception: {0}".format(e))
	
	def RemoveGateway(self, comport):
		if comport in self.LocalUsbDb["gateways"]:
			print("RemoveGateway")
			self.EmitEvent({
				"event": "USBDeviceDisconnectedHandler",
				"data": {
					"type": "GATEWAY",
					"port": self.LocalUsbDb["gateways"][comport]["port"],
					"index": self.LocalUsbDb["gateways"][comport]["index"],
				}
			})
			del self.LocalUsbDb["gateways"][comport]
	
	def RemoveNodes(self, comport):
		if comport in self.LocalUsbDb["nodes"]:
			print("RemoveNodes")
			self.EmitEvent({
				"event": "USBDeviceDisconnectedHandler",
				"data": {
					"type": "NODE",
					"port": self.LocalUsbDb["nodes"][comport]["port"],
					"index": self.LocalUsbDb["nodes"][comport]["index"],
				}
			})
			del self.LocalUsbDb["nodes"][comport]

	def RemoveDisconnected(self, removed_ports_list):
		for com in removed_ports_list:
			self.RemoveGateway(com)
			self.RemoveNodes(com)

	def ConnectNewComDevices(self, added_ports_list):
		for com in added_ports_list:
			status = self.HW.SingleConnect(com, 115200)
			if status is True:
				info = self.HW.GetDeviceType(com)
				device_type = info["device_type"]
				if device_type is None:
					self.HW.SingleDisconnect(com)
				else:
					if device_type == "2020":
						info = self.HW.GetDeviceAdditional(com)
						if "type" in info and "index" in info:
							if info["type"] == "GATEWAY":
								self.LocalUsbDb["gateways"][com] = {
									"port": com,
									"index": info["index"],
									"remotes": {}
								}
								print("NewGateway")
								self.EmitEvent({
									"event": "USBDeviceConnectedHandler",
									"data": {
										"type": "GATEWAY",
										"port": com,
										"index": info["index"],
									}
								})
								data_nodes = self.HW.GetNodeList(com)
								if data_nodes is not None:
									for node in data_nodes["list"]:
										device_id = node["device_id"]
										self.LocalUsbDb["gateways"][com]["remotes"][device_id] = {
											"status": node["status"],
											"info": None
										}
							elif info["type"] == "NODE":
								self.LocalUsbDb["nodes"][com] = {
									"port": com,
									"index": info["index"],
									"sensors": None
								}
								self.EmitEvent({
									"event": "USBDeviceConnectedHandler",
									"data": {
										"type": "NODE",
										"port": com,
										"index": info["index"],
									}
								})
					else:
						self.HW.SingleDisconnect(com)

	def CheckSerialConnections(self):
		current_ports = []
		data = self.HW.ListSerialComPorts()
		local_db_ports = self.LocalUsbDb["comports"]
		for comp in data:
			current_ports.append(comp["port"])
		added, removed = co_common.DiffArray(local_db_ports, current_ports)
		if added is not None or removed is not None:
			self.LocalUsbDb["comports"] = current_ports
		return added, removed

	def RegisterHardware(self, hw_layer):
		self.HW = hw_layer

	def SystemInfoHandler(self, sock, packet):
		print("SystemInfoHandler {0}".format(packet))
		is_async = packet["payload"]["async"]
		data = {
			"event": "SystemInfoHandler",
			"data": {
				"system": {
					"local_db": self.LocalUsbDb
				}
			}
		}
		if is_async is True:
			self.EmitEvent(data)
			return None
		else:
			return {
				"system": {
					"local_db": self.LocalUsbDb
				}
			}

	def GatewayInfoHandler(self, sock, packet):
		print("GatewayInfoHandler {0}".format(packet))
		is_async = packet["payload"]["async"]
		data = {
			"event": "GatewayInfoHandler",
			"data": {
				"gateway": self.LocalUsbDb["gateways"]
			}
		}
		if is_async is True:
			self.EmitEvent(data)
			return None
		else:
			return self.LocalUsbDb["gateways"]
	
	def SerialListHandler(self, sock, packet):
		print("SerialListHandler {0}".format(packet))
		is_async = packet["payload"]["async"]
		data = self.HW.ListSerialComPorts()
		if is_async is True:
			self.EmitEvent({
				"event": "SerialListHandler",
				"data": data
			})
			return None
		else:
			return data
	
	def ConnectHandler(self, sock, packet):
		print("ConnectHandler {0}".format(packet))
		is_async 	= packet["payload"]["async"]
		port 		= packet["payload"]["port"]
		baudrate 	= packet["payload"]["baudrate"]

		print("Connect serial port {0} baudrate {1}".format(port, baudrate))
		status = self.HW.SingleConnect(port, baudrate)
		if status is False:
			print("Connection FAILED.")
		else:
			print("Connection SUCCESS.")
		
		data = {
			'event': "ConnectHandler",
			'data': status
		}

		if is_async is True:
			self.EmitEvent(data)
			return None
		else:
			return data
	
	def DisconnectHandler(self, sock, packet):
		print("DisconnectHandler {0}".format(packet))
		is_async 	= packet["payload"]["async"]
		port 		= packet["payload"]["port"]

		print("Disconnect serial port {0}".format(port))
		status = self.HW.SingleDisconnect(port)
		if status is False:
			print("Disconnect FAILED.")
		else:
			print("Disconnect SUCCESS.")
		
		data = {
			'event': "DisconnectHandler",
			'data': status
		}

		if is_async is True:
			self.EmitEvent(data)
			return None
		else:
			return data
	
	def SetWorkingPortHandler(self, sock, packet):
		print("SetWorkingPortHandler {0}".format(packet))
		is_async 			= packet["payload"]["async"]
		self.WorkingPort 	= packet["payload"]["port"]

		if is_async is True:
			self.EmitEvent({
				'event': "SetWorkingPortHandler",
				'data': True
			})
			return None
		else:
			return {}
	
	def GetDeviceTypeHandler(self, sock, packet):
		is_async = packet["payload"]["async"]
		ans = self.HW.GetDeviceType(self.WorkingPort)
		if is_async is True:
			self.EmitEvent({
				'event': "GetDeviceTypeHandler",
				'data': ans
			})
			return None
		else:
			return ans
	
	def GetDeviceAdditionalHandler(self, sock, packet):
		is_async = packet["payload"]["async"]
		ans = self.HW.GetDeviceAdditional(self.WorkingPort)
		if is_async is True:
			self.EmitEvent({
				'event': "GetDeviceAdditionalHandler",
				'data': ans
			})
			return None
		else:
			return ans
	
	def SetNodeAddressHandler(self, sock, packet):
		print("SetNodeAddressHandler {0}".format(packet))
		is_async = packet["payload"]["async"]
		address = packet["payload"]["address"]
		if address is not None:
			ans = self.HW.SetNodeAddress(self.WorkingPort, address)
			self.LocalUsbDb["nodes"][self.WorkingPort]["index"] = address
			if is_async is True:
				self.EmitEvent({
					'event': "SetNodeAddressHandler",
					'data': ans
				})
				return None
			else:
				return ans
		else:
			return None
	
	def GetNodeAddressHandler(self, sock, packet):
		is_async = packet["payload"]["async"]
		ans = self.HW.GetNodeAddress(self.WorkingPort)
		if is_async is True:
			self.EmitEvent({
				'event': "GetNodeAddressHandler",
				'data': ans
			})
			return None
		else:
			return ans
	
	def GetNodeInfoHandler(self, sock, packet):
		is_async = packet["payload"]["async"]
		ans = self.HW.GetNodeInfo(self.WorkingPort)
		if is_async is True:
			self.EmitEvent({
				'event': "GetNodeInfoHandler",
				'data': ans
			})
			return None
		else:
			return ans
	
	def GetNodesMapHandler(self, sock, packet):
		is_async = packet["payload"]["async"]
		ans = (self.HW.GetNodesMap(self.WorkingPort))
		if is_async is True:
			self.EmitEvent({
				'event': "GetNodesMapHandler",
				'data': ans
			})
			return None
		else:
			return ans
	
	def AddNodeIndexHandler(self, sock, packet):
		is_async = packet["payload"]["async"]
		index = packet["payload"]["index"]
		if index is not None:
			ans = self.HW.AddNodeIndex(self.WorkingPort, index)
			if ans is not None:
				#TODO - Update DB with new registered sensor id
				if ans["status"] is True:
					self.LocalUsbDb["gateways"][self.WorkingPort]["remotes"][index] = {
						"status": 0,
						"info": None
					}
				if is_async is True:
					self.EmitEvent({
						'event': "AddNodeIndexHandler",
						'data': ans
					})
					return None
				else:
					return ans
			else:
				return None
		else:
			return None
	
	def DelNodeIndexHandler(self, sock, packet):
		is_async = packet["payload"]["async"]
		index = packet["payload"]["index"]
		if index is not None:
			ans = self.HW.DelNodeIndex(self.WorkingPort, index)
			if ans is not None:
				#TODO - Update DB with unregistered sensor id
				if ans["status"] is True:
					del self.LocalUsbDb["gateways"][self.WorkingPort]["remotes"][index]
				if is_async is True:
					self.EmitEvent({
						'event': "DelNodeIndexHandler",
						'data': ans
					})
					return None
				else:
					return ans
			else:
				return None
		else:
			return None
	
	def SetRemoteNodeAddressHandler(self, sock, packet):
		is_async = packet["payload"]["async"]
		address = packet["payload"]["address"]
		node_id = packet["payload"]["node_id"]
		if address is not None and node_id is not None:
			ans = self.HW.SetRemoteNodeAddress(self.WorkingPort, node_id, address)
			if is_async is True:
				self.EmitEvent({
					'event': "SetRemoteNodeAddressHandler",
					'data': ans
				})
				return None
			else:
				return ans
		else:
			return None
	
	def GetRemoteNodeAddressHandler(self, sock, packet):
		is_async = packet["payload"]["async"]
		node_id = packet["payload"]["node_id"]
		if node_id is not None:
			ans = self.HW.GetRemoteNodeAddress(self.WorkingPort, node_id)
			if is_async is True:
				self.EmitEvent({
					'event': "GetRemoteNodeAddressHandler",
					'data': ans
				})
				return None
			else:
				return ans
		else:
			return None

	def GetAvailableIndexesHandler(self, sock, packet):
		pass

	def GetNodeListHandler(self, sock, packet):
		print("GetNodeListHandler {0}".format(packet))
		is_async = packet["payload"]["async"]
		ans = self.HW.GetNodeList(self.WorkingPort)
		if ans is not None:
			for node in ans["list"]:
				device_id = node["device_id"]
				if device_id in self.LocalUsbDb["gateways"][self.WorkingPort]["remotes"]:
					self.LocalUsbDb["gateways"][self.WorkingPort]["remotes"][device_id]["status"] = node["status"]
				else:
					self.LocalUsbDb["gateways"][self.WorkingPort]["remotes"][device_id] = {
						"status": node["status"],
						"info": None
					}
			data = {
				'event': "GetNodeListHandler",
				'data': ans
			}
			if is_async is True:
				self.EmitEvent(data)
				return None
			else:
				return ans
		else:
			data = {
				'event': "GetNodeListHandler",
				'data': {
					"list": []
				}
			}
			if is_async is True:
				self.EmitEvent(data)
				return None
			else:
				return {
					"list": []
				}
	
	def GetRemoteNodeInfoHandler(self, sock, packet):
		print("GetRemoteNodeInfoHandler {0}".format(packet))
		is_async = packet["payload"]["async"]
		node_id  = packet["payload"]["node_id"]
		ans = self.HW.GetRemoteNodeInfo(self.WorkingPort, node_id)
		if ans is not None:
			device_type, info = self.Translator.Translate(ans["packet"])
			data = {
				'event': "GetRemoteNodeInfoHandler",
				'data': info
			}

			if is_async is True:
				self.EmitEvent(data)
				return None
			else:
				return info
		else:
			return {
				"error": True
			}
	
	def GetRemoteNodeDataHandler(self, sock, packet):
		print("GetRemoteNodeDataHandler {0}".format(packet))
		is_async 	 = packet["payload"]["async"]
		node_id  	 = packet["payload"]["node_id"]
		sensor_index = packet["payload"]["sensor_index"]

		ans = self.HW.GetRemoteNodeData(self.WorkingPort, node_id, sensor_index)
		if ans is not None:
			info = self.Translator.Translate(ans["packet"])
			data = {
				'event': "GetRemoteNodeDataHandler",
				'data': info
			}

			if is_async is True:
				self.EmitEvent(data)
				return None
			else:
				return info
		else:
			return {
				"error": True
			}
	
	def SetRemoteNodeDataHandler(self, sock, packet):
		print("GetRemoteNodeDataHandler {0}".format(packet))
		is_async 	 = packet["payload"]["async"]
		node_id  	 = packet["payload"]["node_id"]
		sensor_index = packet["payload"]["sensor_index"]
		sensor_value = packet["payload"]["sensor_value"]

		ans = self.HW.SetRemoteNodeData(self.WorkingPort, node_id, sensor_index, sensor_value)
		if ans is not None:
			info = self.Translator.Translate(ans["packet"])
			data = {
				'event': "SetRemoteNodeDataHandler",
				'data': info
			}

			if is_async is True:
				self.EmitEvent(data)
				return None
			else:
				return info
		else:
			return {
				"error": True
			}
	
	def SelectSensorsHandler(self, sock, packet):
		print("SelectSensorsHandler {0}".format(packet))
		is_async = packet["payload"]["async"]
		db_data = self.DB.GetSensors()
		if db_data is not None:
			if is_async is True:
				self.EmitEvent({
					'event': "SelectSensorsHandler",
					'data': db_data
				})
				return None
			else:
				return db_data
		else:
			return None
	
	def SelectSensorHistoryHandler(self, sock, packet):
		print("SelectSensorHistoryHandler {0}".format(packet))
		is_async = packet["payload"]["async"]
		sensor_id = packet["payload"]["sensor_id"]

		db_info = self.DB.GetSensorHistory(sensor_id)
		if is_async is True:
			self.EmitEvent({
				'event': "SelectSensorHistoryHandler",
				'data': db_info
			})
			return None
		else:
			return db_info
	
	def SelectSensorsByDeviceHandler(self, sock, packet):
		print("SelectSensorsByDeviceHandler {0}".format(packet))
		is_async = packet["payload"]["async"]
		device_id = packet["payload"]["device_id"]

		db_info = self.DB.GetSensorByDeviceId(device_id)
		if is_async is True:
			self.EmitEvent({
				'event': "SelectSensorsByDeviceHandler",
				'data': db_info
			})
			return None
		else:
			return db_info
	
	def UpdateSensorInfoHandler(self, sock, packet):
		print("UpdateSensorInfoHandler {0}".format(packet))
		is_async = packet["payload"]["async"]
		sensor_id = packet["payload"]["sensor_id"]
		sensor_name = packet["payload"]["sensor_name"]
		sensor_description = packet["payload"]["sensor_description"]

		status = self.DB.UpdateSensorInfo(sensor_id, sensor_name, sensor_description)
		if status is True:
			if is_async is True:
				self.EmitEvent({
					'event': "UpdateSensorInfoHandler",
					'data': status
				})
				return None
			else:
				return status
		else:
			return None
	
	def SelectDevicesHandler(self, sock, packet):
		print("SelectDevicesHandler {0}".format(packet))
		is_async = packet["payload"]["async"]

		db_data = self.DB.GetDeviceList()
		if is_async is True:
			self.EmitEvent({
				'event': "SelectDevicesHandler",
				'data': db_data
			})
			return None
		else:
			return db_data
	
	def InsertDeviceHandler(self, sock, packet):
		print("InsertDeviceHandler {0}".format(packet))
		is_async = packet["payload"]["async"]
		device_type = packet["payload"]["device_type"]
		device_id = packet["payload"]["device_id"]

		if self.DB.SensorExist(device_id) is True:
			return None

		if device_type == 50:
			sensor_type_map = {
				1: ["Temperature", ""],
				2: ["Humidity", ""],
				3: ["Movement", "PIR"],
				4: ["Switch", "LED"]
			}
			for idx in range(1,5):
				self.DB.InsertSensor({
					"type": idx,
					"index": idx,
					"device_id": device_id,
					"device_type": device_type,
					"name": sensor_type_map[idx][0],
					"description": sensor_type_map[idx][1]
				})
			if is_async is True:
				self.EmitEvent({
					'event': "InsertDeviceHandler",
					'data': {
						"done": True
					}
				})
				return None
			else:
				return {
					"done": True
				}
		else:
			return None
	
	def DeleteDeviceHandler(self, sock, packet):
		print("DeleteDeviceHandler {0}".format(packet))
		is_async = packet["payload"]["async"]
		device_id = packet["payload"]["device_id"]

		if self.DB.SensorExist(device_id) is False:
			return None
		
		self.DB.DeleteDevice(device_id)
		if is_async is True:
			self.EmitEvent({
				'event': "DeleteDeviceHandler",
				'data': {
					"done": True
				}
			})
			return None
		else:
			return {
				"done": True
			}
	
	'''
	Recieve UART packet (pay attention NOT nrf)
	[direction, op_code, content_length, [0...15]]
	'''
	def AsyncDataArrived(self, path, packet):
		# 1. Data from sensors (NRF protocol)
		# 2. Data from Gateway (Other protocol)
		if len(packet) > 3:
			opcode = packet[1]
			payload_size = packet[2]
			if opcode == 112:
				device_id = packet[3]
				# print("DeviceCommunicationLostHandler")
				self.EmitEvent({
					"event": "DeviceCommunicationLostHandler",
					"data": device_id
				})
				self.LocalUsbDb["gateways"][path]["remotes"][device_id]["status"] = 0
			elif opcode == 100:
				if payload_size == 16:
					device_type, info = self.Translator.Translate(packet[3:])
					if info is not None:
						device_id = int(info["device_id"])
						timestamp = int(time.time())
						info["timestamp"] = timestamp
						info["port"] = path
						# print("NRFPacket")
						# Emit this event to browser
						self.EmitEvent({
							"event": "NRFPacket",
							"data": info
						})
						
						if device_type == 50:
							# Update sensor values for this gateway
							if path in self.LocalUsbDb["gateways"]:
								if device_id in self.LocalUsbDb["gateways"][path]["remotes"]:
									self.LocalUsbDb["gateways"][path]["remotes"][device_id]["info"] = info
									self.LocalUsbDb["gateways"][path]["remotes"][device_id]["status"] = 1
							
							db_info = self.DB.GetSensorByDeviceId(device_id)
							self.DB.InsertSensorValue({
								'id': db_info[0]["id"],
								'device_id': device_id,
								'value': float(info["sensors"][0]["value"]),
								'timestamp': timestamp
							})
							self.DB.InsertSensorValue({
								'id': db_info[1]["id"],
								'device_id': device_id,
								'value': float(info["sensors"][1]["value"]),
								'timestamp': timestamp
							})
							self.DB.InsertSensorValue({
								'id': db_info[2]["id"],
								'device_id': device_id,
								'value': float(info["sensors"][2]["value"]),
								'timestamp': timestamp
							})
							self.DB.InsertSensorValue({
								'id': db_info[3]["id"],
								'device_id': device_id,
								'value': float(info["sensors"][3]["value"]),
								'timestamp': timestamp
							})
import _thread
import socket
import struct
from mks import mks_config

class Broadcaster():
	def __init__(self):
		self.Config 		= mks_config.NodeConfig()
		self.ServerSocket	= None
		self.ClientSocket  	= None
		self.DataSize		= 1024
		self.Port 			= 0
		self.ServerRunning 	= True
	
	def Run(self):
		_thread.start_new_thread(self.ServerThread, ())
	
	def Stop(self):
		self.ServerRunning = False

	def ServerThread(self):
		status = self.Config.Load()
		if status is False:
			return
		
		self.Port = self.Config.Application["server"]["broadcast"]["port"]

		MULTICAST_TTL = 2
		self.ClientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		self.ClientSocket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, MULTICAST_TTL)

		self.ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		self.ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.ServerSocket.bind(('', self.Port))

		MCAST_GRP = '224.1.1.1'
		mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
		self.ServerSocket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

		print("(ServerThread)# Start service ({0})".format(self.Port))
		while self.ServerRunning is True:
			try:
				data, addr = self.ServerSocket.recvfrom(self.DataSize)
				print("(ServerThread)# {0} {1}".format(data, addr))
			except Exception as e:
				print("(ServerThread)# {0}".format(str(e)))
	
	def Send(self, data):
		buffer = str.encode(data)
		if self.ClientSocket is not None:
			self.ClientSocket.sendto(buffer, ('224.1.1.1', self.Port))
		return True
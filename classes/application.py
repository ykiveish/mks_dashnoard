import os
import json
import time
import _thread

from core import co_application
from core import co_multicaster

class Application(co_application.ApplicationLayer):
	def __init__(self):
		co_application.ApplicationLayer.__init__(self)
        # REST Handlers
		self.WSHandlers["echo"] 		= self.EchoHandler
		self.WSHandlers["nodes"] 		= self.NodesHandler

		self.Working 					= False
		self.ErrorCallback 				= None

		self.Users 						= co_multicaster.MulticasterUsers()
		self.Users.UserEventsCallback 	= self.UsersEventHandler
	
	def WebErrorEvent(self):
		self.FatalError = True
		if self.ErrorCallback is not None:
			self.ErrorCallback()
	
	def UsersEventHandler(self, name, info):
		print("(UsersEventHandler)# {0}".format(name))
		if "update" in name:
			return
		
		self.EmitEvent({
			'event': "nodes",
			'data': {
				"type": name,
				"data": {}
			}
		})
	
	def Worker(self):
		self.Working = True
		# Nodes live database
		self.Users.Run()

		while self.Working is True:
			try:
				time.sleep(5)
			except Exception as e:
				print("Worker Exception: {0}".format(e))

		self.Users.Stop()
	
	def EchoHandler(self, sock, packet):
		print("EchoHandler {0}".format(packet))
		is_async = packet["payload"]["async"]
		
		if is_async is True:
			return "Echo ASYNC"
		else:
			return "Echo SYNC"
	
	def NodesHandler(self, sock, packet):
		print("NodesHandler {0}".format(packet))

		return {
			"users": self.Users.GetUsers()
		}

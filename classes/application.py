import os
import json
import time
import _thread

from core import co_application

class Application(co_application.ApplicationLayer):
	def __init__(self):
		co_application.ApplicationLayer.__init__(self)
        
		self.WSHandlers["echo"] = self.EchoHandler
		self.Working = False
	
	def Start(self):
		_thread.start_new_thread(self.Worker, ())
	
	def Worker(self):
		self.Working = True
		while self.Working is True:
			try:
				time.sleep(5)
			except Exception as e:
				print("Worker Exception: {0}".format(e))
	
	def EchoHandler(self, sock, packet):
		print("EchoHandler {0}".format(packet))
		is_async = packet["payload"]["async"]
		
		if is_async is True:
			return "Echo ASYNC"
		else:
			return "Echo SYNC"

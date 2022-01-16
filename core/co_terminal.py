from core import co_definitions
from mks import mks_config

class TerminalLayer(co_definitions.ILayer):
	def __init__(self):
		co_definitions.ILayer.__init__(self)
		self.ProcessRunning = True
		self.Handlers 	= None
		self.Config 	= mks_config.NodeConfig()
	
	def Run(self):
		status = self.Config.Load()
		if status is False:
			print("ERROR - Wrong configuration format")
			return False
		while(self.ProcessRunning is True):
			try:
				raw  	= input('> ')
				data 	= raw.split(" ")
				cmd  	= data[0]
				params 	= data[1:]

				if self.Handlers is not None:
					if cmd in self.Handlers:
						self.Handlers[cmd](params)
					else:
						if cmd not in [""]:
							print("unknown command")
			except Exception as e:
				print("Terminal Exception {0}".format(str(e)))
		return True
	
	def Exit(self):
		self.ProcessRunning = False

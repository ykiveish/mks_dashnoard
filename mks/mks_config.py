import os
import json

from core import co_file

class NodeConfig():
	def __init__(self):
		self.MKSEnvPath 	= os.path.join(os.environ['HOME'],"mks")
		self.Application 	= None
		self.Terminal 		= None
		self.Logger 		= None

	def Load(self):
		strJson = co_file.File().Load("config.json")
		if (strJson is None or len(strJson) == 0):
			return False
		
		try:
			config = json.loads(strJson)
			self.Application = config["application"]
			self.Terminal 	 = config["terminal"]
			self.Logger 	 = config["logger"]
		except Exception as e:
			return False
		
		return True

import subprocess
from core import co_definitions
from core import co_terminal
from core import co_file

class Terminal(co_terminal.TerminalLayer):
	def __init__(self):
		co_terminal.TerminalLayer.__init__(self)
		self.Application    = None # TODO - Move to CORE
		self.Handlers       = {
			"help":         self.HelpHandler,
			"echo":    		self.EchoHandler,
			"app":			self.AppHandler,
			"exit":			self.ExitHandler,
		}
	
    # TODO - Move to CORE
	def UpdateApplication(self, data):
		if self.Application is not None:
			self.Application.EmitEvent(data)

	def HelpHandler(self, data):
		pass

	def EchoHandler(self, data):
		pass

	def AppHandler(self, data):
		# Generate command
		cmd = '"c:\program files (x86)\Google\Chrome\Application\chrome.exe" --window-size=1400,800 -incognito --app="http://{0}:{1}"'.format(str(self.Config.Application["server"]["address"]["ip"]), str(self.Config.Application["server"]["web"]["port"]))
		objFile = co_file.File()
		objFile.Save("ui.cmd", cmd)
		subprocess.call(["ui.cmd"])

	def ExitHandler(self, data):
		self.Exit()

	def Close(self):
		pass

from core import co_definitions
from core import co_terminal

class Terminal(co_terminal.TerminalLayer):
	def __init__(self):
		co_terminal.TerminalLayer.__init__(self)
		self.Application    = None # TODO - Move to CORE
		self.Handlers       = {
			"help":         self.HelpHandler,
			"echo":    		self.EchoHandler,
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

	def ExitHandler(self, data):
		self.Exit()

	def Close(self):
		pass

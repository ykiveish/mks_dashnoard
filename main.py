#!/usr/bin/python
import signal
import argparse

from classes import terminal
from classes import application

def signal_handler(signal, frame):
	pass
	
def main():
	signal.signal(signal.SIGINT, signal_handler)

	parser = argparse.ArgumentParser(description='Execution module\n Example: python.exe main.py')
	parser.add_argument('-v', '--version', action='store_true',
			help='Version')
	parser.add_argument('-verb', '--verbose', action='store_true',
			help='Print messages')
	
	args = parser.parse_args()

	cli = terminal.Terminal()
	app = application.Application()

	app.Run()
	cli.Run() # Blocking
	
	cli.Close()
	print("Bye.")

if __name__ == "__main__":
    main()

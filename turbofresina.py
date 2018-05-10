#!/usr/bin/env python3
"""
    T.U.R.B.O.F.R.E.S.A.
    Turboaggeggio Utile alla Rimorzione di Byte Obrobriosi e di abominevoli
    File da dischi rigidi Riciclati ed altri Elettronici Sistemi di
    Accumulazione (semi)permanente di dati.
    Copyright (C) 2018  Hyd3L

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import sys
import getpass
import datetime
import threading
import subprocess

# Path of the log file
LOG_PATH = '/home/' + getpass.getuser() + '/.local/share/turbofresa/log.txt'

# Verbosity levels
ERROR, WARNING, INFO = range(0, 3)
VERBOSITY = INFO


# Function that returns a formatted string with current time
def now():
	return datetime.datetime.now().strftime('[%Y-%m-%d %H:%M:%S] ')


"""
	Console : class for printing errors, warnings and info messages
				to the stdout and into the log file.

	@member printLevel : verbosity level (ERROR, WARNING or INFO)
	@member logFile    : the log file pointer

	@method info : prints info msg to stdout and to the logFile
	@method warn : prints warning to stdout and to the logFile
	@method err  : prints error to stdout and to the logFile
"""


class Console(object):
	def __init__(self):
		self.printLevel = VERBOSITY
		try:
			self.logFile = open(LOG_PATH, "a")
		except IOError:
			print("error: Permission denied. Log file couldn't be created.")
			sys.exit(1)

	def info(self, msg, to_std_out=True):
		if self.printLevel >= INFO:
			if to_std_out is True:
				print("info: " + msg)
			self.logFile.write(now() + "info: " + msg + '\n')

	def proc(self, msg, to_std_out=True):
		if to_std_out is True:
			print("proc: " + msg)
		self.logFile.write(now() + "proc: " + msg + '\n')

	def warn(self, msg, to_std_out=True):
		if self.printLevel >= WARNING:
			if to_std_out is True:
				print("warning: " + msg)
			self.logFile.write(now() + "warning: " + msg + '\n')

	def error(self, msg, to_std_out=True):
		if self.printLevel >= ERROR:
			if to_std_out is True:
				print("error: " + msg)
			self.logFile.write(now() + "error: " + msg + '\n')

	def exit(self):
		self.logFile.close()


# Initialize log
log = Console()


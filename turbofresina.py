#!/usr/bin/env python3
"""
    T.U.R.B.O.F.R.E.S.I.N.A
    Turboaggeggio Utile alla Rimorzione di Byte Obrobriosi e di abominevoli
    File da dischi rigidi Riciclati ed altri Elettronici Sistemi di
    Immagazzinamento (semi)permanente di dati Necessariamente Automatizzato.
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
import datetime
import threading
import subprocess
import argparse  # @quel_tale will you finally stop smashing my nuts?
from getpass import getuser

# Path of the log file
LOG_PATH = '/home/' + getuser() + '/.local/share/turbofresa/log.txt'

# Verbosity levels
ERROR, WARNING, INFO = range(0, 3)
VERBOSITY = INFO


def now():
	"""
		:return: a formatted string containing the current date and time
	"""
	return datetime.datetime.now().strftime('[%Y-%m-%d %H:%M:%S] ')


class Console(object):
	"""
		Class that handles the log file.
	"""
	def __init__(self):
		self.printLevel = VERBOSITY
		try:
			self.logFile = open(LOG_PATH, "a")
		except IOError:
			print("error: Permission denied. Log file couldn't be created.")
			sys.exit(34)

	def info(self, msg, to_std_out=True):
		if self.printLevel >= INFO:
			if to_std_out is True:
				print("info: " + msg)
			self.logFile.write(now() + "info: " + msg + '\n')

	def task(self, msg, to_std_out=True):
		if to_std_out is True:
			print("task: " + msg)
		self.logFile.write(now() + "task: " + msg + '\n')

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


def secure_exit(status=0):
	log.exit()
	sys.exit(status)


def detect_os() -> str:
	"""
		Detects the hard drives connected to the machine
		:return: a list containing '/dev/sdX' entries
	"""
	os_disk = os.popen('df | grep /dev/sd | cut -b -8').read().split('\n')[0]
	return os_disk


def detect_disks() -> list:
	"""
		Detects the hard drives connected to the machine
		:return: a list containing '/dev/sdX' entries
	"""
	os_disk = detect_os()
	disks = list()
	lsblk = os.popen('lsblk | grep sd').read()
	for line in lsblk:
		if line.startswith('s'):
			path = '/dev/'+line[0]
			if path == os_disk:
				print("Skipping mounted drive: " + path)
				continue
			disks.append(path)
	return disks


class Task(threading.Thread):
	"""
		Class that handles the cleaning operation of a disk
	"""

	def __init__(self, hdd):
		"""
			:param hdd: A '/dev/sdX' formatted string
		"""
		threading.Thread.__init__(self)
		self.disk_path = hdd
		self.drive_name = hdd.split('/')[2]

	def run(self):
		log.task("Started cleaning %s" % self.drive_name)
		subprocess.run(['sudo', 'badblocks', '-w', '-t', '0x00', '-o', self.drive_name, self.disk_path])
		result = os.popen('cat %s' % self.drive_name).read()
		if result == "":
			log.task("%s successfully cleaned.")
			subprocess.run(['rm', self.drive_name])
		else:
			log.task("%s is broken.")


def main():
	parser = argparse.ArgumentParser(description='Automatically drill every single connected hard drive.')
	parser.add_argument('-s', '--shutdown', help="Shutdown the machine when everything is done.")
	parser.set_defaults(shutdown=False)
	args = parser.parse_args()

	print("===> Detecting connected hard drives.")
	hdds = detect_disks()
	tasks = list()

	for d in hdds:
		tasks.append(Task(d))

	print("===> Cleaning disks")
	for t in tasks:
		t.start()

	for t in tasks:
		t.join()

	if args.shutdown is True:
		log.info("System halted by the user.")
		subprocess.run(['shutdown', '+1'])
	print("Done.")


if __name__ == '__main__':
	main()
	secure_exit()

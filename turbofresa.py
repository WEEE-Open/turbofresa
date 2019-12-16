#!/usr/bin/env python3
"""
    T.U.R.B.O.F.R.E.S.A
    Turboaggeggio Utile alla Rimorzione di Byte Obrobriosi e di abominevoli
    File da dischi rigidi Riciclati ed altri Elettronici Sistemi di
    Archiviazione di dati.
    Contributors:
        Hyd3L
        e-caste

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
import json
import logging  # TODO: Add log messages
from multiprocessing import Process
import subprocess as sp
import argparse
import smartctl_parser
from pytarallo import Tarallo
from dotenv import load_dotenv

__version__ = '1.3'

# Run parameters
quiet = None
simulate = None


def ask_confirm():
    """
    Asks the user if (s)he is sure of what (s)he's doing.
    """
    while True:
        user_response = input("Are you 100% sure of what you're about to do? [N/y] ")
        if user_response.lower() == 'y':
            break
        elif user_response.lower() == 'n':
            exit(0)
        else:
            print("Unrecognized response... Asking again nicely.")

class Task(Process):
    """
    Disk cleaning process
    """
    def __init__(self, disk):
        """
        :param disk: Disk object
        """
        super().__init__(self)
        self.disk = disk

    def run(self):
        """
        This is the crucial part of the program.
        Here badblocks writes a stream of 0x00 bytes on the hard drive.
        After the writing process, it reads every blocks to ensure that they are actually 0x00 bytes.
        Bad blocks are eventually written in a txt file named as HDDXXX or sdX in case of failures
        while retrieving the HDD code from T.A.R.A.L.L.O.
        If this file is empty, then the disk is good to go, otherwise it'll be kept
        and the broken hard drive is reported into the log file and informations
        are written to the T.A.R.A.L.L.O. database.
        """
        exit_code = sp.Popen(['sudo', 'badblocks', '-w', '-t', '0x00', '-o', self.disk.code, self.disk.dev]).returncode
        # result = os.popen('cat %s' % self.disk.code).read()
        # if result == "":
        if exit_code != 0:
            sp.run(['rm', '-f', self.disk.code])
        else:
            # TODO: Write on tarallo that the hard drive is broken
            # Write it in the turbofresa log file as well
            pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Automatically drill every single connected hard drive.')
    parser.add_argument('-s', '--shutdown', action='store_true', help='Shutdown the machine when everything is done.')
    parser.add_argument('-q', '--quiet', action='store_true', help='Run in background and suppress stdout.')
    parser.add_argument('-d', '--dry', action='store_true', help='Launch simulation.')
    parser.add_argument('--version', '-V', action='version', version='%(prog)s v.' + __version__)
    parser.set_defaults(shutdown=False)
    parser.set_defaults(quiet=False)
    parser.set_defaults(dry=False)
    args = parser.parse_args()
    quiet = args.quiet
    simulate = args.dry

    # ask_confirm()
    if not quiet:
        print("===> Detecting connected hard drives.")
    disks = smartctl_parser.main()
    tasks = []

    # Tarallo connection
    load_dotenv()
    instance = Tarallo.Tarallo(os.getenv("TARALLO_URL"), os.getenv("TARALLO_TOKEN"))

    # Adding disks to clean only if into T.A.R.A.L.L.O. database
    for d in disks:
        # TODO: add a method that adds disk to tarallo, create a Disk object (or a Tarallo.Item)
        # TODO: pass that to every other method from here onward
        disk_code = instance.get_codes_by_feature('sn', d['sn'])
        if len(disk_code) > 1:
            print("Multiple disks in the T.A.R.A.L.L.O. database corresponding to the serial number: " + d['sn'])
        elif len(disk_code) == 0:
            print("No disk in the T.A.R.A.L.L.O. database corresponding to the serial number: " + d['sn'])
        else:
            tasks.append(Task(d))
        
    if not quiet:
        print("===> Cleaning disks")
    for t in tasks:
        if not simulate:
            t.start()
        else:
            if not quiet:
                print("Started cleaning")

    for t in tasks:
        if not simulate:
            t.join()
        else:
            if not quiet:
                print("Ended cleaning")

    if args.shutdown is True:
        if not simulate:
            sp.run(['sudo', 'shutdown'])
        else:
            if not quiet:
                print("System halted by the user.")
    if not quiet:
        print("Done.")
    exit(0)

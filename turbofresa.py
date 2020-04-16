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
from pytarallo import Tarallo, Errors, Item
from dotenv import load_dotenv

__version__ = '1.3'

# Run parameters
quiet = None
simulate = None

tarallo_instance = None


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
        exit_code = sp.Popen(['sudo', 'badblocks', '-w', '-t', '0x00', '-o',
                              self.disk['code'], "/dev/"+self.disk['mount_point']]).returncode
        # result = os.popen('cat %s' % self.disk.code).read()
        # if result == "":
        if exit_code != 0:
            sp.run(['rm', '-f', self.disk["code"]])
            return True
        else:
            # TODO: Write on tarallo that the hard drive is broken
            # Write it in the turbofresa log file as well
            global tarallo_instance
            disk['features']['smart-data'] = smartctl_parser.SMART.fail
            add_to_tarallo_broken(tarallo_instance, disk['features'])
            return False


def add_to_tarallo(instance: Tarallo.Tarallo, disk: dict) -> bool:
    """
    Adds disk to Tarallo database
    :param instance: Tarallo instance where to add the disk
    :param disk: disk to add to the database
    :return: True if added successfully or it was already present,
        False if there were multiple instances of it in the database
    """

    print("===> Searching the T.A.R.A.L.L.O. databse for disk with serial number {}".format(disk['sn']))
    disk_code = instance.get_codes_by_feature('sn', disk['sn'])

    if len(disk_code) > 1:
        print("Multiple disks in the database corresponding to the serial number: " + disk['sn'])
        print("Won't proceed until conflict is solved")
        return False
    elif len(disk_code) == 1:
        print(f"Disk with serial number {disk['sn']} already present in the database"
              f"with the code {disk_code}")
        item = instance.get_item(disk_code)
        for key, value in item.features.items():
            if key == 'smart_data' or key == 'smart_data_long':
                continue
            if value != disk[key]:
                print("There's a conflict in the database for this disk")
                print("Won't proceed until conflict is solved")
                return False
            print("The entry doesn't conflict with the current disk, proceeding anyway")
            return True
    elif len(disk_code) == 0:
        print("No corresponding disk in the database")
        print("===> Adding disk to the database")

    item = Item.Item()
    item.features = disk
    item.location = 'Magazzino'  # TODO: maybe it can be set from config or a better default should be picked

    try:
        instance.add_item(item=item)
        print("Item inserted successfully")
    except Errors.ValidationError:
        print("Item not inserted")
        response = instance.response
        print("HTTP status code:", response.status_code, "\n" + response.json()['message'])
        return False

    print("Successfully added the disk")
    print("Disk code on the Database: " + instance.get_codes_by_feature('sn', disk['sn']))
    return True


def add_to_tarallo_broken(instance: Tarallo.Tarallo, disk: dict) -> bool:
    if disk['smart-data'] != smartctl_parser.SMART.fail:
        print("Not a broken disk")
        return False

    if add_to_tarallo(instance, disk) is False:
        print("Failed to update informations")
        return False

    disk_code = instance.get_codes_by_feature('sn', disk['sn'])
    try:
        instance.update_features(disk_code, disk)
    except Errors.ValidationError:
        print("Failed to update informations")
        return False

    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Automatically drill every single connected hard drive.')
    parser.add_argument('-s', '--shutdown', action='store_true', help='Shutdown the machine when everything is done.')
    parser.add_argument('-q', '--quiet', action='store_true', help='Run in background and suppress stdout.')
    parser.add_argument('-d', '--dry', action='store_true', help='Launch simulation.')
    parser.add_argument('--usb', action='store_true', help='Launch simulation.')
    parser.add_argument('--version', '-V', action='version', version='%(prog)s v.' + __version__)
    parser.set_defaults(shutdown=False)
    parser.set_defaults(quiet=False)
    parser.set_defaults(dry=False)
    parser.set_defaults(usb=False)
    args = parser.parse_args()
    quiet = args.quiet
    simulate = args.dry

    global tarallo_instance

    # ask_confirm()
    if not quiet:
        print("===> Detecting connected hard drives.")

    disks = smartctl_parser.parse_disks(interactive=True, usbdebug=args.usb)
    tasks = []

    # Tarallo connection
    load_dotenv()
    tarallo_instance = Tarallo.Tarallo(os.getenv("TARALLO_URL"), os.getenv("TARALLO_TOKEN"))

    # Adding disks to clean in queue and adding them to T.A.R.A.L.L.O if not present
    for d in disks:
        disk = d['features']

        if add_to_tarallo(tarallo_instance, disk) is False:
            print("Something went wrong with Disk addition to database, skipping to the next one")
            continue

        d['code'] = tarallo_instance.get_codes_by_feature('sn', disk['sn'])
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

#!/usr/bin/env python3
"""
COPY-PASTE of parsers/read_smartctl from https://github.com/WEEE-Open/peracotta
Added only slight modifications to adapt to TURBOFRESA usage
Check commit hystory there for any major change
"""

from enum import Enum

import sys
import os
import subprocess as sp
from math import log10, floor

from InputFileNotFoundError import InputFileNotFoundError

"""
Read "smartctl" output:
"""


class Disk:
    def __init__(self):
        self.type = ""
        self.brand = ""
        self.model = ""
        self.family = ""
        self.wwn = ""
        self.serial_number = ""
        self.form_factor = None
        self.capacity = -1  # n of bytes
        self.human_readable_capacity = ""
        self.rotation_rate = -1
        self.port = PORT.unknown
        self.smart_data_long = SMART.not_available
        self.smart_data = SMART.not_available
        self.dev = ""


class SMART(Enum):
    working = "ok"
    fail = "fail"
    not_available = "not_available"
    old = "old"  # this means "il disco funziona, ma ha quantità inumane di ore di funzionamento alle spalle (perché stava in un server), non sta ancora morendo ma non facciamoci affidamento"


class PORT(Enum):
    unknown = "unknown"
    sata = "sata-ports-n"
    ide = "ide-ports-n"
    miniide = "mini-ide-ports-n"
    # TODO: add more, if they can even be detected


def parse_disks(interactive: bool = False, ignore: list = [], usbdebug: bool = False):
    """
    Parses disks mounted on the current machine
    :param interactive: adds verbosity if set to True
    :param ignore: list of disks to ignore (eg. 'sda', 'sdb', etc.)
    :param usbdebug: allow scan of USB drives (FOR TEST PURPOSES, USE ONLY ON A TEST INSTANCE OF TARALLO!!!)
    :return: list of disks in a TARALLO friendly format
    """

    disks = []
    smartctl_path = os.path.join(os.getcwd(), "smartctl")
    if not os.path.exists(smartctl_path):
        os.makedirs(smartctl_path)

    filegen = os.path.join(os.getcwd(), "smartctl_filegen.sh")
    return_code = sp.run(["sudo", "-S", filegen, smartctl_path]).returncode
    assert (return_code == 0), 'Error during disk detection'

    files = os.listdir(smartctl_path)
    for filename in files:
        if "smartctl-dev-" in filename:

            # Ignoring disks pointed on call
            ignored = False
            for mount_point in ignore:
                if mount_point in filename:
                    ignored = True
                    break
            if ignored is True:
                if interactive is True:
                    print("Disk mounted at /dev/"+mount_point+" ignored")
                os.remove(os.path.join(smartctl_path, filename))
                continue

            # File reading
            try:
                with open(os.path.join(smartctl_path, filename), 'r') as f:
                    output = f.read()
            except FileNotFoundError:
                raise InputFileNotFoundError(smartctl_path)

            # Checks if it's a valid disk
            # If usbdebug is True, the disk is filled with dummy informations
            disk = read_smartctl(output)
            if not check_complete(disk):
                if usbdebug is True:
                    disk = dummy_disk(disk)
                else:
                    if interactive:
                        print(f"{filename} does not contain disk information, was it a USB stick?")
                    continue

            disk.dev = filename.split("smartctl-dev-")[1].split(".txt")[0]

            old_filename = os.path.join("smartctl/", filename)
            new_filename = os.path.join("smartctl/", disk.serial_number) + ".txt"
            os.rename(old_filename, new_filename)

            disks.append(disk)

    if len(disks) >= 1:
        return tarallo_conversion(disks)
    return []


def dummy_disk(disk=Disk()):
    """
    Creates a dummy disk or, if passed, fills a disk with dummy information where needed
    """
    from random import choice
    from string import digits

    dummy = Disk()

    dummy.smart_data = SMART.working
    dummy.brand = "USB_TEST"
    dummy.model = "TEST"
    dummy.type = "ssd"
    dummy.capacity = 1
    dummy.form_factor = "2.5-7mm"
    dummy.port = PORT.sata
    dummy.serial_number = 'USB' + ''.join(choice(digits) for i in range(6)) # USBxxxxxx where x is a random digit

    for a in dir(dummy):
        if a.startswith('__') or callable(getattr(dummy, a)):
            continue
        if getattr(disk, a) == "":
            setattr(disk, a, getattr(dummy, a))

    return disk


def check_complete(disk):
    """
    Check if the disk passed contains all the necessary information to be added to TARALLO
    """
    essentials = ['smart_data', 'brand', 'model', 'type', 'capacity', 'form_factor', 'port', 'serial_number']

    for ess in essentials:
        if getattr(disk, ess) == "":
            return False

    return True


def read_smartctl(smartctl_output):

    disk = Disk()

    data = smartctl_output.split('=== START OF INFORMATION SECTION ===', 1)[1] \
        .split('=== START OF READ SMART DATA SECTION ===', 1)[0]

    # For manual inspection later on
    if 'Vendor Specific SMART Attributes with Thresholds:' in smartctl_output:
        disk.smart_data_long = 'Vendor Specific SMART Attributes with Thresholds:' + \
                               smartctl_output.split('Vendor Specific SMART Attributes with Thresholds:', 1)[1].split('\n\n', 1)[
                                   0]
    elif 'SMART/Health Information' in smartctl_output:
        disk.smart_data_long = 'SMART/Health Information' + \
                               smartctl_output.split('SMART/Health Information', 1)[1].split('\n\n', 1)[0]

    status = "not supported"
    for line in smartctl_output.splitlines():
        if "SMART overall-health" in line:
            status = line.split(":")[1].strip()
        elif "Device does not support Self Test logging" in line:
            status = "not supported"

    if status == "PASSED":
        # the disk is working fine
        disk.smart_data = SMART.working

    elif status == "FAILED!":
        # the disk is not working fine
        disk.smart_data = SMART.fail

    elif status == "UNKNOWN!":
        # the connection timed out, there could be different reasons
        disk.smart_data = SMART.not_available

    # TODO: throw a catastrophic fatal error of death if a disk has SMART disabled (can be enabled and disabled with smartctl to test and view the exact error message)

    elif status == "not supported":
        # the smart data need to be switched on or the smart capability is not supported
        for line in data.splitlines():
            if "SMART support is:" in line:
                line = line.split("SMART support is:")[1].strip()
                if "device lacks SMART capability" in line:
                    # disk doesn't support smart capabilities
                    disk.smart_data = SMART.not_available
                elif "device has SMART capability" in line:
                    # you need to enable smart capabilities
                    print("you need to enable smart capabilities on disk")
                    disk.smart_data = SMART.not_available

    for line in data.splitlines():
        if "Model Family:" in line:
            line = line.split("Model Family:")[1].strip()
            brand, family = split_brand_and_other(line)
            disk.family = family
            if brand is not None:
                disk.brand = brand

        elif "Model Number:" in line:
            line = line.split("Model Number:")[1].strip()
            brand, model = split_brand_and_other(line)
            disk.model = model
            if brand is not None:
                disk.brand = brand

        elif "Device Model:" in line:
            line = line.split("Device Model:")[1].strip()
            brand, model = split_brand_and_other(line)
            disk.model = model
            if brand is not None:
                disk.brand = brand

        elif "Serial Number:" in line:
            disk.serial_number = line.split("Serial Number:")[1].strip()

        elif "LU WWN Device Id:" in line:
            disk.wwn = line.split("LU WWN Device Id:")[1].strip()

        elif "Form Factor:" in line:
            ff = line.split("Form Factor:")[1].strip()
            # https://github.com/smartmontools/smartmontools/blob/40468930fd77d681b034941c94dc858fe2c1ef10/smartmontools/ataprint.cpp#L405
            if ff == '3.5 inches':
                disk.form_factor = '3.5'
            elif ff == '2.5 inches':
                # This is the most common height, just guessing...
                disk.form_factor = '2.5-7mm'
            elif ff == '1.8 inches':
                # Still guessing...
                disk.form_factor = '1.8-8mm'
            elif ff == 'M.2':
                disk.form_factor = 'm2'

        elif "User Capacity:" in line:
            # https://stackoverflow.com/a/3411435
            num_bytes = line.split('User Capacity:')[1].split("bytes")[0].strip().replace(',', '').replace('.',
                                                                                                           '')
            round_digits = int(floor(log10(abs(float(num_bytes))))) - 2
            bytes_rounded = int(round(float(num_bytes), - round_digits))
            disk.capacity = bytes_rounded

            tmp_capacity = line.split("[")[1].split("]")[0]
            if tmp_capacity is not None:
                disk.human_readable_capacity = tmp_capacity

        elif "Rotation Rate:" in line:
            if "Solid State Device" not in line:
                disk.rotation_rate = int(line.split("Rotation Rate:")[1].split("rpm")[0].strip())
                disk.type = "hdd"
            else:
                disk.type = "ssd"

    if disk.brand == 'Western Digital':
        # These are useless and usually not even printed on labels and in bar codes...
        disk.model = remove_prefix('WDC ', disk.model)
        disk.serial_number = remove_prefix('WD-', disk.serial_number)
    if disk.model.startswith('SSD '):
        disk.model = disk.model[4:]

    if 'SATA' in disk.family or 'SATA' in disk.model:
        disk.port = PORT.sata
    if 'SATA Version is:' in smartctl_output:
        disk.port = PORT.sata

    return disk


def tarallo_conversion(disks: list):
    """
    Transforms list of disks in a format compatible to TARALLO
    :param disks: list of disks to convert
    :return: converted disks list
    """
    result = []
    for disk in disks:
        if disk.smart_data.value == "ok":
            working = "yes"
        else:
            working = "no"

        if disk.type == "ssd":  # ssd
            this_disk = {
                "type": "ssd",
                "brand": disk.brand,
                "model": disk.model,
                "family": disk.family,
                "wwn": disk.wwn,
                "sn": disk.serial_number,
                "capacity-byte": disk.capacity,
                "smart-data": disk.smart_data.value,
                "working": working
            }
            if disk.smart_data_long is not SMART.not_available:
                this_disk['notes'] = disk.smart_data_long
        else:
            this_disk = {
                "type": "hdd",
                "brand": disk.brand,
                "model": disk.model,
                "family": disk.family,
                "wwn": disk.wwn,
                "sn": disk.serial_number,
                # Despite the name it's still in bytes, but with SI prefix (not power of 2), "deci" is there just to
                # tell some functions how to convert it to human-readable format
                "capacity-decibyte": disk.capacity,
                "spin-rate-rpm": disk.rotation_rate,
                "smart-data": disk.smart_data.value,
                "working": working
            }
        if disk.form_factor is not None:
            this_disk["hdd-form-factor"] = disk.form_factor
        if disk.port != PORT.unknown:
            # Disks usually have 1 port (be it SATA or IDE or SCSI or other)
            this_disk[disk.port.value] = 1
        if disk.smart_data_long is not SMART.not_available:
            this_disk['notes'] = disk.smart_data_long
        this_disk = {k: v for k, v in this_disk.items() if v != '' and v is not None}
        result.append({
            'features': this_disk,
            'mount_point': disk.dev
        })

    return result


def split_brand_and_other(line):
    lowered = line.lower()

    possibilities = [
        'Western Digital',
        'Seagate',
        'Maxtor',
        'Hitachi',
        'Toshiba',
        'Samsung',
        'Fujitsu',
        'Apple',
        'Crucial/Micron',
        'Crucial',
        'LiteOn',
    ]

    brand = None
    other = line
    for possible in possibilities:
        if lowered.startswith(possible.lower()):
            brand = possible
            other = line[len(possible):].lstrip('_').strip()
            break

    return brand, other


def remove_prefix(prefix, text):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


def main():
    import pprint

    pp = pprint.PrettyPrinter()

    result = parse_disks(interactive=True, usbdebug=True)
    pp.pprint(result)


if __name__ == '__main__':
    main()
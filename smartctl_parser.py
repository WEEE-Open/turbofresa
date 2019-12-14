#!/usr/bin/env python3
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
    """
    Class defining disk parameters
    """
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
        self.smart_data_long = SMART.not_available
        self.smart_data = SMART.not_available


class SMART(Enum):
    working = "ok"
    fail = "fail"
    not_available = "not_available"
    old = "old"  # TODO: ask @quel_tale what the heck is this


def read_smartctl(path: str, interactive: bool = False) -> list:
    """
    Detects disks through smartctl and outputs disks list
    :param path: path where to save smartctl output files
    :param interactive:
    :return: list of disks
    """
    disks = []

    filegen = os.getcwd() + "/smartctl_filegen.sh"

    return_code = sp.run(["sudo", filegen, path]).returncode

    assert(return_code == 0), 'Error during disk detection'

    for filename in os.listdir(path):
        if "smartctl-dev-" in filename:

            disk = Disk()

            try:
                with open(path + "/" + filename, 'r') as f:
                    output = f.read()
            except FileNotFoundError:
                raise InputFileNotFoundError(path)

            if '=== START OF INFORMATION SECTION ===' not in output:
                if interactive:
                    print(f"{filename} does not contain disk information, was it a USB stick?")
                continue

            data = output.split('=== START OF INFORMATION SECTION ===', 1)[1] \
                .split('=== START OF READ SMART DATA SECTION ===', 1)[0]

            # For manual inspection later on
            if '=== START OF SMART DATA SECTION ===' in output:
                disk.smart_data_long = '=== START OF SMART DATA SECTION ===' + \
                                       output.split('=== START OF SMART DATA SECTION ===', 1)[1]
            elif '=== START OF READ SMART DATA SECTION ===' in output:
                disk.smart_data_long = '=== START OF READ SMART DATA SECTION ===' + \
                                       output.split('=== START OF READ SMART DATA SECTION ===', 1)[1]

            if disk.smart_data_long != SMART.not_available:
                status = "not supported"
                for line in disk.smart_data_long.splitlines():
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

                elif status == "not supported":
                    # the smart data need to be switched on or the smart capability is not supported
                    for line in data.splitlines():
                        if "SMART support is:" in line:
                            line = line.split("SMART support is:")[1].strip()
                            if "device lacks SMART capability" in line:
                                # disk doesn't support smart capabilities
                                disk.smart_data = SMART.old
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

            disks.append(disk)

    result = []
    for disk in disks:
        if disk.type == "ssd":  # ssd
            this_disk = {
                "type": "ssd",
                "brand": disk.brand,
                "model": disk.model,
                "family": disk.family,
                "wwn": disk.wwn,
                "sn": disk.serial_number,
                "capacity-byte": disk.capacity,
                "human_readable_capacity": disk.human_readable_capacity,
                # "human_readable_smart_data": disk.smart_data_long
                "smart-data": disk.smart_data.value
            }
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
                "human_readable_capacity": disk.human_readable_capacity,
                "spin-rate-rpm": disk.rotation_rate,
                # "human_readable_smart_data": disk.smart_data.long
                "smart-data": disk.smart_data.value
            }
        if disk.form_factor is not None:
            this_disk["hdd-form-factor"] = disk.form_factor
        if 'SATA' in disk.family or 'SATA' in disk.model:
            this_disk["sata-ports-n"] = 1
        result.append(this_disk)
    return result


def split_brand_and_other(line):
    lowered = line.lower()

    possibilities = [
        'Western Digital',
        'Seagate',
        'Maxtor',
        'Hitachi',
        'Samsung',
        'Fujitsu',
        'Apple',
        'Crucial/Micron',
        'Crucial',
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
    path = os.getcwd() + "/smartctl"

    try:
        return read_smartctl(path, True)
    except InputFileNotFoundError as e:
        print(str(e))
        exit(1)


if __name__ == '__main__':
    print(main())

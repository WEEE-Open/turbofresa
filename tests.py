import os
import subprocess as sp
from dotenv import load_dotenv
from pytarallo.Tarallo import Tarallo, Item
from tarallo_interface import TaralloInterface
from pytarallo.Errors import *
import turbofresa
from smartctl_parser import parse_disks, SMART

from nose.plugins.skip import SkipTest


class Test_Tarallo:
    """Verify functioning of TaralloInterface"""

    # !!!WARNING!!!
    # Only run this on a test version of the TARALLO!!!

    @classmethod
    def setup_class(cls):
        cls.dummy_disk = {
            'brand': 'PYTHON_TEST',
            'capacity-byte': 1,
            'hdd-form-factor': '2.5-7mm',
            'model': 'TEST',
            'sata-ports-n': 1,
            'smart-data': SMART.working.value,
            'sn': 'USB123456',
            'type': 'ssd',
        }

        load_dotenv()
        tarallo_url = os.getenv("TARALLO_URL")
        tarallo_token = os.getenv("TARALLO_TOKEN")

        try:
            cls.tarallo_instance = Tarallo(tarallo_url, tarallo_token)
            status = cls.tarallo_instance.status()
        except:
            cls.connected = False
        else:
            if status == 200:
                cls.connected = True
            else:
                cls.connected = False
        finally:
            if cls.connected is False:
                print("Couldn't connect to tarallo server")
            else:
                cls.tarallo_interface = TaralloInterface(cls.tarallo_instance)

    def setup(self):
        if not self.connected:
            raise SkipTest("Not connected to TARALLO")
        else:
            codes = self.tarallo_instance.get_codes_by_feature('sn', self.dummy_disk['sn'])
            if len(codes) > 1:
                for code in codes:
                    self.tarallo_instance.remove_item(code)
            elif len(codes) == 1:
                self.tarallo_instance.remove_item(codes[0])

    def test_add_disk(self):
        """Try adding disk to TARALLO"""

        disk = self.dummy_disk

        assert turbofresa.add_to_tarallo(self.tarallo_instance, disk) is True

        disk_code = self.tarallo_instance.get_codes_by_feature('sn', disk['sn'])
        assert len(disk_code) == 1

    def test_add_duplicate(self):
        """Try to add a non-conflicting duplicate"""
        disk = self.dummy_disk

        item = Item()
        item.features = disk
        item.location = 'Polito'

        try:
            self.tarallo_instance.add_item(item=item)
            print("Item inserted successfully")
        except ValidationError:
            print("Item not inserted")
            response = self.tarallo_instance.response
            print("HTTP status code:", response.status_code, "\n" + response.json()['message'])
            raise AssertionError("Failed to manually add disk to TARALLO")

        assert turbofresa.add_to_tarallo(self.tarallo_instance, disk) is True, "Failed to add disk through" \
                                                                               "TURBOFRESA"

        disk_code = self.tarallo_instance.get_codes_by_feature('sn', disk['sn'])
        assert len(disk_code) == 1, "Disk added by error"

    def test_add_conflicting(self):
        """Try to add a conflicting duplicate"""

        disk = self.dummy_disk
        conflicting = dict(disk)

        conflicting['model'] = "UNEXPECTED"

        item = Item()
        item.features = conflicting
        item.location = 'Polito'

        try:
            self.tarallo_instance.add_item(item=item)
            print("Item inserted successfully")
        except ValidationError:
            print("Item not inserted")
            response = self.tarallo_instance.response
            print("HTTP status code:", response.status_code, "\n" + response.json()['message'])
            raise AssertionError("Failed to manually add disk to TARALLO")

        assert turbofresa.add_to_tarallo(self.tarallo_instance, disk) is False

    def test_update_broken(self):
        """Update TARALLO with broken disk"""

        disk = dict(self.dummy_disk)
        turbofresa.add_to_tarallo(self.tarallo_instance, disk)
        disk['smart-data'] = SMART.fail.value
        assert turbofresa.add_to_tarallo_broken(self.tarallo_instance, disk) is True


class Test_Turbofresa:
    """Verify functioning of disk parser and TURBOFRESA"""

    def test_smartctl_filegen(self):
        import subprocess as sp

        print('')

        smartctl_path = os.path.join(os.getcwd(), "smartctl_test")
        filegen = os.path.join(os.getcwd(), "smartctl_filegen.sh")
        return_code = sp.run(["sudo", "-S", filegen, smartctl_path]).returncode
        assert (return_code == 0), 'Error during disk detection'
        sp.run(['sudo', '-S', 'rm', '-rf', smartctl_path])

    def test_parser(self):
        import sys
        connected = set()
        output = sp.check_output(["lsblk", "-nd", "-o", "NAME"]).decode(sys.stdout.encoding)

        for line in output.splitlines():
            connected.add(line)

        disks = parse_disks(interactive=False, usbdebug=True)
        assert len(connected) == len(disks)
        for disk in disks:
            assert disk["mount_point"] in connected

    def test_ignore_sys_disks(self):
        ignored = turbofresa.ignore_sys_disks()
        assert len(ignored) > 0
        for disk in ignored:
            assert "sd" in disk

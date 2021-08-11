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

        # Dummy disk used throughout all the tests
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

        # Load url and token from env
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
            # Skip the test if we're not connected to TARALLO
            raise SkipTest("Not connected to TARALLO")
        else:
            # Remove all possible duplicates of the dummy
            codes = self.tarallo_instance.get_codes_by_feature('sn', self.dummy_disk['sn'])
            for code in codes:
                self.tarallo_instance.remove_item(code)

    def test_add_disk(self):
        """Try adding disk to TARALLO"""

        disk = self.dummy_disk

        # Verify that we don't have any problem adding the disk
        assert self.tarallo_interface.add_disk(disk) is True

        # Verify that one and only one disk is being added
        disk_code = self.tarallo_instance.get_codes_by_feature('sn', disk['sn'])
        assert len(disk_code) == 1

    def test_add_duplicate_no_conflict(self):
        """Try to add a non-conflicting duplicate"""
        disk = self.dummy_disk

        # Check that there are no duplicates
        assert self.tarallo_interface.check_duplicate(disk) == 0, "TaralloInterface is detecting a duplicate"

        # Manually add the dummy through pytarallo
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
            raise AssertionError("Failed to manually add disk through pytarallo")

        # Verify that check_duplicate doesn't detect a conflicting entry
        assert self.tarallo_interface.check_duplicate(disk) == 1, "TaralloInterface is detecting a conflicting duplicate"

        # Try to add the duplicate through TaralloInterface
        assert self.tarallo_interface.add_disk(disk) is True, "Failed to add disk through TaralloInterface"

        # Verify there's only one copy of the disk on TARALLO
        disk_code = self.tarallo_instance.get_codes_by_feature('sn', disk['sn'])
        assert len(disk_code) == 1, "Disk added by error"

    def test_add_duplicate_conflict(self):
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

        # Check if conflict is detected
        assert self.tarallo_interface.check_duplicate(disk) == -1, "TaralloInterface didn't detect the conflict"

        # Check if TaralloInterface refuses to add the disk
        assert self.tarallo_interface.add_disk(disk) is False, "TaralloInterface added the disk anyway"

    def test_update_broken(self):
        """Update TARALLO with broken disk"""

        disk = dict(self.dummy_disk)
        self.tarallo_interface.add_disk(disk)
        disk['smart-data'] = SMART.fail.value

        # Verify the disk has been added even if duplicate
        assert self.tarallo_interface.add_disk(disk) is True


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

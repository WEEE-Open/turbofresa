import os
from dotenv import load_dotenv
from pytarallo.Tarallo import Tarallo, Item
from pytarallo.Errors import *
import turbofresa
from smartctl_parser import parse_disks, SMART

from nose.plugins.skip import SkipTest


class Test_Tarallo:
    """
    Used to verify intereactions between TARALLO and TURBOFRESA

    !!!WARNING!!!
    Only run this on a test version of the TARALLO!!!
    """

    def setup(self):
        if not self.connected:
            raise SkipTest("Not connected to TARALLO")

    def teardown(self):
        if self.connected:
            codes = self.tarallo_instance.get_codes_by_feature('sn', self.dummy_disk['sn'])
            if len(codes) > 1:
                for code in codes:
                    self.tarallo_instance.remove_item(code)
            elif len(codes) == 1:
                self.tarallo_instance.remove_item(codes)

    @classmethod
    def setup_class(cls):
        cls.dummy_disk = {
            'brand': 'PYTHON_TEST',
            'capacity-byte': 1,
            'hdd-form-factor': '2.5-7mm',
            'model': 'TEST',
            'sata-ports-n': 1,
            'smart-data': SMART.working,
            'sn': 'USB123456',
            'type': 'ssd',
        }

        load_dotenv()
        tarallo_url = os.getenv("TARALLO_URL")
        tarallo_token = os.getenv("TARALLO_TOKEN")
        try:
            cls.tarallo_instance = Tarallo(tarallo_url, tarallo_token)
        except:
            cls.connected = False
        else:
            if cls.tarallo_instance.status() == 200:
                cls.connected = True
            else:
                cls.connected = False
        finally:
            if cls.connected is False:
                print("Couldn't connect to tarallo server")

    def test_add_disk(self):
        """
        Simple disk addition to TARALLO through the TURBOFRESA
        """
        disk = self.dummy_disk

        assert turbofresa.add_to_tarallo(self.tarallo_instance, disk) is True

        disk_code = self.tarallo_instance.get_codes_by_feature('sn', disk['sn'])
        assert len(disk_code) == 1

    def test_add_duplicate(self):
        """
        Check if TURBOFRESA refuses to add a duplicate disk (with the same specs),
        but anyway continues to wipe it
        """
        disk = self.dummy_disk

        item = Item()
        item.features = disk
        item.location = 'Magazzino'

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
        """
        Check if TURBOFRESA refuses to wipe disk if another one with same serial (but different specs)
        is already present to avoid conflicting information on the database
        """
        disk = self.dummy_disk
        conflicting = dict(disk)

        conflicting['model'] = "UNEXPECTED"

        item = Item()
        item.features = conflicting
        item.location = 'Magazzino'

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
        """
        Ensures that in case the disk results broken its TARALLO entry is updated
        """
        disk = dict(self.dummy_disk)

        turbofresa.add_to_tarallo(self.tarallo_instance, disk)

        disk['smart-data'] = SMART.fail

        assert turbofresa.add_to_tarallo_broken(self.tarallo_instance, disk) is True


class Test_Turbofresa:
    """
    Tests correct functioning of the parser and the TURBOFRESA
    """
    @classmethod
    def setup_class(cls):
        while True:
            answer = input("\nSome of these tests require a USB key connected to the pc\n"
                           "If you want to do the usb tests make sure only one is connected, "
                           "otherwise make sure none is plugged. \n"
                           "\nDo you want to execute USB tests? [y/N]")

            if answer == 'y' or answer == 'Y':
                cls.usb_present = True
                break
            elif answer == 'n' or answer == 'N' or answer == '':
                cls.usb_present = False
                break
            else:
                print(f'Unrecognized answer {answer}, type either "y" or "n"')

    def test_smartctl_filegen(self):
        import subprocess as sp

        print('')

        smartctl_path = os.getcwd() + "/smartctl_test"
        filegen = os.getcwd() + "/smartctl_filegen.sh"
        return_code = sp.run(["sudo", "-S", filegen, smartctl_path]).returncode
        assert (return_code == 0), 'Error during disk detection'

    def test_parser_no_usb(self):
        disks = parse_disks(interactive=False, usbdebug=False)
        filenum = len(os.listdir())
        if self.usb_present is False:
            assert filenum == len(disks)
        else:
            assert filenum == len(disks)+1

    def test_parser_usb(self):
        if self.usb_present is False:
            raise SkipTest("USB not connected")


if __name__ == "__main__":
    test = Test_Tarallo()
    test.setup_class()
    test.setup()
    test.test_add_disk()

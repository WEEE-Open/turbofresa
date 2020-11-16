from pytarallo import Tarallo, Errors, Item

class TaralloInterface:
    instance = None

    @staticmethod
    def connect(url: str, token: str):
        interface = TaralloInterface()

        print("Trying to connect to the T.A.R.A.L.L.O. database")
        try:
            interface.instance = Tarallo.Tarallo(url, token)
        except:
            print('Failed to connect to the database')
            return None
        print("Connection successful!")
        return interface

    def add_disk(self, disk: dict) -> bool:
        """
        Adds disk to Tarallo database
        :param instance: Tarallo instance where to add the disk
        :param disk: disk to add to the database
        :return: True if added successfully or it was already present,
            False if there were multiple instances of it in the database
        """

        if not self.check_on_tarallo(disk):
            return False

        print("Adding disk to the database")
        item = Item.Item()
        item.features = disk
        item.location = 'Polito'  # TODO: maybe it can be set from config or a better default should be picked

        try:
            self.instance.add_item(item=item)
            print("Item inserted successfully")
        except Errors.ValidationError:
            print("Item not inserted")
            response = self.instance.response
            print("HTTP status code:", response.status_code, "\n" + response.json()['message'])
            return False

        print("Successfully added the disk")
        print("Disk code on the Database: " + self.instance.get_codes_by_feature('sn', disk['sn'])[0])
        return True

    def check_on_tarallo(self, disk: dict) -> bool:
        """
        Verify if there's a disk that might conflict
        with what we want to insert into the TARALLO
        """

        print("\nSearching the T.A.R.A.L.L.O. databse for disk with serial number {}".format(disk['sn']))
        disk_code = self.instance.get_codes_by_feature('sn', disk['sn'])

        # if there's already more than 1 corresponding disk in the TARALLO, don't add
        if len(disk_code) > 1:
            print("Multiple disks in the database corresponding to the serial number: " + disk['sn'])
            print("Won't proceed until conflict is solved")
            return False
        # if there is exactly one disk, check if we're simply changing the status or there's a conflict
        elif len(disk_code) == 1:
            print(f"Disk with serial number {disk['sn']} already present in the database"
                  f"with the code {disk_code[0]}")
            item = self.instance.get_item(disk_code[0])
            # checking for conflicing features
            for key, value in item.features.items():
                if key == 'smart-data' or key == 'smart-data-long':
                    continue  # we don't care if it has a different status
                if value != disk[key]:
                    print("There's a conflict in the database for this disk")
                    print("Won't proceed until conflict is solved")
                    return False
            print("The entry doesn't conflict with the current disk, safe to add")
            return True
        elif len(disk_code) == 0:
            print("No corresponding disk in the database")
            return True
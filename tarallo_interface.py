from pytarallo import Tarallo, Errors, Item


class TaralloInterface:
    def __init__(self, instance=None):
        self.instance = instance

    def connect(self, url: str, token: str):
        if self.instance is not None:
            print("Already connected to a T.A.R.A.L.L.O. instance")
            return False

        print("Trying to connect to the T.A.R.A.L.L.O. database")
        try:
            self.instance = Tarallo.Tarallo(url, token)
        except:
            print('Failed to connect to the database')
            return False
        print("Successfully connected to the database")
        return True

    def add_disk(self, disk: dict) -> bool:
        """
        Adds or updates disk to Tarallo database
        :param disk: disk to add to the database
        :return: True if added/updated successfully, False otherwise
        """

        # Don't do any operation if there are conflicting entries in the db
        duplicates = self.check_duplicate(disk)
        if duplicates == -1:
            return False

        print("Adding disk to the database")

        # Catch any errors thrown by the TARALLO in case some disaster happens
        try:
            # Base on the presence of duplicates, add or update
            if duplicates == 0:
                item = Item.Item()
                item.features = disk
                item.location = 'Polito'  # TODO: maybe it can be set from config or a better default should be picked
                self.instance.add_item(item=item)
            elif duplicates == 1:
                # TODO: to avoid checking twice the database for the disk we could return the code from check_duplicates
                code = self.instance.get_codes_by_feature('sn', disk['sn'])[0]
                self.instance.update_features(code, disk)
            print("Item inserted successfully")
        except Errors.ValidationError:
            # Simply return False and don't crash if there's some error
            print("Item not inserted")
            response = self.instance.response
            print("HTTP status code:", response.status_code, "\n" + response.json()['message'])
            return False

        print("Successfully added the disk")
        print("Disk code on the Database: " + self.instance.get_codes_by_feature('sn', disk['sn'])[0])
        return True

    def check_duplicate(self, disk: dict) -> int:
        """
        Verify if there's a disk that might conflict with what we want to insert into the TARALLO
        :param disk: the disk that might give a conflict
        :return: 0 if no duplicates are detected
        :return: 1 if a non-conflicting duplicate is found
        :return: -1 if a conflicting duplicate is found
        """

        print("\nSearching the T.A.R.A.L.L.O. databse for disk with serial number {}".format(disk['sn']))
        disk_code = self.instance.get_codes_by_feature('sn', disk['sn'])

        # if there's already more than 1 corresponding disk in the TARALLO, don't add
        if len(disk_code) > 1:
            print("Multiple disks in the database corresponding to the serial number: " + disk['sn'])
            print("Won't proceed until conflict is solved")
            return -1
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
                    return -1
            print("The entry doesn't conflict with the current disk, safe to add")
            return 1
        elif len(disk_code) == 0:
            print("No corresponding disk in the database")
            return 0

    def get_instance(self):
        """Returns an instance of the tarallo connection if interested in acting on that manually"""
        return self.instance

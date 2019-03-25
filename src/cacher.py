import pickle
import os

from src import CONSTANTS


class Cacher:
    def __init__(self):
        self.dir_ = CONSTANTS.CACHE_FOLDER

        if not os.path.exists(self.dir_):
            os.mkdir(self.dir_)


    def dump(self, data, email_address):
        filepath = self._create_file_path(email_address)
        print('dumping!')
        if not os.path.exists(filepath):
            f = open(filepath, 'w')
            f.close()

        with open(filepath, 'ab') as file_:
            pickle.dump(data, file_)

        return True


    def load(self, email_address):
        filepath = self._create_file_path(email_address)

        if not os.path.exists(filepath) or not os.path.getsize(filepath):
            return None

        with open(filepath, 'rb') as file_:
            data = pickle.load(file_)

        return data


    def _create_file_path(self, email_address):
        return os.path.join(self.dir_, email_address)


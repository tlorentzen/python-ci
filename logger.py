import os
from datetime import datetime


class Logger:

    path: str = None
    store: str = ""

    def __init__(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
        self.path = path

    def print(self, text: str, add_empty_line= False, write_out: bool = True):
        time_stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S:: ")

        for line in text.splitlines():
            message = time_stamp + line
            self.store += message+"\n"

            if write_out:
                print(message)

        if add_empty_line:
            self.store += "\n"
            print("")

    def save_and_clear(self):
        file_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        if self.store != "":
            with open(self.path+"/"+file_time+".txt", 'w') as out_file:
                out_file.write(self.store)
        self.clear()

    def clear(self):
        self.store = ""




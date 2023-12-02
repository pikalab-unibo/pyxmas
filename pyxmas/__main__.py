import pyxmas
import pickle 
import os
import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import os
from .interaction import Interact
from .xmpp import XmppService
import threading

pyxmas.enable_logging()

def save(df,filename):
    with open(filename, 'wb') as file:
        pickle.dump(df, file)

#Watchdog Signal Observer
class Joined(FileSystemEventHandler):
    def __init__(self):
        self.stop = False

    def method_to_run(self):
        self.stop = True

    def on_modified(self, event):
        # Check if the modified file is 'interaction.pickle'
        if os.path.basename(event.src_path) == "lobby.pickle":
            self.method_to_run()


def start_observer(event_handler):
    observer = Observer()
    # Schedule the observer for the directory containing 'interaction.pickle'
    path = os.getcwd()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    print(f"Observer started at {path}")  # Debugging print
    try:
        while not event_handler.stop:
            time.sleep(1)
            if event_handler.stop:
                observer.stop()
                return

    except KeyboardInterrupt:
        observer.stop()
    observer.join()

pyxmas.enable_logging()

if __name__ == '__main__':
    with pyxmas.System() as system:

        local_service = XmppService()
        local_service.start()

        while True:
            handler = Joined()
            start_observer(handler)
            lobby = pd.read_pickle("lobby.pickle")
            print(lobby)

            usernames = lobby.index.values
            lobby = pd.DataFrame({"Username":[]})
            save(lobby, "lobby.pickle")

            processes = []
            for username in usernames:
                process = threading.Thread(target=Interact, args=(username,local_service))
                process.start()
                processes.append(process)

            time.sleep(1)
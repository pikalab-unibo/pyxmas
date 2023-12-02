import pyxmas
import subprocess
from Expectation.explainee_imp import ExplaineeAgent
from Expectation.recommender_imp import RecommenderAgent
import pickle 
import os
import pandas as pd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import os
import threading

pyxmas.enable_logging()
_DEFAULT_DOMAIN = 'localhost'

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
    path = os.getcwd() + "/Expectation"
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

class XmppService:
    docker = 'docker'

    def __init__(self, domain: str = _DEFAULT_DOMAIN):
        self._domain = domain
        self._started = self._check_health()

    def _run_lazy(self, *args: str):
        p = subprocess.run(list(args), capture_output=True)
        p.check_returncode()
        for line in p.stdout.splitlines():
            line = line.decode("utf-8").strip()
            pyxmas.logger.info(line)
            yield line

    def _run(self, *args: str):
        for _ in self._run_lazy(*args):
            pass

    @property
    def domain(self):
        return self._domain

    @property
    def is_started(self):
        return self._started

    def start(self):
        if not self._started:
            self._run(self.docker, "compose", "up", "--wait")
            self._started = True
        else:
            pyxmas.logger.warning("Silently ignored attempt to start already started service")

    def stop(self):
        if self._started:
            self._run(self.docker, "compose", "kill")
            self._run(self.docker, "compose", "down")
            self._started = False
        else:
            pyxmas.logger.warning("Silently ignored attempt to stop unstarted service")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def _ensure_started(self):
        if not self._started:
            raise RuntimeError("Service is not started")

    def _check_health(self, msg='is_on'):
        try:
            lines = list(self._run_lazy(self.docker, "compose", "exec", "xmpp-service", "echo", msg))
            return lines == [msg]
        except subprocess.CalledProcessError:
            return False

    def add_user(self, username: str, password: str):
        self._ensure_started()
        self._run(self.docker, "compose", "exec", "xmpp-service", "/usr/local/bin/ejabberdctl", "register", username, self._domain,
                  password)

    def remove_user(self, username: str):
        self._ensure_started()
        self._run(self.docker, "compose", "exec", "xmpp-service", "/usr/local/bin/ejabberdctl", "unregister", username,
                  self._domain)

    def get_users(self):
        self._ensure_started()
        return list(
            self._run_lazy(self.docker, "compose", "exec", "xmpp-service", "/usr/local/bin/ejabberdctl", "registered_users",
                           self._domain))



with pyxmas.System() as system:
    XmppService = XmppService(_DEFAULT_DOMAIN)
    XmppService.start()

    path = os.getcwd() + "/Expectation"

    while True:

        handler = Joined()
        start_observer(handler)
        lobby = pd.read_pickle(path + "/lobby.pickle")
        print(lobby)

        temp = lobby.index.values

        lobby = pd.DataFrame({"Username":[]})
        save(lobby,"lobby.pickle")

        for username in temp:

            username = str(username)

            XmppService.add_user(username= username , password="password")
            XmppService.add_user(username= "recommender-" + username, password="password")

            with RecommenderAgent(jid="recommender-"+username+"@localhost", password="password") as recommender:
                with ExplaineeAgent(user_id=username,jid=username+"@localhost", password="password") as explainee:
                            try:
                                explainee.sync_await(timeout=200)
                                recommender.sync_await(timeout=200)
                            except KeyboardInterrupt:
                                recommender.stop()
                                explainee.stop()


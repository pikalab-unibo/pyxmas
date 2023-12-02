import subprocess
import pyxmas


_DEFAULT_DOMAIN = 'localhost'



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

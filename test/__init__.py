from typing import Dict, List
import pyxmas
import subprocess
import spade.behaviour as sb


__all__ = ['XmppService', 'xmpp_service', 'random_string', 'TestAgent', 'RecordEventBehaviour']


_DEFAULT_DOMAIN = 'localhost'


def random_string(length: int = 16):
    import random
    import string
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


class XmppService:
    def __init__(self, domain: str = _DEFAULT_DOMAIN):
        self._domain = domain
        self._started = False

    def _run_lazy(self, *args: str):
        p = subprocess.run(list(args), capture_output=True)
        p.check_returncode()
        for line in p.stdout.splitlines():
            line = line.decode("utf-8")
            print(line)
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
            self._run("docker", "compose", "up", "-d")
            self._started = True
        else:
            pyxmas.logger.warning("Silently ignored attempt to start already started service")

    def stop(self):
        if self._started:
            self._run("docker", "compose", "kill")
            self._run("docker", "compose", "down")
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

    def add_user(self, username: str, password: str):
        self._ensure_started()
        self._run("docker", "compose", "exec", "xmpp-service", "bin/ejabberdctl", "register", username, self._domain, password)

    def remove_user(self, username: str):
        self._ensure_started()
        self._run("docker", "compose", "exec", "xmpp-service", "bin/ejabberdctl", "unregister", username, self._domain)

    def get_users(self):
        self._ensure_started()
        return list(self._run_lazy("docker", "compose", "exec", "xmpp-service", "bin/ejabberdctl", "registered_users", self._domain))


_xmpp_serices: Dict[str, XmppService] = {}


def xmpp_service(domain: str = _DEFAULT_DOMAIN):
    if domain in _xmpp_serices:
        return _xmpp_serices[domain]
    else:
        service = XmppService(domain)
        _xmpp_serices[domain] = service
        return service


class TestAgent(pyxmas.Agent):
    def __init__(self, name: str, password: str = random_string(), domain: str = _DEFAULT_DOMAIN, service: XmppService = None, events: List = []):
        if service is None:
            service = xmpp_service(domain)
        service.add_user(name, password)
        super().__init__(f"{name}@{domain}", password)
        self._events = events
        self._xmpp_service = service

    @property
    def xmpp_service(self):
        return self._xmpp_service

    @property
    def observable_events(self):
        if self.is_alive():
            raise RuntimeError("Agent is still alive")
        return self._events

    def record_observable_event(self, message):
        self._events.append(message)


class RecordEventBehaviour(pyxmas.Behaviour, sb.OneShotBehaviour):
    def __init__(self, event):
        super().__init__()
        self.event = event

    async def run(self):
        self.agent.record_observable_event(self.event)


xmpp_service().stop()

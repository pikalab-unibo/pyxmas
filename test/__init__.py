from typing import Dict, List
import pyxmas
import subprocess
import spade.behaviour as sb
import unittest

__all__ = ['XmppService', 'xmpp_service', 'random_string', 'TestAgent', 'RecordEventBehaviour',
           'SharedXmppServiceTestCase', 'IndividualXmppServiceTestCase']

_DEFAULT_DOMAIN = 'localhost'

pyxmas.enable_logging()


def random_string(length: int = 16):
    import random
    import string
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


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
        self._run(self.docker, "compose", "exec", "xmpp-service", "bin/ejabberdctl", "register", username, self._domain,
                  password)

    def remove_user(self, username: str):
        self._ensure_started()
        self._run(self.docker, "compose", "exec", "xmpp-service", "bin/ejabberdctl", "unregister", username,
                  self._domain)

    def get_users(self):
        self._ensure_started()
        return list(
            self._run_lazy(self.docker, "compose", "exec", "xmpp-service", "bin/ejabberdctl", "registered_users",
                           self._domain))


_xmpp_serices: Dict[str, XmppService] = {}


def xmpp_service(domain: str = _DEFAULT_DOMAIN):
    if domain in _xmpp_serices:
        return _xmpp_serices[domain]
    else:
        service = XmppService(domain)
        _xmpp_serices[domain] = service
        return service


class TestAgent(pyxmas.Agent):
    def __init__(self, name: str,
                 password: str = random_string(),
                 domain: str = _DEFAULT_DOMAIN,
                 service: XmppService = None,
                 events=None):
        if events is None:
            events = []
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


class SharedXmppServiceTestCase(unittest.TestCase):
    xmpp_service = xmpp_service()

    @classmethod
    def setUpClass(cls):
        cls.xmpp_service.start()

    @classmethod
    def tearDownClass(cls):
        cls.xmpp_service.stop()


class IndividualXmppServiceTestCase(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.xmpp_service = xmpp_service()

    def setUp(self):
        self.xmpp_service.start()

    def tearDown(self):
        self.xmpp_service.stop()


xmpp_service().stop()

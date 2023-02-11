import unittest
import pyxmas
import subprocess


_DEFAULT_DOMAIN = 'localhost'


def _run_lazy(*args):
    p = subprocess.run(list(*args), capture_output=True)
    p.check_returncode()
    for line in p.stdout.splitlines():
        l = line.decode("utf-8")
        pyxmas.logger.info(l) 
        yield l


def _run(*args):
    for _ in _run_lazy(*args):
        pass


def start_xmpp_service():
    _run("docker", "compose", "up", "-d")


def stop_xmpp_service():
    _run("docker", "compose", "kill")
    _run("docker", "compose", "down")


def add_xmpp_user(username, password, domain=_DEFAULT_DOMAIN):
    _run("docker", "exec", "xmpp-service", "bin/ejabberdctl", "register", username, domain, password)


def remove_xmpp_user(username, domain=_DEFAULT_DOMAIN):
    _run("docker", "exec", "xmpp-service", "bin/ejabberdctl", "unregister", username, domain)


def get_xmpp_users(domain=_DEFAULT_DOMAIN):
    return list(_run_lazy("docker", "exec", "xmpp-service", "bin/ejabberdctl", "registered_users", domain))


class TestMyClass(unittest.TestCase):
    # test methods' names should begin with `test_`
    def test_my_method(self):
        x = MyClass().my_method()
        self.assertEqual("Hello World", x)

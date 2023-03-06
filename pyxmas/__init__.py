from ._logging import *
import spade
import spade.agent
import spade.behaviour
import spade.message
import random
import string
import asyncio
import time
import warnings


__all__ = ['System', 'Agent', 'Behaviour', 'enable_logging', 'logger', 'LOG_DEBUG', 'LOG_INFO', 'LOG_WARNING',
           'LOG_ERROR', 'LOG_CRITICAL', 'LOG_FATAL', 'random_string']


def random_string(length: int = 16):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))


class System:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        spade.quit_spade()


class Agent(spade.agent.Agent):

    def __init__(self, jid: str, password: str, verify_security: bool = False):
        super().__init__(jid, password, verify_security)
        self._termination = asyncio.Future()
        self.log(LOG_DEBUG, "Created")

    def __enter__(self):
        f = self.start(auto_register=True)
        f.result()
        return self

    async def __aenter__(self):
        await self.start(auto_register=True)
        return self

    @property
    def termination(self):
        return self._termination

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.is_alive():
            self.stop()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.is_alive():
            await self.stop()

    def log(self, level=LOG_INFO, msg="", *args, **kwargs):
        logger.log(level, f"[{self.jid}] {msg}", *args, **kwargs)

    async def setup(self):
        self.log(LOG_DEBUG, "Started")

    def sync_await(self, sleep=0.1, timeout=None):
        start = time.time()
        while self.is_alive():
            if timeout is not None and time.time() - start > timeout:
                break
            time.sleep(sleep)
    
    async def async_await(self, sleep=0.1, timeout=None):
        start = time.time()
        while self.is_alive():
            if timeout is not None and time.time() - start > timeout:
                break
            await asyncio.sleep(sleep)

    def stop(self):
        self.log(msg="Stopping...")
        result = super().stop()
        # def on_terminated(_):
        #     self._termination.set_result(None)
        # result.add_done_callback(on_terminated)
        return result


class Behaviour(spade.behaviour.CyclicBehaviour):
    def __init__(self):
        super().__init__()
        self._thread = random_string()

    def log(self, level=LOG_INFO, msg="", *args, **kwargs):
        logger.log(level, f"[{self.agent.jid}/{str(self)}] {msg}", *args, **kwargs)

    def set_agent(self, agent) -> None:
        old_agent = self.agent
        result = super().set_agent(agent)
        if agent and agent != old_agent:
            self.log(LOG_DEBUG, "Behaviour added")
        return result

    def new_message(self,
                    recipient: str,
                    payload: str,
                    thread: str = None,
                    metadata: str = None
                ) -> spade.message.Message:
        sender = self.agent.jid
        if isinstance(recipient, str) and "@" not in recipient:
            recipient += f"@{self.agent.jid.domain}"
        if thread is None:
            thread = "#".join([str(sender), str(self), self._thread])
        return spade.agent.Message(to=recipient, sender=str(sender), body=payload, thread=thread, metadata=metadata)


# DeprecationWarning: The loop argument is deprecated since Python 3.8, and scheduled for removal in Python 3.10.
#   self._finished = locks.Event(loop=loop)
warnings.filterwarnings("ignore", category=DeprecationWarning)

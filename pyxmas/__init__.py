from ._logging import *
import spade
import spade.agent
import spade.behaviour


class System:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        spade.quit_spade()


class Agent(spade.agent.Agent):

    def __init__(self, jid: str, password: str, verify_security: bool = False):
        super().__init__(jid, password, verify_security)
        self._future = None
        self.log(LOG_DEBUG, "Created")    

    def __enter__(self):
        self._future = self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._future.result()
        self.stop()

    def log(self, level = LOG_INFO, msg = "", *args, **kwargs):
        logger.log(level, f"[{self.jid}] {msg}", *args, **kwargs)

    async def setup(self):
        self.log(LOG_DEBUG, "Started")


class Behaviour(spade.behaviour.CyclicBehaviour):
    def log(self, level = LOG_INFO, msg = "", *args, **kwargs):
        logger.log(level, f"[{self.agent.jid}/{str(self)}] {msg}", *args, **kwargs)

    def set_agent(self, agent) -> None:
        result = super().set_agent(agent)
        if agent:
            self.log(LOG_DEBUG, "Behaviour added", self)
        return result

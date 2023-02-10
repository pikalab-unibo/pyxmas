import pyxmas
import spade
import spade.agent
import spade.behaviour


pyxmas.enable_logging()


class DummyAgent(pyxmas.Agent):
    class DummyBehaviour(spade.behaviour.OneShotBehaviour, pyxmas.Behaviour):
        async def run(self):
            self.log(msg="Hello World!")

    async def setup(self):
        await super().setup()
        self.add_behaviour(self.DummyBehaviour())


with pyxmas.System() as system:
    with DummyAgent("admin@localhost", "password") as dummy:
        pass

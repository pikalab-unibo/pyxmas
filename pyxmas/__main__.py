import pyxmas
import spade
import spade.agent
import spade.behaviour


class DummyAgent(pyxmas.Agent):
    class DummyBehaviour(spade.behaviour.OneShotBehaviour, pyxmas.Behaviour):
        async def run(self):
            self.log(msg="Hello World!")

    async def setup(self):
        super().setup()
        self.add_behaviour(self.DummyBehaviour())


with pyxmas.System() as system:
    with DummyAgent("your_jid@your_xmpp_server", "your_password") as dummy:
        pass

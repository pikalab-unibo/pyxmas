import test
import unittest
import pyxmas


class HelloAgent(test.TestAgent):
    class RecordEventThenStopBehaviour(test.RecordEventBehaviour):
        def __init__(self, event):
            super().__init__(event)

        async def on_end(self) -> None:
            await self.agent.stop()

    def __init__(self, name, service=None):
        super().__init__(name, service=service)

    async def setup(self):
        await super().setup()
        self.add_behaviour(self.RecordEventThenStopBehaviour("hello"))


class TestExample(test.SharedXmppServiceTestCase):

    def test_hello(self):
        with pyxmas.System():
            with HelloAgent("alice") as agent:
                agent.sync_await()
                self.assertEqual(agent.observable_events, ["hello"])


if __name__ == '__main__':
    unittest.main()

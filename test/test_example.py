import test
import unittest
import pyxmas


class RecordEventThenStopBehaviour(test.RecordEventBehaviour):
    def __init__(self, event):
        super().__init__(event)

    async def run(self):
        await super().run()
        await self.agent.stop()


class HelloAgent(test.TestAgent):
    def __init__(self, name, service = None):
        super().__init__(name, service = service)

    async def setup(self):
        await super().setup()
        self.add_behaviour(RecordEventThenStopBehaviour("hello"))
    

class TestExample(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        pyxmas.enable_logging()
        super().__init__(methodName)
        self.xmpp_service = test.xmpp_service()

    def setUp(self):
        self.xmpp_service.start()

    def test_hello(self):
        with pyxmas.System():
            with HelloAgent("alice") as agent:
                agent.sync_await()
                self.assertEqual(agent.observable_events, ["hello"])

    def tearDown(self):
        self.xmpp_service.stop()


if __name__ == '__main__':
    unittest.main()

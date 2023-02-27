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


class PingerAgent(test.TestAgent):
    class PingPongStop(pyxmas.Behaviour):
        async def on_end(self) -> None:
            await self.agent.stop()

        async def run(self) -> None:
            try:
                message = self.new_message(recipient='ponger', payload='ping')
                self.log(msg=f"Sending message {message}")
                await self.send(message)
                self.log(msg=f"Sent message {message}")
                self.agent.record_observable_event('sent_ping')
                self.log(msg=f"Receiving message matching {self.template}")
                pong = await self.receive()
                self.log(msg=f'Received message {pong}')
                self.agent.record_observable_event(f'received_{pong.body}')
            except Exception as e:
                self.log(msg=str(e))
                self.agent.record_observable_event(e)
            finally:
                self.kill()

    def __init__(self, name, service=None):
        super().__init__(name, service=service)

    async def setup(self):
        await super().setup()
        self.add_behaviour(self.PingPongStop())


class PongerAgent(test.TestAgent):
    class PongPingStop(pyxmas.Behaviour):
        async def on_end(self) -> None:
            await self.agent.stop()

        async def run(self) -> None:
            try:
                self.log(msg=f"Receiving message matching {self.template}")
                ping = await self.receive()
                self.log(msg=f'Received message {ping}')
                self.agent.record_observable_event(f'received_{ping.body}')
                pong = ping.make_reply(body='pong')
                self.log(msg=f"Sending message {pong}")
                await self.send(pong)
                self.log(msg=f"Sent message {pong}")
                self.agent.record_observable_event(f'sent_pong')
            except Exception as e:
                self.log(msg=str(e))
                self.agent.record_observable_event(e)
            finally:
                self.kill()

    def __init__(self, name, service=None):
        super().__init__(name, service=service)

    async def setup(self):
        await super().setup()
        self.add_behaviour(self.PongPingStop())


class TestExample(test.SharedXmppServiceTestCase):

    def test_hello(self):
        with HelloAgent("alice") as agent:
            agent.sync_await()
            self.assertEqual(["hello"], agent.observable_events)

    def test_ping_pong(self):
        with PongerAgent("ponger") as ponger:
            with PingerAgent("pinger") as pinger:
                pinger.sync_await()
                ponger.sync_await()
                self.assertEqual(["sent_ping", "received_pong"], pinger.observable_events)
                self.assertEqual(["received_ping", "sent_pong"], ponger.observable_events)


if __name__ == '__main__':
    unittest.main()

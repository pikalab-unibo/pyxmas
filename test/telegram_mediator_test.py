import asyncio
import test
import unittest
import pyxmas

from spade.behaviour import CyclicBehaviour
from spade.template import Template
from spade.message import MessageBase, Message

from telegram import Update, error
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext, Updater, MessageHandler

import aioxmpp
import aioxmpp.dispatcher


def get_token():
    with open('token', 'r') as fin:
        return fin.readline()


class TelegramBot:
    application: Application

    async def echo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        assert update.message is not None

        def receive_xmpp_message(msg):
            if not msg.body:
                return
            
            body_text = msg.body[aioxmpp.structs.LanguageTag.fromstr('en')]

            assert update.message
            asyncio.ensure_future(update.message.reply_text(f"Received echo: {body_text}"))
            self.message_dispatcher.unregister_callback(aioxmpp.MessageType.CHAT, None)

        self.message_dispatcher.register_callback(
            aioxmpp.MessageType.CHAT,
            None,
            receive_xmpp_message)
        
        await self.send_xmpp_message(update)

    def __init__(self) -> None:
        self.application = Application.builder().token(get_token()).build()
        self.application.add_handler(MessageHandler(None, self.echo_command))
        self.jid = aioxmpp.JID.fromstr(f"telegram@{test._DEFAULT_DOMAIN}")
        self.xmpp_client = aioxmpp.PresenceManagedClient(
            self.jid,
            aioxmpp.make_security_layer("telegram_test", no_verify=True))  # BIG PROBLEM
        
        self.message_dispatcher: aioxmpp.dispatcher.SimpleMessageDispatcher = self.xmpp_client.summon(
            aioxmpp.dispatcher.SimpleMessageDispatcher)

    async def start_bot(self):
        await self.application.initialize()
        await self.application.start()
        assert self.application.updater
        await self.application.updater.start_polling()

    async def send_xmpp_message(self, update: Update):
        async with self.xmpp_client.connected():
            target_jid = aioxmpp.JID.fromstr(f"mediator@{test._DEFAULT_DOMAIN}")
            msg = aioxmpp.stanza.Message(to=target_jid,
                                         from_=self.jid,
                                         type_=aioxmpp.MessageType.CHAT)

            assert update.message
            msg.body[None] = f"{update.message.text}"

            res = await self.xmpp_client.send(msg)

class WebServiceMediatorAgent(test.TestAgent):
    class WebServiceReceiverBehavior(CyclicBehaviour):
        async def run(self):
            print("Waiting Message")
            msg = await self.receive(timeout=10)

            if msg:
                print(f"Message received with content: {msg.body}, from: {msg.sender}")
                reply = msg.make_reply()
                reply.body = f"{msg.body}"
                reply.to = "telegram@localhost"
                await self.send(reply)
            else:
                print("Did not receive any message after 10 seconds")

    async def setup(self):
        self.add_behaviour(self.WebServiceReceiverBehavior())


class TestExample(test.SharedXmppServiceTestCase, unittest.IsolatedAsyncioTestCase):
    async def test_telegram_echo(self):
        test.xmpp_service().add_user("telegram", "telegram_test")  # necessary line to authenticate the telegram agent and to reply

        telegram_bot = TelegramBot()
        await telegram_bot.start_bot()

        loop = asyncio.get_running_loop()
        with WebServiceMediatorAgent("mediator") as mediatorAgent:
            await mediatorAgent.async_await()

        await telegram_bot.application.updater.stop()
        await telegram_bot.application.stop()


if __name__ == '__main__':
    unittest.main()

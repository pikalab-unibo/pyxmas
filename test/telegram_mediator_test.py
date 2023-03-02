import asyncio
import test
import unittest
import pyxmas

from spade.behaviour import CyclicBehaviour
from spade.template import Template

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext, Updater, MessageHandler

def get_token():
    with open('token', 'r') as fin:
        return fin.readline()

class TelegramAgent(test.TestAgent):
    class WebServiceSenderBehavior(pyxmas.Behaviour):
        async def run(self):
            print("Waiting message from telegram")
            msg = await self.queue.get()

            print("Message: ", msg)
            if msg:
                print("Message received from Telegram with content: {}".format(msg.body))
            else:
                print("Did not receive any message from Telegram")

            message = self.new_message(recipient='mediator', payload=msg)
            self.log(msg=f"Sending message {message}")
            await self.send(message)

    async def echo_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await self.queue.put(update.message.text)
        await update.message.reply_text(f"Message ({update.message.text}) sent")

    async def setup(self):
        self.queue = asyncio.Queue()
    
        application = Application.builder().token(get_token()).build()
        application.add_handler(MessageHandler(None, self.echo_command))
        await application.initialize()
        await application.updater.start_polling()

        print("TELEGRAM STARTING")
        
        await application.start()

        print("TELEGRAM SETUP COMPLETE")
        self.add_behaviour(self.WebServiceSenderBehavior())

class WebServiceMediatorAgent(test.TestAgent):
    class WebServiceReceiverBehavior(CyclicBehaviour):
        async def run(self):
            print("Waiting Message")
            msg = await self.receive(timeout=10)    

            if msg:
                print("Message received with content: {}".format(msg.body))
            else:
                print("Did not receive any message after 10 seconds")

    async def setup(self):
        self.add_behaviour(self.WebServiceReceiverBehavior())

class TestExample(test.SharedXmppServiceTestCase):
    def test_telegram_echo(self):
        with WebServiceMediatorAgent("mediator") as mediatorAgent:
            with TelegramAgent("telegram") as telegramAgent:
                mediatorAgent.sync_await()
                telegramAgent.sync_await()

if __name__ == '__main__':
    unittest.main()
import pyxmas
from pyxmas.protocol import messages
import pyxmas.protocol.data as data
import aioxmpp
import json
from spade.message import Message

from pyxmas.protocol.explainee import ExplaineeBehaviour


class ExplaineeAgent(pyxmas.Agent):
    def __init__(self,  jid: str, password: str, user_id: str, verify_security: bool = False, thread=None):
        super().__init__(jid, password, verify_security)
        self.user_id = user_id

    class EXP_Behaviour(ExplaineeBehaviour):
        def __init__(self, user_id: str, recipient: str,  query: data.Query = None, thread: str = None, impl: data.Types = None):
            query = self.receive()
            super().__init__(query, recipient, thread, impl)
            self.user_id = user_id
            
        async def on_error(self, error: Exception) -> None:
            # Implement error handling logic here
            pass

        async def handle_recommendation(self, message: messages.RecommendationMessage) -> messages.ResponseToRecommendationMessage:

            # Placeholder for implementation
            # Determine the type of response to send based on the recommendation
            handler = f"handler-{self.user_id}@localhost"
            response = json.dumps(message.recommendation.response)
            msg = Message(to=handler,body=response)
            print(f"Sending recommendation {msg}")
            await self.send(msg)
      
            return messages.WhyMessage.create(query=message.query, recommendation=message.recommendation, to=self.recipient)

        async def handle_details(self, message: messages.MoreDetailsMessage) -> messages.ResponseToMoreDetailsMessage:
            # Implement handling for more details message
             
                response = await self.receive()

                response = response.body

                response = json.loads(response)

                feedback = response["feedback"]

                print(feedback)

                if feedback == "Accepted":
                    return messages.AcceptMessage.create(query=message.query,recommendation=message.recommendation,to=self.recipient)
                

        async def handle_comparison(self,
                                    message: messages.ComparisonMessage
                                    ) -> messages.ResponseToComparisonMessage:
            "Implement This Methos"

        async def handle_invalid_alternative(self,
                                            message: messages.InvalidAlternativeMessage
                                            ) -> messages.ResponseToInvalidAlternativeMessage:
            "Implement This Methos"


    async def setup(self):
        behaviour = self.EXP_Behaviour(user_id=self.user_id, recipient=f"recommender-{self.user_id}@localhost")
        self.add_behaviour(behaviour)
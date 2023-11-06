from typing import Any, Coroutine
import pyxmas
from .protocol import messages
import spade
import spade.agent
import spade.behaviour


from .protocol.explainee import ExplaineeBehaviour, _get_all_state_classes
import pyxmas.protocol.data as data


class ExplaineeAgent(pyxmas.Agent):

    def __init__(self, jid: str, password: str, verify_security: bool = False):
        super().__init__(jid, password, verify_security)
                

    class EXP_Behaviour(ExplaineeBehaviour):
            
            def __init__(self, query: data.Query, recipient: str, thread: str = None, impl: data.Types = None):
                super().__init__(query, recipient, thread, impl)


            async def on_error(self, error: Exception) -> None:
                "Implement This Methos"

            async def handle_recommendation(self,
                                            message: messages.RecommendationMessage
                                            ) -> messages.ResponseToRecommendationMessage:
                "Implement This Methos -- ResponseToRecommendationMessage = Union[WhyMessage, WhyNotMessage, AcceptMessage, CollisionMessage, DisapproveMessage]"

                #Place hodler for later implementation
                answer = 0
                
                if answer == 0:
                    return messages.WhyMessage.create(query=message.query,recommendation=message.recommendation,to=self.recipient)
                
                elif answer == 1:
                    return messages.WhyNotMessage.create(query=message.query,recommendation=message.recommendation,to=self.recipient)
                
                elif answer == 2:
                    return messages.AcceptMessage.create(query=message.query,recommendation=message.recommendation,to=self.recipient)
                
                elif answer == 3:
                    return messages.CollisionMessage.create(query=message.query,recommendation=message.recommendation,to=self.recipient)
                
                elif answer == 4:
                    return messages.DisapproveMessage.create(query=message.query,recommendation=message.recommendation,to=self.recipient)
                

            async def handle_details(self,
                                    message: messages.MoreDetailsMessage
                                    ) -> messages.ResponseToMoreDetailsMessage:
                "Implement This Methos"

                #Place hodler for later implementation
                answer = 2
                
                if answer == 0:
                    return messages.WhyMessage.create(query=message.query,recommendation=message.recommendation,to=self.recipient)
                
                elif answer == 1:
                    return messages.WhyNotMessage.create(query=message.query,recommendation=message.recommendation,to=self.recipient)
                
                elif answer == 2:
                    return messages.AcceptMessage.create(query=message.query,recommendation=message.recommendation,to=self.recipient)
                
                elif answer == 3:
                    return messages.CollisionMessage.create(query=message.query,recommendation=message.recommendation,to=self.recipient)
                
                elif answer == 4:
                    return messages.DisapproveMessage.create(query=message.query,recommendation=message.recommendation,to=self.recipient)
                

            async def handle_comparison(self,
                                        message: messages.ComparisonMessage
                                        ) -> messages.ResponseToComparisonMessage:
                "Implement This Methos"

            async def handle_invalid_alternative(self,
                                                message: messages.InvalidAlternativeMessage
                                                ) -> messages.ResponseToInvalidAlternativeMessage:
                "Implement This Methos"

    async def setup(self):
        query = data.Query(user_id="TestPerson")
        self.add_behaviour(self.EXP_Behaviour(query=query, recipient="recommender@localhost"))    



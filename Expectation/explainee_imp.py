import pyxmas
from pyxmas.protocol import messages
from .UI_message_handler import get_feedback
import requests
from pyxmas.protocol.explainee import ExplaineeBehaviour, _get_all_state_classes
import pyxmas.protocol.data as data


class ExplaineeAgent(pyxmas.Agent):

    def __init__(self, jid: str, password: str, verify_security: bool = False):
        super().__init__(jid, password, verify_security)      
        

    class EXP_Behaviour(ExplaineeBehaviour):
            
            def __init__(self, query: data.Query, recipient: str, thread: str = None, impl: data.Types = None, baseIP = "http://127.0.0.1:8000"):
                super().__init__(query, recipient, thread, impl)
                self.baseIP = baseIP
                self.activeLearningAPI = baseIP + "/active-learning"
                self.explanationAPI = baseIP + "/explanation-generation"
                self.recommendationAPI = baseIP + "/recommendation"
                self.user_id = "34"  
                

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
                

            async def handle_details(self,
                                    message: messages.MoreDetailsMessage
                                    ) -> messages.ResponseToMoreDetailsMessage:
                "Implement This Methos"

                #Place hodler for later implementation

                url = f"http://127.0.0.1:1234/get-feedback/{self.user_id}"
                answer = ""
                try:
                    response = requests.get(url)
                    response.raise_for_status()
                    answer = response.json()
                except requests.RequestException as e:
                    print(f"An error occurred: {e}")
            
                print(answer)
            
                accepted = answer["accepted"]

                feedback = answer["feedback"]

                if answer == 0:
                    return messages.WhyMessage.create(query=message.query,recommendation=message.recommendation,to=self.recipient)
                
                elif answer == 1:
                    return messages.WhyNotMessage.create(query=message.query,recommendation=message.recommendation,to=self.recipient)
                
                elif accepted:
                    return messages.AcceptMessage.create(query=message.query,recommendation=message.recommendation,to=self.recipient)
                
                elif answer == 3:
                    return messages.CollisionMessage.create(query=message.query,recommendation=message.recommendation,to=self.recipient)
                
                elif not accepted:
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
        query = data.Query(user_id= "34")
        self.add_behaviour(self.EXP_Behaviour(query=query, recipient="recommender@localhost"))    



import pyxmas
from pyxmas.protocol import data
import spade
import spade.agent
import spade.behaviour
from typing import Iterable, Callable, List
import requests
import json

from pyxmas.protocol.recommender import RecommenderBehaviour, _get_all_state_classes
import pyxmas.protocol.data as datas
from pyxmas.protocol.messages import get_default_data_types


class RecommenderAgent(pyxmas.Agent):

    class REC_Behaviour(RecommenderBehaviour):
               
            def __init__(self, thread: str = None, impl: data.Types = None, baseIP = "http://127.0.0.1:8000"):
                super().__init__(impl=get_default_data_types())
                self.baseIP = baseIP
                self.activeLearningAPI = baseIP + "/active-learning"
                self.explanationAPI = baseIP + "/explanation-generation"
                self.recommendationAPI = baseIP + "/recommendation"

            async def on_error(self, error: Exception) -> None:
                "Implement This Methos"
      
            async def compute_recommendation(self, message: data.Query) -> data.Recommendation:
                "Implement This Methos"
                url = self.explanationAPI + "/get-recommendation"
                headers = {'Content-Type': 'application/json'}
                data = {'uuid': message.user_id}
                response = requests.post(url, headers=headers, data=json.dumps(data))

                response.raise_for_status()  # raises exception when not a 2xx response
                if response.status_code != 204:
                    response =  response.json()
                else:
                    raise Exception("Empty JSON Object")  
            
                recommendation = datas.Recommendation(response)
                return recommendation



            async def compute_explanation(self, message: data.Query, recommendation: data.Recommendation) -> data.Explanation:
                "Implement This Methos"

                return data.Explanation(reccommandation = recommendation)

            async def compute_contrastive_explanation(self,
                                                    message: data.Query,
                                                    recommendation: data.Recommendation,
                                                    alternative: data.Recommendation) -> data.Explanation:
                "Implement This Methos"

            async def is_valid(self,
                            message: data.Query,
                            recommendation: data.Recommendation,
                            alternative: data.Recommendation) -> bool:
                "Implement This Methos"

            async def on_collision(self,
                                message: data.Query,
                                recommendation: data.Recommendation,
                                feature: data.Feature):
                "Implement This Methos"

            async def on_disagree(self,
                                message: data.Query,
                                recommendation: data.Recommendation,
                                motivation: data.Motivation):
                "Implement This Methos"

            async def on_accept(self,
                                message: data.Query,
                                recommendation: data.Recommendation,
                                explanation: data.Explanation = None):
                "Implement This Methos"

            async def on_unclear(self,
                                message: data.Query,
                                recommendation: data.Recommendation,
                                explanation: data.Explanation
                                ):
                "Implement This Methos"

            async def on_prefer_alternative(self,
                                message: data.Query,
                                recommendation: data.Recommendation,
                                alternative: data.Recommendation
                                ):
                "Implement This Methos"

            async def on_override_alternative(self,
                                message: data.Query,
                                recommendation: data.Recommendation,
                                alternative: data.Recommendation
                                ):
                "Implement This Methos"
                
    async def setup(self):
        self.add_behaviour(self.REC_Behaviour())    



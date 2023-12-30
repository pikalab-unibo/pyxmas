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

    def __init__(self, jid: str, password: str, verify_security: bool = False, thread= None):
        super().__init__(jid, password, verify_security)
        self.thread = thread


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
                url = "http://127.0.0.1:8000/explanation-generation/get-recipe"
                serialized_data = json.dumps(message.JSON)

                try:
                    internal_response = requests.post(url, data=serialized_data, headers={"Content-Type": "application/json"})
                    internal_response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    print(e)
            
                recommendation = datas.Recommendation(internal_response.json())
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
                "{'uuid': 'ESd', 'unwantedIngredients': ['Sauce', 'Apple']}"

                feedback = {"uuid" : message.user_id, "unwantedIngredients":feature.list}

                print(f"Sending feedback {feedback}")

                url = "http://127.0.0.1:8000/save-constraints"

                serialized_data = json.dumps(feedback)

                try:
                    internal_response = requests.post(url, data=serialized_data, headers={"Content-Type": "application/json"})
                    internal_response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    print(e)

                self.memory['history'].append(self.memory["history"][0])


            async def on_disagree(self,
                                message: data.Query,
                                recommendation: data.Recommendation,
                                motivation: data.Motivation):
                
                ingredients = {i : 0 for i in motivation.list}
                
                feedback = { "uuid": message.user_id, "obj_name": "feedback", "obj_id": recommendation.recipe_id, "obj": {"item_label": False, "item_id": recommendation.recipe_id,  "feedback": ingredients } }

                print(f"Sending feedback {feedback}")

                url = "http://127.0.0.1:8000/active-learning/save-user-response"

                serialized_data = json.dumps(feedback)

                try:
                    internal_response = requests.post(url, data=serialized_data, headers={"Content-Type": "application/json"})
                    internal_response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    print(e)

                self.memory['history'].append(self.memory["history"][0])

                url  ="http://127.0.0.1:8000/active-learning/active_learning_feedback_and_update_step"

                user_id = {"uuid" : message.user_id}
                serialized_data = json.dumps(user_id)

                try:
                    internal_response = requests.post(url, data=serialized_data, headers={"Content-Type": "application/json"})
                    internal_response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    print(e)


            async def on_accept(self,
                                message: data.Query,
                                recommendation: data.Recommendation,
                                explanation: data.Explanation = None):
                
                url = "http://127.0.0.1:8000/explanation-generation/end-negotiation"

                serialized_data = json.dumps(message.JSON)

                try:
                    internal_response = requests.post(url, data=serialized_data, headers={"Content-Type": "application/json"})
                    internal_response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    print(e)

            
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
        print("Setup is called")
        self.add_behaviour(self.REC_Behaviour())    



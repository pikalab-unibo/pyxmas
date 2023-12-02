import pyxmas
from pyxmas.protocol import messages
import requests
from pyxmas.protocol.explainee import ExplaineeBehaviour, _get_all_state_classes
import pyxmas.protocol.data as data
import pickle 
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import os
import threading
import pandas as pd

path = os.getcwd() + "/Expectation"

def save(df,filename):
    with open(path + "/" + filename, 'wb') as file:
        pickle.dump(df, file)

#Watchdog Signal Observer
class startInteraction(FileSystemEventHandler):
    def __init__(self,user_id):
        self.user_id = user_id
        self.stop = False

    def method_to_run(self):

        interaction = pd.read_pickle(path + f"/interaction-{self.user_id}.pickle")

        print(interaction)
        
        if self.user_id in interaction.index.values:
            print("Interaction started!")
            self.stop = True

    def on_modified(self, event):
        # Check if the modified file is 'interaction.pickle'
        print(event.src_path)
        print(os.path.basename(event.src_path))

        if os.path.basename(event.src_path) == f"interaction-{self.user_id}.pickle":
            self.method_to_run()


def start_observer(event_handler):
    observer = Observer()
    # Schedule the observer for the directory containing 'interaction.pickle'
    path = os.getcwd() + "/Expectation"

    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    print(f"Observer started at {path}")  # Debugging print
    try:
        while not event_handler.stop:
            time.sleep(1)
            if event_handler.stop:
                return

    except KeyboardInterrupt:
        observer.stop()
    observer.join()


#Watchdog Signal Observer
class Feedback(FileSystemEventHandler):
    def __init__(self,user_id):
        self.user_id = user_id
        self.stop = False

    def method_to_run(self):

        interaction = pd.read_pickle(path + f"/interaction-{self.user_id}.pickle")

        print(interaction)
        
        if self.user_id in interaction.index.values:
            print("Feedback Recived!")
            self.stop = True

    def on_modified(self, event):
        # Check if the modified file is 'interaction.pickle'
        print(event.src_path)
        print(os.path.basename(event.src_path))

        if os.path.basename(event.src_path) == f"interaction-{self.user_id}.pickle":
            self.method_to_run()


def start_observer(event_handler):
    observer = Observer()
    # Schedule the observer for the directory containing 'interaction.pickle'
    path = os.getcwd() + "/Expectation"

    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    print(f"Observer started at {path}")  # Debugging print
    try:
        while not event_handler.stop:
            time.sleep(1)
            if event_handler.stop:
                observer.stop()
                return

    except KeyboardInterrupt:
        observer.stop()
    observer.join()


class ExplaineeAgent(pyxmas.Agent):

    def __init__(self, jid: str, password: str,user_id:str, verify_security: bool = False):
        super().__init__(jid, password, verify_security)      
        self.user_id = user_id
        self.recommendation_df = None

        # Check if the file 'recommendation.pickle' exists
        if not os.path.exists(path + f"/recommendation-{self.user_id}.pickle"):
            self.recommendation_df = pd.DataFrame({"JSON" : []})
            save(self.recommendation_df,f"recommendation-{user_id}.pickle")

        with open(path + f"/recommendation-{self.user_id}.pickle", 'rb') as file:
                self.recommendation_df = pickle.load(file)


    class EXP_Behaviour(ExplaineeBehaviour):
            
            def __init__(self, user_id : str, query: data.Query, recipient: str, thread: str = None, impl: data.Types = None, baseIP = "http://127.0.0.1:8000"):
                super().__init__(query, recipient, thread, impl)
                self.baseIP = baseIP
                self.activeLearningAPI = baseIP + "/active-learning"
                self.explanationAPI = baseIP + "/explanation-generation"
                self.recommendationAPI = baseIP + "/recommendation"
                self.user_id = user_id 
                self.recommendation_df = pd.read_pickle(path + f"/recommendation-{self.user_id}.pickle") 
                

            async def on_error(self, error: Exception) -> None:
                "Implement This Methos"

            async def handle_recommendation(self,
                                            message: messages.RecommendationMessage
                                            ) -> messages.ResponseToRecommendationMessage:
                "Implement This Methos -- ResponseToRecommendationMessage = Union[WhyMessage, WhyNotMessage, AcceptMessage, CollisionMessage, DisapproveMessage]"

                
                self.recommendation_df.loc[self.user_id] = [message.recommendation.response]

                print()

                print()

                print(self.recommendation_df)

                save(self.recommendation_df, f"recommendation-{self.user_id}.pickle")
                #Place hodler for later implementation
                answer = 0
                
                if answer == 0:
                    return messages.WhyMessage.create(query=message.query,recommendation=message.recommendation,to=self.recipient)
                

            async def handle_details(self,
                                    message: messages.MoreDetailsMessage
                                    ) -> messages.ResponseToMoreDetailsMessage:
                "Implement This Methos"

                #Place hodler for later implementation
            
            
                handler = Feedback(user_id=self.user_id)
                start_observer(handler)

                interaction = pd.read_pickle(path + f"/interaction-{self.user_id}.pickle")
      
                accepted = interaction.loc[self.user_id, "Accepted"]

                answer = -1

                # Feedback = { type:Explanation, Recommendation, content: {type: Positive, Negative}, {type: Not conving,More Details,...} }
                feedback = interaction.loc[self.user_id, "Feedback"]

                if accepted == True:
                    return messages.WhyMessage.create(query=message.query,recommendation=message.recommendation,to=self.recipient)
                

            async def handle_comparison(self,
                                        message: messages.ComparisonMessage
                                        ) -> messages.ResponseToComparisonMessage:
                "Implement This Methos"

            async def handle_invalid_alternative(self,
                                                message: messages.InvalidAlternativeMessage
                                                ) -> messages.ResponseToInvalidAlternativeMessage:
                "Implement This Methos"

    async def setup(self):
        handler = startInteraction(user_id=self.user_id)
        start_observer(handler)
        print("Sending First Query")
        interaction = pd.read_pickle(path + f"/interaction-{self.user_id}.pickle")
        query = data.Query(interaction.at[self.user_id,"JSON"])
        self.add_behaviour(self.EXP_Behaviour(user_id=self.user_id,query=query, recipient=f"recommender-{self.user_id}@localhost"))    



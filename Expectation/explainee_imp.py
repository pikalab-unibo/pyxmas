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
import pandas as pd

# Define base path for interactions and recommendations
base_path = os.getcwd() + "/Expectation/"

def save(df, filename, folder):
    with open(os.path.join(folder, filename), 'wb') as file:
        pickle.dump(df, file)

# Function to load or initialize dataframe
def load_or_initialize_df(user_id, folder_name, file_name, columns):
    folder = os.path.join(base_path, folder_name, user_id)
    if not os.path.exists(folder):
        os.makedirs(folder)

    file_path = os.path.join(folder, file_name)
    if not os.path.exists(file_path):
        return pd.DataFrame(columns=columns)
    else:
        with open(file_path, 'rb') as file:
            return pickle.load(file)

# Function to start an observer for a given path
def start_observer(event_handler, folder_name):
    observer = Observer()
    path = os.path.join(base_path, folder_name, event_handler.user_id)
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

# Watchdog Signal Observer for Interaction
class StartInteraction(FileSystemEventHandler):
    def __init__(self, user_id):
        self.user_id = user_id
        self.stop = False

    def method_to_run(self):
        interaction = pd.read_pickle(base_path + "interactions/" + f"{self.user_id}/" + f"interaction-{self.user_id}.pickle")
        print(interaction)

        if self.user_id in interaction.index.values:
            print("Started Interaction!")
            self.stop = True

    def on_modified(self, event):
        if os.path.basename(event.src_path) == f"interaction-{self.user_id}.pickle":
            self.method_to_run()

class Feedback(FileSystemEventHandler):
    def __init__(self, user_id):
        self.user_id = user_id
        self.stop = False

    def method_to_run(self):
        interaction = pd.read_pickle(base_path + "interactions/" + f"{self.user_id}/" + f"interaction-{self.user_id}.pickle")
        print(interaction)

        if self.user_id in interaction.index.values:
            print("Feedback Recieved!")
            self.stop = True

    def on_modified(self, event):
        if os.path.basename(event.src_path) == f"interaction-{self.user_id}.pickle":
            self.method_to_run()

class ExplaineeAgent(pyxmas.Agent):
    def __init__(self,  jid: str, password: str, user_id: str, verify_security: bool = False, thread=None):
        super().__init__(jid, password, verify_security)
        self.user_id = user_id
        self.thread = thread

        # Load or initialize the recommendation dataframe
        self.recommendation_df = load_or_initialize_df(
            user_id, "recommendations", f"recommendation-{user_id}.pickle", ["JSON"]
        )

    class EXP_Behaviour(ExplaineeBehaviour):
        def __init__(self, user_id: str, query: data.Query, recipient: str, thread: str = None, impl: data.Types = None, baseIP = "http://127.0.0.1:8000"):
            super().__init__(query, recipient, thread, impl)
            self.baseIP = baseIP
            self.activeLearningAPI = baseIP + "/active-learning"
            self.explanationAPI = baseIP + "/explanation-generation"
            self.recommendationAPI = baseIP + "/recommendation"
            self.user_id = user_id
            self.recommendation_df = load_or_initialize_df(
                user_id, "recommendations", f"recommendation-{user_id}.pickle", ["JSON"]
            )
            
        async def on_error(self, error: Exception) -> None:
            # Implement error handling logic here
            pass

        async def handle_recommendation(self, message: messages.RecommendationMessage) -> messages.ResponseToRecommendationMessage:
            # Process the recommendation message and update the dataframe
            self.recommendation_df.loc[self.user_id] = [message.recommendation.response]
            save(self.recommendation_df, f"recommendation-{self.user_id}.pickle", os.path.join(base_path, "recommendations/", self.user_id))

            # Placeholder for implementation
            # Determine the type of response to send based on the recommendation
            answer = 0
            if answer == 0:
                return messages.WhyMessage.create(query=message.query, recommendation=message.recommendation, to=self.recipient)

        async def handle_details(self, message: messages.MoreDetailsMessage) -> messages.ResponseToMoreDetailsMessage:
            # Implement handling for more details message
             
                handler = Feedback(user_id=self.user_id)
                start_observer(handler,folder_name="interactions")

                interaction = pd.read_pickle(base_path + "/interactions/" + f"{self.user_id}/" + f"interaction-{self.user_id}.pickle")
      
                accepted = interaction.loc[self.user_id, "Accepted"]

                answer = -1

                # Feedback = { type:Explanation, Recommendation, content: {type: Positive, Negative}, {type: Not conving,More Details,...} }
                feedback = interaction.loc[self.user_id, "Feedback"]

                if accepted == True:
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
            # Start the interaction observer
            handler = StartInteraction(user_id=self.user_id)
            start_observer(handler, "interactions")
            print("Sending First Query")

            # Load interaction data and send the first query
            interaction = pd.read_pickle(base_path + "interactions/" + f"{self.user_id}/" + f"interaction-{self.user_id}.pickle")
            query = data.Query(interaction.at[self.user_id, "JSON"])
            self.add_behaviour(self.EXP_Behaviour(user_id=self.user_id,query=query, recipient=f"recommender-{self.user_id}@localhost"))  
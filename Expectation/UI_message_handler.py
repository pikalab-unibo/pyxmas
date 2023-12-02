from fastapi import FastAPI, HTTPException, Request, status
import requests
import json
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import pandas as pd
import pickle 
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import threading

# Helper function to save a DataFrame as a pickle file in the specified directory
def save(df, filename, folder):
    with open(os.path.join(folder, filename), 'wb') as file:
        pickle.dump(df, file)

class getRecommendation(FileSystemEventHandler):
    def __init__(self, user_id, event):
        self.user_id = user_id
        self.event = event
        self.stop = False

    def method_to_run(self):
        recommendation_file = os.path.join(os.getcwd(), "recommendations", self.user_id, f"recommendation-{self.user_id}.pickle")
        recommendations = pd.read_pickle(recommendation_file)
        if self.user_id in recommendations.index.values:
            print("Recommendation Arrived!")
            self.event.set()  # Signal that the recommendation has arrived
            self.stop = True

    def on_modified(self, event):
        # Check if the modified file is the specific user's recommendation file
        if os.path.basename(event.src_path) == f"recommendation-{self.user_id}.pickle":
            self.method_to_run()

# Function to start an observer for a specific user's recommendation folder
def start_observer(event_handler, user_id):
    observer = Observer()
    # Set the path to the specific user's recommendation folder
    path = os.path.join(os.getcwd(), "recommendations", user_id)
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    print(f"Observer started for user {user_id}")

    try:
        while not event_handler.stop:
            time.sleep(1)
            if event_handler.stop:
                observer.stop()
                return

    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# FastAPI instance and CORS middleware setup
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Endpoint to handle recipe recommendation requests
@app.post("/explanation-generation/get-recipe")
async def getRecipe(request: Request):
    request_data = await request.json()
    user_id = request_data["uuid"]
    feedback = request_data["feedback"]

    folder = os.path.join(os.getcwd(), "interactions", user_id)

    if not os.path.exists(folder):
        os.makedirs(folder)

    interaction_file = os.path.join(folder, f'interaction-{user_id}.pickle')
    if not os.path.exists(interaction_file):
        interaction = pd.DataFrame({"Accepted": [], "Feedback": [], "JSON":[]})
        save(interaction, f'interaction-{user_id}.pickle', folder)

    with open(interaction_file, 'rb') as file:
        interaction = pickle.load(file)

    if user_id not in interaction.index.values:
        interaction.loc[user_id] = [False, "", request_data]
    else:
        interaction.at[user_id, 'Feedback'] = feedback
        interaction.at[user_id, 'JSON'] = request_data

    save(interaction, f'interaction-{user_id}.pickle', folder)
    print(interaction.loc[user_id])

    event = threading.Event()
    handler = getRecommendation(user_id, event)
    start_observer(handler,user_id)

    # Wait for the recommendation to arrive
    event.wait()

    print("Returning Recommendation")
    recommendation_file = os.path.join(os.getcwd(), "recommendations", user_id, f"recommendation-{user_id}.pickle")
    recommendations = pd.read_pickle(recommendation_file)
    recommendation = recommendations.loc[user_id]["JSON"]

    return recommendation


@app.post("/explanation-generation/end-negotiation")
async def endNego(request: Request):
    print("Accepted")

    request_data = await request.json()
    user_id = request_data["uuid"]

    # Define the folder and file paths
    folder = os.path.join(os.getcwd(), "interactions", user_id)
    interaction_file = os.path.join(folder, f'interaction-{user_id}.pickle')

    # Load the interaction data
    with open(interaction_file, 'rb') as file:
        interaction = pickle.load(file)

    # Update the interaction data
    interaction.loc[user_id] = [True, "", ""]

    save(interaction, f'interaction-{user_id}.pickle', folder)
    print(interaction.loc[user_id])

    # Serialize the request data and make an internal POST request
    serialized_data = json.dumps(request_data)
    url = "http://127.0.0.1:8000/explanation-generation/end-negotiation"

    try:
        internal_response = requests.post(url, data=serialized_data, headers={"Content-Type": "application/json"})
        internal_response.raise_for_status()
        return internal_response.json()
    except requests.exceptions.RequestException as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")




# Rest of this is just being forwarded 

# Home Route Forwards
@app.post("/register")
async def register(request: Request):

    request_data = await request.json()
    print(request_data)
    user_id = request_data["username"]

    folder = os.path.join(os.getcwd(), "interactions", user_id)

    if not os.path.exists(folder):
        os.makedirs(folder)

    interaction_file = os.path.join(folder, f'interaction-{user_id}.pickle')
    if not os.path.exists(interaction_file):
        interaction = pd.DataFrame({"Accepted": [], "Feedback": [], "JSON":[]})
        save(interaction, f'interaction-{user_id}.pickle', folder)

    path =  os.path.dirname(os.getcwd())

    if not os.path.exists("lobby"):
        lobby = pd.DataFrame({"Username":[]})
        save(lobby,path + "/lobby.pickle", folder="")

    with open(path + "/lobby.pickle", 'rb') as file:
            lobby = pickle.load(file)

    user_name = request_data["username"]
    lobby.loc[user_name] = "Active"
    save(lobby,path + "/lobby.pickle", folder="")

    url = "http://127.0.0.1:8000/register"

    try:
        request_data = await request.json()
        internal_response = requests.post(url, json=request_data)
        internal_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

    return internal_response.json()

@app.post("/get-user-categories")
async def register(request: Request):

    url = "http://127.0.0.1:8000/get-user-categories"

    try:
        request_data = await request.json()
        internal_response = requests.post(url, json=request_data)
        internal_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

    return internal_response.json()

@app.post("/save-user-profile")
async def register(request: Request):

    url = "http://127.0.0.1:8000/save-user-profile"

    try:
        request_data = await request.json()
        internal_response = requests.post(url, json=request_data)
        internal_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

    return internal_response.json()


@app.post("/save-preferences")
async def register(request: Request):

    url = "http://127.0.0.1:8000/save-preferences"

    try:
        request_data = await request.json()
        internal_response = requests.post(url, json=request_data)
        internal_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

    return internal_response.json()

@app.post("/get-recipe-ingredients")
async def register(request: Request):

    url = "http://127.0.0.1:8000/get-recipe-ingredients"

    try:
        request_data = await request.json()
        internal_response = requests.post(url, json=request_data)
        internal_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

    return internal_response.json()

@app.post("/save-constraints")
async def register(request: Request):

    url = "http://127.0.0.1:8000/save-constraints"

    try:
        request_data = await request.json()
        internal_response = requests.post(url, json=request_data)
        internal_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

    return internal_response.json()


#Active Learning Forwards

@app.post("/active-learning/get-init-sample")
async def register(request: Request):

    url = "http://127.0.0.1:8000/active-learning/get-init-sample"

    try:
        request_data = await request.json()
        internal_response = requests.post(url, json=request_data)
        internal_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

    return internal_response.json()

@app.post("/active-learning/save-user-response")
async def register(request: Request):

    url = "http://127.0.0.1:8000/active-learning/save-user-response"

    try:
        request_data = await request.json()
        internal_response = requests.post(url, json=request_data)
        internal_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

    return internal_response.json()

@app.post("/active-learning/submit-feedback-data")
async def register(request: Request):

    url = "http://127.0.0.1:8000/active-learning/submit-feedback-data"

    try:
        request_data = await request.json()
        internal_response = requests.post(url, json=request_data)
        internal_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

    return internal_response.json()

@app.post("/active-learning/active_learning_feedback_and_update_step")
async def register(request: Request):

    url = "http://127.0.0.1:8000/active-learning/active_learning_feedback_and_update_step"

    try:
        request_data = await request.json()
        internal_response = requests.post(url, json=request_data)
        internal_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

    return internal_response.json()


# Recommendation Forwards 
@app.post("/recommendation/generate-user-recommendations")
async def register(request: Request):

    url = "http://127.0.0.1:8000/recommendation/generate-user-recommendations"

    try:
        request_data = await request.json()
        internal_response = requests.post(url, json=request_data)
        internal_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

    return internal_response.json()
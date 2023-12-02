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
import os
import threading


def save(df,filename):
    with open(filename, 'wb') as file:
        pickle.dump(df, file)

class getRecommendation(FileSystemEventHandler):
    def __init__(self, user_id, event):
        self.user_id = user_id
        self.event = event
        self.stop = False

    def method_to_run(self):
        recommendations = pd.read_pickle(f"recommendation-{self.user_id}.pickle")
        if self.user_id in recommendations.index.values:
            print("Recommendation Arrived!")
            self.event.set()  # Signal that the recommendation has arrived
            self.stop = True

    def on_modified(self, event):
        if os.path.basename(event.src_path) == f"recommendation-{self.user_id}.pickle":
            self.method_to_run()

def start_observer(event_handler):
    observer = Observer()
    observer.schedule(event_handler, os.getcwd(), recursive=False)
    observer.start()
    print("Observer started")

    try:
        while not event_handler.stop:
            time.sleep(1)
            if event_handler.stop:
                observer.stop()
                return

    except KeyboardInterrupt:
        observer.stop()
    observer.join()



#API SERVER

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.post("/explanation-generation/get-recipe")
async def getRecipe(request: Request):
    request_data = await request.json()
    user_id = request_data["uuid"]
    feedback = request_data["feedback"]

        # Check if the file 'interaction-{user_id}.pickle' exists
    if not os.path.exists(f'interaction-{user_id}.pickle'):
        interaction = pd.DataFrame({"Accepted": [], "Feedback": [], "JSON":[]})
        save(interaction,f"interaction-{user_id}.pickle")

    with open(f'interaction-{user_id}.pickle', 'rb') as file:
            interaction = pickle.load(file)

    if user_id not in interaction.index.values:
        interaction.loc[user_id] = [False, "", request_data]
    else:
        interaction.at[user_id, 'Feedback'] = feedback
        interaction.at[user_id, 'JSON'] = request_data

    save(interaction, f"interaction-{user_id}.pickle")
    print(interaction.loc[user_id])

    event = threading.Event()
    handler = getRecommendation(user_id, event)
    observer_thread = threading.Thread(target=start_observer, args=(handler,))
    observer_thread.start()

    # Wait for the recommendation to arrive
    event.wait()

    print("Returning Recommendation")
    recommendations = pd.read_pickle(f"recommendation-{user_id}.pickle")
    recommendation = recommendations.loc[user_id]["JSON"]


    return recommendation


@app.post("/explanation-generation/end-negotiation")
async def endNego(request: Request):

    print("Accepted!")

    request_data = await request.json()
    user_id = request_data["uuid"]

    interaction = pd.read_pickle(f"interaction-{user_id}.pickle")

    interaction.loc[user_id] = ["","",""]
    save(interaction,f"interaction-{user_id}.pickle")
    print(interaction.loc[user_id])

    request_data = await request.json()
    serialized_data = json.dumps(request_data)
    url = "http://127.0.0.1:8000/explanation-generation/end-negotiation"

    try:
        internal_response = requests.post(url, data=serialized_data, headers={"Content-Type": "application/json"})
        internal_response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(e)

    return internal_response.json()


# Rest of this is just being forwarded 

# Home Route Forwards
@app.post("/register")
async def register(request: Request):

    if not os.path.exists("lobby"):
        lobby = pd.DataFrame({"Username":[]})
        save(lobby,"lobby.pickle")

    with open("lobby.pickle", 'rb') as file:
            lobby = pickle.load(file)


    request_data = await request.json()
    print(request_data)
    user_name = request_data["username"]
    lobby.loc[user_name] = "Active"
    save(lobby,"lobby.pickle")

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
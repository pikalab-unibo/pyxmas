from fastapi import FastAPI, HTTPException, Request, status
import requests
import json
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import pickle 
import os
import aioxmpp
import asyncio

# Helper function to save a DataFrame as a pickle file in the specified directory
def save(df, filename, folder):
    with open(os.path.join(folder, filename), 'wb') as file:
        pickle.dump(df, file)

# FastAPI instance and CORS middleware setup
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class XMPPReceiver:
    def __init__(self, client):
        self.client = client
        self.queue = asyncio.Queue()
        self.client.stream.register_message_callback(
            aioxmpp.MessageType.CHAT,
            None,
            self.message_callback  # This is a regular function now
        )

    def message_callback(self, msg):
        # Schedule the async handling of the message
        asyncio.create_task(self.handle_message(msg))

    async def handle_message(self, msg):
        # Now an async function to properly await queue operations
        if msg.body:
            print(f"Recieved Message: {msg}")
            print(f"Body: {msg.body}")
            await self.queue.put(msg.body)

    async def get_recommendation(self):
        msg = await self.queue.get()
        msg = msg
        recommendation = next(iter(msg.values()), None)
        print(f"Recommendation is {recommendation}")
        return json.loads(recommendation)


# Endpoint to handle recipe recommendation requests
@app.post("/explanation-generation/get-recipe")
async def getRecipe(request: Request):

    request_data = await request.json()
    user_id = request_data["uuid"]
    recipient = aioxmpp.JID.fromstr(f"{user_id}@localhost")   

    jid = aioxmpp.JID.fromstr(f"handler-{user_id}@localhost")
    security_layer = aioxmpp.make_security_layer('password', no_verify=True)
    client = aioxmpp.PresenceManagedClient(jid, security_layer)

    receiver = XMPPReceiver(client)   

    async with client.connected() as stream:
        msg = aioxmpp.Message(
            to=recipient,
            type_=aioxmpp.MessageType.CHAT,
        )
        msg.body[None] = json.dumps(request_data)
        print(f"Sent: {msg}")
        await stream.send(msg)

    
        recommendation = await receiver.get_recommendation()

    return json.dumps(recommendation)


@app.post("/explanation-generation/end-negotiation")
async def endNego(request: Request):

    print("Accepted")

    request_data = await request.json()
    user_id = request_data["uuid"]
    recipient = aioxmpp.JID.fromstr(f"{user_id}@localhost")  
    request_data["feedbackDetailed"] = "Accepted"

    jid = aioxmpp.JID.fromstr(f"handler-{user_id}@localhost")
    security_layer = aioxmpp.make_security_layer('password', no_verify=True)
    client = aioxmpp.PresenceManagedClient(jid, security_layer)

    receiver = XMPPReceiver(client)   

    async with client.connected() as stream:
        msg = aioxmpp.Message(
            to=recipient,
            type_=aioxmpp.MessageType.CHAT,
        )
        msg.body[None] = json.dumps(request_data)
        print(f"Sent: {msg}")
        await stream.send(msg)

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
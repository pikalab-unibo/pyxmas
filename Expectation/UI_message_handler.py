from fastapi import FastAPI, HTTPException, Request, status
import requests
import json
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import pandas as pd
import pickle 
import os

app = FastAPI()

def save(interaction):
    with open('interaction.pickle', 'wb') as file:
        pickle.dump(interaction, file)

# Check if the file 'interaction.pickle' exists
if not os.path.exists('interaction.pickle'):
    interaction = pd.DataFrame({"Accepted": [], "Feedback": []})
    save(interaction)

with open('interaction.pickle', 'rb') as file:
        interaction = pickle.load(file)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.post("/explanation-generation/get-recipe")
async def save_user_response(request: Request):
    global feedback_user_map, initial

    request_data = await request.json()
    user_id = request_data["uuid"]
    feedback = request_data["feedback"]

    if user_id not in interaction.index.values:
        interaction.loc[user_id] = [False,""]
    else:
        interaction.at[user_id, 'Feedback'] = feedback

    save(interaction)
    print(interaction.loc[user_id])

    url = "http://127.0.0.1:8000/explanation-generation/get-recipe"
    serialized_data = json.dumps(request_data)

    try:
        internal_response = requests.post(url, data=serialized_data, headers={"Content-Type": "application/json"})
        internal_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

    return internal_response.json()


@app.post("/explanation-generation/end-negotiation")
async def save_user_response(request: Request):

    print("Accepted!")

    request_data = await request.json()
    user_id = request_data["uuid"]

    interaction.loc[user_id] = [True,""]
    save(interaction)
    print(interaction.loc[user_id])

    request_data = await request.json()
    serialized_data = json.dumps(request_data)
    url = " http://127.0.0.1:8000/explanation-generation/end-negotiation"

    try:
        internal_response = requests.post(url, data=serialized_data)
        internal_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

    return internal_response.json()

@app.get("/get-feedback/{user_id}")
async def get_feedback(user_id: str):

    timeout = 90  # Timeout in seconds
    end_time = asyncio.get_event_loop().time() + timeout

    while asyncio.get_event_loop().time() < end_time:

        if interaction.at[user_id, 'Accepted']:
            print(interaction.loc[user_id])
            return {"accepted": True, "feedback": ""}
    
        elif interaction.at[user_id, 'Feedback'] != "":
            result = interaction.at[user_id, 'Feedback']
            interaction.at[user_id,"Feedback"] = ""
            print(interaction.loc[user_id])
            save(interaction)
            return {"accepted": False, "feedback": result}
        
        await asyncio.sleep(2)  # Sleep for 2 seconds before checking again

    raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT,
                        detail="Feedback request timed out")










# Rest of this is just being forwarded 

# Home Route Forwards
@app.post("/register")
async def register(request: Request):

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
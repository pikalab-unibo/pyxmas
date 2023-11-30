from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import requests
import json
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

feedback_user_map = dict()

class UserResponse(BaseModel):
    uuid: str
    obj: dict
    obj_name: str
    obj_id: float

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.post("/save-user-response")
async def save_user_response(request: Request):
    # Parse the request body to Python dict
    request_data = await request.json()

    # Validate data using Pydantic model
    try:
        user_response = UserResponse(**request_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid data: {e}")

    feedback_user_map[request_data["uuid"]] = request_data

    url = "http://127.0.0.1:8000/active-learning/save-user-response"

    # Serialize the Pydantic model to JSON
    serialized_data = json.dumps(request_data)

    # Send the POST request to the internal URL
    try:
        internal_response = requests.post(url, data=serialized_data, headers={"Content-Type": "application/json"})
        internal_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

    return {"status": "success", "response": internal_response.json()}


async def get_feedback(user_id):

    global feedback_user_map

    if user_id in feedback_user_map:
        result = feedback_user_map[user_id]
        feedback_user_map.pop(user_id,None)
        print(result)
        return result
    
    else:
        while user_id  not in feedback_user_map:
            ""

            
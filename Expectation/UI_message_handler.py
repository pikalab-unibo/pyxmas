from fastapi import FastAPI, HTTPException, Request, status
import requests
import json
from fastapi.middleware.cors import CORSMiddleware
import asyncio

app = FastAPI()

feedback_user_map = dict()
feedback_lock = asyncio.Lock()
accepted = False
accepted_lock = asyncio.Lock()
initial = True

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
    if initial:
        initial = False

    else:
        async with feedback_lock:
            feedback_user_map[request_data["uuid"]] = request_data["feedback"]

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

    global accepted

    print("Accepted!")

    async with accepted_lock:
        accepted = True

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

    global feedback_user_map, accepted

    if accepted:
        return {"accepted": True, "feedback": ""}

    timeout = 30  # Timeout in seconds
    end_time = asyncio.get_event_loop().time() + timeout

    while asyncio.get_event_loop().time() < end_time:

        async with accepted_lock:
                if accepted:
                    return {"accepted": True, "feedback": ""}
    
        async with feedback_lock:
            if user_id in feedback_user_map:
                result = feedback_user_map.pop(user_id)
                return {"accepted": False, "feedback": result}
        
        await asyncio.sleep(2)  # Sleep for 2 seconds before checking again

    raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT,
                        detail="Feedback request timed out")


            
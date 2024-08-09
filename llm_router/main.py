from fastapi import FastAPI, HTTPException
import requests
import time
from google.cloud import firestore
from pydantic import BaseModel

app = FastAPI()

# Firestore client setup
db = firestore.Client()

# Predefined collection name in Firestore
collection_name = 'llm_endpoints'

# List of predefined endpoints
endpoints = [
    {"ip": "34.162.17.74:80", "region": "us-central1"},
    {"ip": "34.162.150.249:80", "region": "us-east4"},
    {"ip": "34.162.162.249:80", "region": "asia-south1"},
    {"ip": "34.162.197.70:80", "region": "us-east1"},
    {"ip": "34.162.131.187:80", "region": "us-east5"}
]

class PromptRequest(BaseModel):
    prompt: str

# Helper function to update Firestore with response times
def update_response_time(endpoint_ip: str, response_time: float):
    doc_ref = db.collection(collection_name).document(endpoint_ip)
    doc = doc_ref.get()
    
    if doc.exists:
        data = doc.to_dict()
        count = data['count'] + 1
        avg_time = ((data['avg_time'] * data['count']) + response_time) / count
        doc_ref.update({
            'avg_time': avg_time,
            'count': count
        })
    else:
        db.collection(collection_name).document(endpoint_ip).set({
            'avg_time': response_time,
            'count': 1
        })

# Helper function to get the endpoint with the lowest response time
def get_fastest_endpoint():
    docs = db.collection(collection_name).stream()
    fastest_endpoint = None
    lowest_time = float('inf')
    
    for doc in docs:
        data = doc.to_dict()
        if data['avg_time'] < lowest_time:
            lowest_time = data['avg_time']
            fastest_endpoint = doc.id

    return fastest_endpoint

# Main route to handle LLM requests
@app.post("/generate-response")
async def generate_response(request: PromptRequest):
    fastest_endpoint = get_fastest_endpoint()
    if not fastest_endpoint:
        raise HTTPException(status_code=500, detail="No endpoints available")

    endpoint_url = f"http://{fastest_endpoint}/generate-response"
    
    try:
        start_time = time.time()
        response = requests.post(endpoint_url, json={"prompt": request.prompt})
        response_time = time.time() - start_time
        
        update_response_time(fastest_endpoint, response_time)

        return response.json()
    
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to endpoint: {str(e)}")
# Initialize Firestore with endpoints and zero response time if not already present
@app.on_event("startup")
async def startup_event():
    for endpoint in endpoints:
        doc_ref = db.collection(collection_name).document(endpoint['ip'])
        if not doc_ref.get().exists:
            doc_ref.set({
                'avg_time': 0.0,
                'count': 0
            })

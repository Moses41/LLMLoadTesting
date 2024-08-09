from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import random
import time
from typing import Optional

app = FastAPI()

class Payload(BaseModel):
     llm_endpoint: Optional[str] = "http://35.221.38.211/generate-response" # Default endpoint
     llm_endpoints: Optional[list] = ["http://35.221.38.211/generate-response"] # Empty list
     run_time: Optional[str] = "60s"
     users: Optional[int] = 1
     spawn_rate: Optional[int] = 1
     min_tokens: Optional[int] = 1
     max_tokens: Optional[int] = 10
     num_prompts: Optional[int] = 1
     num_experiments: Optional[int] = 1

def generate_prompts(llm_endpoint,num_prompts, min_tokens, max_tokens):
    
     prompt_request = {
         "prompt": f"generate {num_prompts} prompts with each prompt having a token count between {min_tokens} and {max_tokens}. Provide only the final output without any explanation and make it a list format."
     }
     print(f'Intiated prompt generator call: payload is {prompt_request}')
     response = requests.post(llm_endpoint, json=prompt_request)
     if response.status_code != 200:
         raise HTTPException(status_code=response.status_code, detail="Error generating prompts from LLM endpoint")
     print("Finished Prompt generator call")
     content = response.json()["response"]["content"]
     # Assuming the content is a string with each prompt separated by a newline
     generated_prompts = content.strip().split('\n')
     return generated_prompts

@app.post("/start_load_test")
async def start_load_test(payload: Payload):
     print("Entered API")
     load_test_responses = []
     for experiment in range(payload.num_experiments):
         print("Within Experiment loop")
         try:
            generated_prompts = generate_prompts(payload.llm_endpoint,payload.num_prompts, payload.min_tokens, payload.max_tokens)
            # print(generate_prompts)
         except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
         # Randomly pick an endpoint from the list of llm_endpoints
         selected_endpoint = random.choice(payload.llm_endpoints)

         # Prepare the payload for the load testing application
         load_test_payload = {
            "endpoint": selected_endpoint,
            "prompts": generated_prompts,
            "run_time": payload.run_time,
            "users": payload.users,
            "spawn_rate": payload.spawn_rate
         }
         # print(load_test_payload)
         # Call the deployed load testing application
         print(f'Intiated request: payload {load_test_payload}')
         response = requests.post("http://34.162.198.84/start_load_test", json=load_test_payload)
         print("Finished Request")
         if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Error starting load test")
    
         load_test_responses.append(response.json())
         print(f'Length of load_test_response = {len(load_test_responses)}')
         # Wait 30 seconds before starting the next experiment
         time.sleep(3)
    
     return {
         "message": f"Started {payload.num_experiments} load tests",
         "load_test_responses": load_test_responses
     }

# Example FastAPI command to run the server: uvicorn main:app --reload
if __name__ == "__main__":
     import uvicorn
     uvicorn.run(app, host="0.0.0.0", port=8000)
import yaml
from fastapi import FastAPI, Request
import os
import subprocess
from urllib.parse import urlparse

app = FastAPI()

@app.post("/start_load_test")
async def start_load_test(request: Request):
    data = await request.json()

    endpoint = data.get("endpoint")
    prompts = data.get("prompts", [])
    run_time = data.get("run_time", "60s")
    users = data.get("users", 10)
    spawn_rate = data.get("spawn_rate", 10)

    if not endpoint or not prompts:
        return {"error": "Endpoint and prompts are required."}

    # Extract host from endpoint
    parsed_url = urlparse(endpoint)
    host = f"{parsed_url.scheme}://{parsed_url.netloc}"

    config_data = {
        "endpoint": endpoint,
        "prompts": prompts,
        "host": host
    }

    # Write the config data to config.yaml
    config_path = os.path.join('traffic_generator', 'config.yaml')
    with open(config_path, 'w') as file:
        yaml.dump(config_data, file)

    # Start Locust load test using the configuration
    locust_command = [
        "locust",
        # "-f", os.path.join('..', 'traffic_generator', 'traffic_generator.py'),
        "-f", os.path.join('traffic_generator', 'traffic_generator.py'),
        "--host", host,
        "--headless",
        "-u", str(users),
        "-r", str(spawn_rate),
        "--run-time", run_time
    ]
    subprocess.Popen(locust_command)

    return {"message": "Load test started with given parameters."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

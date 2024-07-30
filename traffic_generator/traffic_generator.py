import os
import yaml
import requests
import time
import sys
from locust import HttpUser, task, between, events
from locust.main import main as locust_main

# Ensure the metric_collector module can be found
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from metric_collector.metric_collector import MetricCollector

# Load configuration
config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

endpoint = config['endpoint']
prompts = config['prompts']

# Initialize MetricCollector
metric_collector = MetricCollector()

class UserBehavior(HttpUser):
    wait_time = between(0.5, 2.5)

    def on_start(self):
        self.user_id = id(self)

    @task
    def send_request(self):
        for prompt in prompts:
            metric_collector.increment_concurrent_requests(self.user_id)
            start_time = time.time()
            with self.client.post(endpoint, json={"prompt": prompt}, catch_response=True) as response:
                response_time = time.time() - start_time
                if response.status_code == 200:
                    json_response = response.json()
                    prompt_token_count = json_response["response"]["prompt_token_count"]
                    candidates_token_count = json_response["response"]["candidates_token_count"]
                    total_token_count = json_response["response"]["total_token_count"]
                    metric_collector.add_metric(self.user_id, prompt, response.status_code, response_time, prompt_token_count, candidates_token_count, total_token_count)
                    print(f"User: {self.user_id}, Prompt: {prompt}, Status Code: {response.status_code}, Response Time: {response_time:.4f} seconds, Tokens: {total_token_count}")
                else:
                    metric_collector.add_metric(self.user_id, prompt, response.status_code, response_time, 0, 0, 0)
                    print(f"User: {self.user_id}, Prompt: {prompt}, Status Code: {response.status_code}, Response Time: {response_time:.4f} seconds")

    @events.test_stop.add_listener
    def on_test_stop(environment, **kwargs):
        metric_collector.display_metrics()

if __name__ == "__main__":
    locust_main()

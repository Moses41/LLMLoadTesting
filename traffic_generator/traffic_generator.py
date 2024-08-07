import os
import yaml
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
host = config['host']
users = config['users']
spawn_rate = config['spawn_rate']
run_time = config['run_time']

# Initialize MetricCollector
metric_collector = MetricCollector()

class UserBehavior(HttpUser):
    # wait_time = between(0.5, 2.5)

    def on_start(self):
        self.user_id = id(self)
        metric_collector.add_config(users, spawn_rate, endpoint, host, run_time)
    @task
    def send_request(self):
        for prompt in prompts:
            metric_collector.increment_concurrent_requests(self.user_id)
            start_time = time.time()
            with self.client.post(endpoint, json={"prompt": prompt}, catch_response=True) as response:
                response_time = time.time() - start_time
                if response.status_code == 200:
                    json_response = response.json()
                    # print(f'JSON: {json_response}')
                    prompt_token_count = json_response["response"].get("prompt_token_count", 0)
                    candidates_token_count = json_response["response"].get("candidates_token_count", 0)
                    total_token_count = json_response["response"].get("total_token_count", 0)
                    metric_collector.add_metric(self.user_id, prompt, response.status_code, response_time, prompt_token_count, candidates_token_count, total_token_count)
                    print(f"User: {self.user_id}, Prompt: {prompt}, Status Code: {response.status_code}, Response Time: {response_time:.4f} seconds, Tokens: {total_token_count}")
                else:
                    metric_collector.add_metric(self.user_id, prompt, response.status_code, response_time, 0, 0, 0)
                    print(f"User: {self.user_id}, Prompt: {prompt}, Status Code: {response.status_code}, Response Time: {response_time:.4f} seconds")
                metric_collector.decrement_concurrent_requests(self.user_id)

    @events.test_start.add_listener
    def on_test_start(environment, **kwargs):
        metric_collector.start_traffic()

    @events.test_stop.add_listener
    def on_test_stop(environment, **kwargs):
        try:
            metric_collector.end_traffic()
            metric_collector.display_metrics()
            metric_collector.upload_to_bigquery()
            print("Data upload to BigQuery completed.")
        except Exception as e:
            print(f"Error during BigQuery upload: {e}")


if __name__ == "__main__":
    locust_main()

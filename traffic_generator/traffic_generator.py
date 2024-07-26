import yaml
from locust import HttpUser, task, between, events, LoadTestShape
import os
import gevent
from gevent import monkey

monkey.patch_all()  # Patch standard library to work with gevent

class LoadTestUser(HttpUser):
    wait_time = between(1, 5)  # Simulate user wait time

    def on_start(self):
        # Load configuration from file
        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
        if os.path.exists(config_path):
            with open(config_path, 'r') as file:
                config = yaml.safe_load(file)
                self.prompts = config.get('prompts', [])
                self.endpoint = config.get('endpoint', '')
        else:
            self.prompts = []
            self.endpoint = ''
        self.results = []

    @task
    def send_requests(self):
        if self.prompts and self.endpoint:
            # Use greenlets to perform concurrent requests
            greenlets = [gevent.spawn(self.send_request, prompt) for prompt in self.prompts]
            gevent.joinall(greenlets)

    def send_request(self, prompt):
        response = self.client.post(self.endpoint, json={"prompt": prompt})
        self.results.append((prompt, response.status_code, response.elapsed.total_seconds()))

    def on_stop(self):
        # Print out metrics
        for prompt, status, time in self.results:
            print(f"Prompt: {prompt}, Status Code: {status}, Response Time: {time:.4f} seconds")
        
        # Additional detailed metrics from Locust
        stats = self.environment.stats
        for key, entry in stats.entries.items():
            print(f"Name: {key}, Request Count: {entry.num_requests}, Failures: {entry.num_failures}, "
                  f"Average Response Time: {entry.avg_response_time:.2f} ms, Min Response Time: {entry.min_response_time:.2f} ms, "
                  f"Max Response Time: {entry.max_response_time:.2f} ms")

if __name__ == "__main__":
    import locust.main
    locust.main.main()

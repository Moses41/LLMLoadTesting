import uuid
from tabulate import tabulate
from collections import defaultdict
import threading
import time
from google.cloud import bigquery
from google.oauth2 import service_account
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MetricCollector:
    def __init__(self):
        self.metrics = defaultdict(list)  # Metrics per user
        self.failures = defaultdict(list)  # Failure metrics per user
        self.concurrent_requests = 0
        self.peak_concurrent_requests = 0
        self.user_concurrent_requests = defaultdict(int)
        self.lock = threading.Lock()
        self.start_time = None
        self.end_time = None
        self.experiment_id = self.generate_experiment_id()

        self.users = None
        self.spawn_rate = None
        self.endpoint = None
        self.host = None
        self.run_time = None

    def add_config(self, users, spawn_rate, endpoint, host, run_time):
        self.users = users
        self.spawn_rate = spawn_rate
        self.endpoint = endpoint
        self.host = host
        self.run_time = run_time

    def generate_experiment_id(self):
        return str(uuid.uuid4())

    def add_metric(self, user_id, prompt, status_code, response_time, prompt_token_count, candidates_token_count, total_token_count):
        metric = {
            "prompt": prompt,
            "status_code": status_code,
            "response_time": response_time,
            "prompt_token_count": prompt_token_count,
            "candidates_token_count": candidates_token_count,
            "total_token_count": total_token_count
        }

        if status_code == 200:
            self.metrics[user_id].append(metric)
        else:
            self.failures[user_id].append(metric)

    def increment_concurrent_requests(self, user_id):
        with self.lock:
            self.concurrent_requests += 1
            self.user_concurrent_requests[user_id] += 1
            if self.concurrent_requests > self.peak_concurrent_requests:
                self.peak_concurrent_requests = self.concurrent_requests

    def decrement_concurrent_requests(self, user_id):
        with self.lock:
            self.concurrent_requests -= 1
            self.user_concurrent_requests[user_id] -= 1

    def display_metrics(self):
        overall_table = []
        overall_total_requests = 0
        overall_total_response_time = 0
        overall_total_tokens = 0
        overall_failures = 0
        overall_prompt_tokens = 0
        overall_response_tokens = 0

        logging.info("Displaying User-wise Metrics:")
        for user_id, user_metrics in self.metrics.items():
            user_table = []
            user_total_requests = len(user_metrics) + len(self.failures[user_id])
            user_total_response_time = sum(metric['response_time'] for metric in user_metrics + self.failures[user_id])
            user_total_tokens = sum(metric['total_token_count'] for metric in user_metrics)
            user_total_prompt_tokens = sum(metric['prompt_token_count'] for metric in user_metrics)
            user_total_response_tokens = sum(metric['candidates_token_count'] for metric in user_metrics)
            user_failures = len(self.failures[user_id])
            user_concurrent_requests = self.user_concurrent_requests[user_id]

            for metric in user_metrics + self.failures[user_id]:
                user_table.append([
                    metric['prompt'],
                    metric['status_code'],
                    metric['response_time'],
                    metric['prompt_token_count'],
                    metric['candidates_token_count'],
                    metric['total_token_count']
                ])

            headers = ["Prompt", "Status Code", "Response Time (s)", "Prompt Tokens", "Response Tokens", "Total Tokens"]
            logging.info(f"User ID: {user_id}")
            logging.info(f"\n{tabulate(user_table, headers=headers, tablefmt='pretty')}")

            avg_response_time = user_total_response_time / user_total_requests if user_total_requests > 0 else 0
            rps = user_total_requests / user_total_response_time if user_total_response_time > 0 else 0

            logging.info(f"User {user_id} Analysis:")
            logging.info(f"Total Requests: {user_total_requests}")
            logging.info(f"Total Response Time: {user_total_response_time:.4f} seconds")
            logging.info(f"Average Response Time: {avg_response_time:.4f} seconds")
            logging.info(f"Requests Per Second (RPS): {rps:.4f}")
            logging.info(f"Total Tokens: {user_total_tokens}")
            logging.info(f"Average Tokens Per Request: {user_total_tokens / user_total_requests if user_total_requests > 0 else 0:.4f}")
            logging.info(f"Total Failures: {user_failures}")
            logging.info(f"Concurrent Requests: {user_concurrent_requests}")
            logging.info("-" * 60)

            overall_table.extend(user_table)
            overall_total_requests += user_total_requests
            overall_total_response_time += user_total_response_time
            overall_total_tokens += user_total_tokens
            overall_prompt_tokens += user_total_prompt_tokens
            overall_response_tokens += user_total_response_tokens
            overall_failures += user_failures

        overall_avg_response_time = overall_total_response_time / overall_total_requests if overall_total_requests > 0 else 0
        overall_rps = overall_total_requests / overall_total_response_time if overall_total_response_time > 0 else 0

        logging.info("Overall Analysis:")
        logging.info(f"Total Requests: {overall_total_requests}")
        logging.info(f"Total Response Time: {overall_total_response_time:.4f} seconds")
        logging.info(f"Average Response Time: {overall_avg_response_time:.4f} seconds")
        logging.info(f"Requests Per Second (RPS): {overall_rps:.4f}")
        logging.info(f"Total Tokens Processed: {overall_total_tokens}")
        logging.info(f"Average Tokens Per Request: {overall_total_tokens / overall_total_requests if overall_total_requests > 0 else 0:.4f}")
        logging.info(f"Total Failures: {overall_failures}")
        logging.info(f"Peak Concurrent Requests: {self.peak_concurrent_requests}")
        logging.info(f"Average Prompt Tokens: {overall_prompt_tokens / overall_total_requests if overall_total_requests > 0 else 0:.4f}")
        logging.info(f"Average Response Tokens: {overall_response_tokens / overall_total_requests if overall_total_requests > 0 else 0:.4f}")

    def start_traffic(self):
        self.start_time = time.time()

    def end_traffic(self):
        self.end_time = time.time()

    def upload_to_bigquery(self):
        logging.info("Entered Upload function")
        logging.info(f'HOST : {self.host}')
        try:
            credentials = service_account.Credentials.from_service_account_file("credentials.json")
            client = bigquery.Client(credentials=credentials, project=credentials.project_id)
        except Exception as e:
            logging.error(f"Error loading credentials: {e}")
            return

        dataset_id = "loadTesting"
        experiments_table_id = f"{dataset_id}.experiments"
        metrics_table_id = f"{dataset_id}.metrics"

        overall_total_requests = sum(len(metrics) + len(self.failures[user_id]) for user_id, metrics in self.metrics.items())
        overall_failures = sum(len(failures) for failures in self.failures.values())
        overall_total_response_time = sum(metric['response_time'] for metrics in self.metrics.values() for metric in metrics)
        overall_avg_response_time = overall_total_response_time / overall_total_requests if overall_total_requests > 0 else 0
        overall_total_tokens = sum(metric['total_token_count'] for metrics in self.metrics.values() for metric in metrics)
        overall_prompt_tokens = sum(metric['prompt_token_count'] for metrics in self.metrics.values() for metric in metrics)
        overall_response_tokens = sum(metric['candidates_token_count'] for metrics in self.metrics.values() for metric in metrics)
        overall_rps = overall_total_requests / overall_total_response_time if overall_total_response_time > 0 else 0

        # Prepare experiment data
        experiment_data = {
            "experiment_id": self.experiment_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_requests": overall_total_requests,
            "success_requests": overall_total_requests - overall_failures,
            "failure_requests": overall_failures,
            "average_rps": overall_rps,
            "average_response_time": overall_avg_response_time,
            "average_prompt_tokens": round(overall_prompt_tokens / overall_total_requests) if overall_total_requests > 0 else 0,
            "average_response_tokens": round(overall_response_tokens / overall_total_requests) if overall_total_requests > 0 else 0,
            "total_token_count": overall_total_tokens,
            "users": self.users,
            "spawn_rate": self.spawn_rate,
            "host": self.host,
            "endpoint": self.endpoint,
            "run_time": self.run_time
        }

        try:
            # Insert experiment data
            errors = client.insert_rows_json(experiments_table_id, [experiment_data])
            if errors:
                logging.error(f"Error inserting experiment data: {errors}")
            else:
                logging.info("Experiment data inserted successfully.")
        except Exception as e:
            logging.error(f"Exception occurred while inserting experiment data: {e}")

        # Prepare metrics data
        metrics_data = []
        for user_id, user_metrics in self.metrics.items():
            for metric in user_metrics:
                metrics_data.append({
                    "experiment_id": self.experiment_id,
                    "user_id": user_id,
                    "prompt": metric["prompt"],
                    "status_code": metric["status_code"],
                    "response_time": metric["response_time"],
                    "prompt_token_count": metric["prompt_token_count"],
                    "candidates_token_count": metric["candidates_token_count"],
                    "total_token_count": metric["total_token_count"],
                    "concurrent_requests": self.user_concurrent_requests[user_id]
                })

        # Insert metrics data in batches
        batch_size = 10000  # You can adjust this size as needed
        for i in range(0, len(metrics_data), batch_size):
            batch = metrics_data[i:i + batch_size]
            try:
                errors = client.insert_rows_json(metrics_table_id, batch)
                if errors:
                    logging.error(f"Error inserting metrics data in batch {i // batch_size + 1}: {errors}")
                else:
                    logging.info(f"Metrics data batch {i // batch_size + 1} inserted successfully.")
            except Exception as e:
                logging.error(f"Exception occurred while inserting metrics data in batch {i // batch_size + 1}: {e}")

from tabulate import tabulate
from collections import defaultdict
import threading

class MetricCollector:
    def __init__(self):
        self.metrics = defaultdict(list)  # Metrics per user
        self.failures = defaultdict(list)  # Failure metrics per user
        self.concurrent_requests = 0
        self.peak_concurrent_requests = 0
        self.user_concurrent_requests = defaultdict(int)
        self.lock = threading.Lock()

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

    def display_metrics(self):
        overall_table = []
        overall_total_requests = 0
        overall_total_response_time = 0
        overall_total_tokens = 0
        overall_failures = 0

        print("\nUser-wise Metrics:\n")
        for user_id, user_metrics in self.metrics.items():
            user_table = []
            user_total_requests = len(user_metrics) + len(self.failures[user_id])
            user_total_response_time = sum(metric['response_time'] for metric in user_metrics + self.failures[user_id])
            user_total_tokens = sum(metric['total_token_count'] for metric in user_metrics)
            user_failures = len(self.failures[user_id])
            user_concurrent_requests = self.user_concurrent_requests[user_id]

            for metric in user_metrics + self.failures[user_id]:
                user_table.append([
                    metric['prompt'],
                    metric['status_code'],
                    f"{metric['response_time']:.4f}",
                    metric['prompt_token_count'],
                    metric['candidates_token_count'],
                    metric['total_token_count']
                ])

            headers = ["Prompt", "Status Code", "Response Time (s)", "Prompt Tokens", "Response Tokens", "Total Tokens"]
            print(f"User ID: {user_id}")
            print(tabulate(user_table, headers=headers, tablefmt="pretty"))

            avg_response_time = user_total_response_time / user_total_requests if user_total_requests > 0 else 0
            rps = user_total_requests / user_total_response_time if user_total_response_time > 0 else 0

            print(f"\nUser {user_id} Analysis:")
            print(f"  Total Requests: {user_total_requests}")
            print(f"  Total Response Time: {user_total_response_time:.4f} seconds")
            print(f"  Average Response Time: {avg_response_time:.4f} seconds")
            print(f"  Requests Per Second (RPS): {rps:.4f}")
            print(f"  Total Tokens Processed: {user_total_tokens}")
            print(f"  Average Tokens Per Request: {user_total_tokens / user_total_requests if user_total_requests > 0 else 0:.4f}")
            print(f"  Total Failures: {user_failures}")
            print(f"  Concurrent Requests: {user_concurrent_requests}")
            print("\n" + "-"*60 + "\n")

            overall_table.extend(user_table)
            overall_total_requests += user_total_requests
            overall_total_response_time += user_total_response_time
            overall_total_tokens += user_total_tokens
            overall_failures += user_failures

        overall_avg_response_time = overall_total_response_time / overall_total_requests if overall_total_requests > 0 else 0
        overall_rps = overall_total_requests / overall_total_response_time if overall_total_response_time > 0 else 0

        print("\nOverall Analysis:")
        print(f"  Total Requests: {overall_total_requests}")
        print(f"  Total Response Time: {overall_total_response_time:.4f} seconds")
        print(f"  Average Response Time: {overall_avg_response_time:.4f} seconds")
        print(f"  Requests Per Second (RPS): {overall_rps:.4f}")
        print(f"  Total Tokens Processed: {overall_total_tokens}")
        print(f"  Average Tokens Per Request: {overall_total_tokens / overall_total_requests if overall_total_requests > 0 else 0:.4f}")
        print(f"  Total Failures: {overall_failures}")
        print(f"  Peak Concurrent Requests: {self.peak_concurrent_requests}")

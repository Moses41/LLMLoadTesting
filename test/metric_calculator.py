import time
import requests
import pandas as pd
from prettytable import PrettyTable

# List of users and prompts
users = [135339859030416, 135339860401776, 135339859601648, 135339841005520, 135339859346576, 135339859346288]
prompts = [
    "Hello, how are you?",
    "What is the capital of France?",
    "Tell me a joke."
]

# URL of the API endpoint
url = "https://gemini-flash-qj4brxgvmq-uc.a.run.app/generate-response"

# Dictionary to store user-wise metrics
user_metrics = {}

# Iterate over each user
for user_id in users:
    user_data = []
    
    # Iterate over each prompt
    for prompt in prompts:
        start_time = time.time()
        
        # Simulate an API request
        response = requests.post(url, json={"user_id": user_id, "prompt": prompt})
        end_time = time.time()
        
        response_time = end_time - start_time
        status_code = response.status_code
        response_text = response.json()

        # Handle response text being a dictionary
        if isinstance(response_text, dict):
            response_text = response_text.get("response", "")

        prompt_tokens = len(prompt.split())
        response_tokens = len(response_text.split())
        total_tokens = prompt_tokens + response_tokens
        
        # Store data for this prompt
        user_data.append({
            "Prompt": prompt,
            "Status Code": status_code,
            "Response Time (s)": response_time,
            "Prompt Tokens": prompt_tokens,
            "Response Tokens": response_tokens,
            "Total Tokens": total_tokens
        })
    
    # Store data for this user
    user_metrics[user_id] = user_data

# Function to calculate metrics for each user
def calculate_user_metrics(user_id, user_data):
    total_requests = len(user_data)
    total_response_time = sum(item["Response Time (s)"] for item in user_data)
    average_response_time = total_response_time / total_requests
    requests_per_second = total_requests / total_response_time
    total_tokens = sum(item["Total Tokens"] for item in user_data)
    average_tokens_per_request = total_tokens / total_requests
    total_failures = sum(1 for item in user_data if item["Status Code"] != 200)
    concurrent_requests = len(set(item["Prompt"] for item in user_data))  # Unique prompts as a proxy for concurrent requests
    
    return {
        "Total Requests": total_requests,
        "Total Response Time": total_response_time,
        "Average Response Time": average_response_time,
        "Requests Per Second (RPS)": requests_per_second,
        "Total Tokens": total_tokens,
        "Average Tokens Per Request": average_tokens_per_request,
        "Total Failures": total_failures,
        "Concurrent Requests": concurrent_requests
    }

# Generate and print user-wise metrics
for user_id, user_data in user_metrics.items():
    table = PrettyTable()
    table.field_names = ["Prompt", "Status Code", "Response Time (s)", "Prompt Tokens", "Response Tokens", "Total Tokens"]
    
    for item in user_data:
        table.add_row([item["Prompt"], item["Status Code"], item["Response Time (s)"], item["Prompt Tokens"], item["Response Tokens"], item["Total Tokens"]])
    
    print(f"User ID: {user_id}")
    print(table)
    
    user_analysis = calculate_user_metrics(user_id, user_data)
    print(f"User {user_id} Analysis:")
    for key, value in user_analysis.items():
        print(f"{key}: {value}")
    print("\n" + "-"*60 + "\n")

# Summary across all users
summary_table = PrettyTable()
summary_table.field_names = ["User ID", "Total Requests", "Total Response Time", "Average Response Time", "Requests Per Second (RPS)", "Total Tokens", "Average Tokens Per Request", "Total Failures", "Concurrent Requests"]

for user_id, user_data in user_metrics.items():
    user_analysis = calculate_user_metrics(user_id, user_data)
    summary_table.add_row([user_id, user_analysis["Total Requests"], user_analysis["Total Response Time"], user_analysis["Average Response Time"], user_analysis["Requests Per Second (RPS)"], user_analysis["Total Tokens"], user_analysis["Average Tokens Per Request"], user_analysis["Total Failures"], user_analysis["Concurrent Requests"]])

print("Summary Across All Users:")
print(summary_table)

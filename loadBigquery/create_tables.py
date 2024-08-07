from google.cloud import bigquery
from google.api_core.exceptions import NotFound

# Define schema fields
experiments_schema = [
    bigquery.SchemaField("experiment_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("start_time", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("end_time", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("total_requests", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("success_requests", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("failure_requests", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("average_rps", "FLOAT", mode="REQUIRED"),
    bigquery.SchemaField("average_response_time", "FLOAT", mode="REQUIRED"),
    bigquery.SchemaField("users", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("spawn_rate", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("run_time", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("host", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("endpoint", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("average_prompt_tokens", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("average_response_tokens", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("total_token_count", "INTEGER", mode="REQUIRED"),
]

metrics_schema = [
    bigquery.SchemaField("experiment_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("prompt", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("status_code", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("response_time", "FLOAT", mode="REQUIRED"),
    bigquery.SchemaField("prompt_token_count", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("candidates_token_count", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("total_token_count", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("concurrent_requests", "INTEGER", mode="REQUIRED")
]

def get_bigquery_client():
    """Initializes a BigQuery client."""
    return bigquery.Client.from_service_account_json('../credentials.json')

def create_dataset(client):
    """Creates a dataset if it does not exist."""
    dataset_id = 'loadTesting'
    dataset_ref = client.dataset(dataset_id)

    try:
        client.get_dataset(dataset_ref)# Make an API request.
        print(f"Dataset {dataset_id} already exists.")
    except NotFound:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"
        client.create_dataset(dataset)# Make an API request.
        print(f"Created dataset {dataset_id}.")

def create_or_update_table(client, table_id, schema):
    """Creates a table if it does not exist or updates the schema if it does."""
    dataset_id = 'loadTesting'
    table_ref = client.dataset(dataset_id).table(table_id)

    try:
        table = client.get_table(table_ref) # Make an API request.
        print(f"Table {table_id} already exists. Updating schema.")
        table.schema = schema
        client.update_table(table, ["schema"]) # Make an API request.
    except NotFound:
        print(f"Creating table {table_id}.")
        table = bigquery.Table(table_ref, schema=schema)
        client.create_table(table) # Make an API request.

def create_tables(client):
    """Creates or updates tables in the dataset."""
    create_or_update_table(client, 'experiments', experiments_schema)
    create_or_update_table(client, 'metrics', metrics_schema)

if __name__ == "__main__":
    client = get_bigquery_client()
    create_dataset(client)
    create_tables(client)
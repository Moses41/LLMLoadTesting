import redis
import sys

# Replace these with your Redis server details
REDIS_HOST = '34.162.116.47'  # Use external IP or hostname if not local
REDIS_PORT = 6379          # Default Redis port

# Connect to the Redis server
try:
    client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    # Test connection
    if client.ping():
        print("Successfully connected to Redis!")
except redis.ConnectionError as e:
    print(f"Failed to connect to Redis: {e}")
    sys.exit(1)

# Test setting and getting a value
try:
    test_key = 'test_key'
    test_value = 'test_value'
    
    # Set a key-value pair
    client.set(test_key, test_value)
    
    # Retrieve the value
    value = client.get(test_key)
    
    if value == test_value:
        print("Redis is working correctly!")
    else:
        print(f"Unexpected value retrieved: {value}")
except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)

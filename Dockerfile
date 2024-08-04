# Use a base image with Python installed
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire content of the current directory to the container
COPY . .

ENV CONFIG_PATH="/app/traffic_generator/config.yaml"
# Expose the port on which the application will run
EXPOSE 8000

# Specify the entry point for the container
CMD ["python", "api/main.py"]

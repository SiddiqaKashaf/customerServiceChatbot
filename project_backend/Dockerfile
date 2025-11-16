# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Copy all backend code into container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that Fly.io uses
EXPOSE 8080

# Run the Flask app from inside the src folder
CMD ["python", "src/main.py"]

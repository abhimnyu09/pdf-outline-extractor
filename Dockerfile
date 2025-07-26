# Use official Python runtime as base image
FROM --platform=linux/amd64 python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY extract_outline.py .

# Create input and output directories
RUN mkdir -p /app/input /app/output

# Make script executable
RUN chmod +x extract_outline.py

# Run the application
CMD ["python", "extract_outline.py"]
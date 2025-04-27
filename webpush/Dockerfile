FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=server.py

# Command to run the application with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "server:app"]

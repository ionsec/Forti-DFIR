FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies directly
RUN pip install --no-cache-dir \
    Flask==3.0.0 \
    Flask-CORS==4.0.0 \
    pandas==2.1.4 \
    Werkzeug==3.0.1

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p uploads results

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "simple_app.py"]
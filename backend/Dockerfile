FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY backend/requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application code
COPY backend/app /app

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["python", "main.py"]
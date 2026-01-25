# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Upgrade pip and install uv
RUN pip install --upgrade pip && pip install uv==0.9.26

# Install any needed packages specified in requirements.txt using uv
RUN uv pip install --system --no-cache-dir -r requirements.txt

# Copy the source code into the container
COPY src/ ./src/
COPY static/ ./static/

# Expose port 8000 for the FastAPI app
EXPOSE 8000

# Run the application using uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

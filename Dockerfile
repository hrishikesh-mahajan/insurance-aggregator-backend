# Use a smaller official Python runtime as a parent image
FROM python:3.9-alpine

# Set the working directory in the container
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Define environment variables with default values
ENV PORT=5000
ENV THREADS=4
ENV SERVER_IP=0.0.0.0

# Make port available to the world outside this container
EXPOSE ${PORT}

# Run app.py when the container launches
CMD ["gunicorn", "-w", "${THREADS}", "-b", "${SERVER_IP}:${PORT}", "api:app"]

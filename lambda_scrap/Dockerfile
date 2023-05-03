
#FROM python:3.8-slim

#RUN pip install --upgrade pip

#WORKDIR /code

#COPY . .

#RUN pip install -r requirements.txt

#EXPOSE 8080

#ENV PORT=8080

#CMD ["python", "app.py"]

# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variable
ENV FLASK_APP app.py

# Run app.py when the container launches
CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]

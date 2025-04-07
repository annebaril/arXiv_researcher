FROM python:3.10-slim

# Disable interactive mode to avoid prompts
ARG DEBIAN_FRONTEND=noninteractive

# Setting PYTHONUNBUFFERED to a non-empty value different from 0 ensures that the python output 
# i.e. the stdout and stderr streams are sent straight to terminal 
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR  /code

# Install curl to perform health checks
RUN apt-get update && apt-get install -y curl

# Install the dependencies
COPY pyproject.toml pyproject.toml
COPY src/ src/
RUN pip install . 

# If you need to understand between EXPOSE and docker run --port , please read this 
# Stack Overflow answer: https://stackoverflow.com/questions/22111060/what-is-the-difference-between-expose-and-publish-in-docker
EXPOSE $PORT

# Copy the source code to the container
# Copying after the dependencies are installed ensures that the dependencies are cached 🔥
COPY streamlit_app.py streamlit_app.py

# Run the application
CMD ["streamlit", "run", "streamlit_app.py"]
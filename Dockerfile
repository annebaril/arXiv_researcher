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

COPY pyproject.toml ./

# Copy the source code to the container
COPY src ./src

COPY streamlit_app.py ./streamlit_app.py
COPY README.md ./

# ENV variables
ENV CHROMADB_HOST=34.163.106.5 
ENV AGENT_PROMPT=hwchase17/structured-chat-agent
ENV EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
ENV LLM_MODEL=gemini-2.0-flash-lite
ENV MODEL_PROVIDER=google_vertexai
ENV VERBOSE=True

# Install the dependencies
RUN pip install .

# If you need to understand between EXPOSE and docker run --port , please read this 
# Stack Overflow answer: https://stackoverflow.com/questions/22111060/what-is-the-difference-between-expose-and-publish-in-docker
EXPOSE $PORT

# Run the application
CMD ["streamlit", "run", "streamlit_app.py"]
FROM python:3.9

# Set the working directory
WORKDIR /cloudrun

# Copy the requirements file
COPY requirements.txt requirements.txt

# Install dependencies
RUN pip install -r requirements.txt

# Copy the rest of the app code
COPY . .

# Run the Flask app
CMD ["python3", "-m" , "flask", "run", "--host=0.0.0.0"]
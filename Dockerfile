FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

# Install app dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy app source code
COPY app /app

# Set the working directory
WORKDIR /app

# Start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8086", "--reload"]

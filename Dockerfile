FROM node:18-bullseye-slim

WORKDIR /app

# Install Python and pip
RUN apt-get update && \
    apt-get install -y python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

# Symlink python to python3 so that 'python' command works globally
RUN ln -s /usr/bin/python3 /usr/bin/python

# Install Python requirements
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy ML model and scripts
COPY infer.py .
COPY vocabulary.json .
COPY threat_model.tflite .

# Copy backend files
COPY backend/ ./backend/
WORKDIR /app/backend

# Install Node dependencies
RUN npm install

# Expose API port
EXPOSE 5050

# Start Node server
CMD ["node", "server.js"]

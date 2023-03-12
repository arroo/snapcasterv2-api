# Build container
FROM python:3.9-slim-buster AS build

# Set working directory
WORKDIR /app

# Install playwright dependencies
RUN apt-get update && \
    apt-get install -y wget gnupg ca-certificates && \
    wget -qO- https://playwright.dev/cli/sh | bash && \
    playwright install && \
    playwright install chromium

# Copy the requirements file into the container
COPY requirements.txt .

# Install requirements
RUN pip install --no-cache-dir -r requirements.txt



# Copy the application code into the container
COPY . .

# Final container
FROM python:3.9-slim-buster

# Set working directory
WORKDIR /app

# Copy only necessary files from the build container
COPY --from=build /app .

# Set the command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", $PORT]

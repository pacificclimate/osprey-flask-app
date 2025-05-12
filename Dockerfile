FROM python:3.10-slim

LABEL Maintainer="https://github.com/pacificclimate/osprey-flask-app" \
      Description="osprey-flask-app" \
      Vendor="pacificclimate" \
      Version="0.2.0"

# Set environment variables
ENV POETRY_VIRTUALENVS_CREATE=false 

# Install Poetry
RUN apt-get update && apt-get install -y curl && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    apt-get purge -y curl && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app
WORKDIR /app

# Install dependencies
RUN poetry install --extras "dev"

EXPOSE 5000
CMD ["poetry", "run", "gunicorn", "--timeout", "0", "--bind=0.0.0.0:5000", "osprey_flask_app:create_app()"]

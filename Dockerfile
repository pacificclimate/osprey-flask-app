FROM python:3.11-slim

LABEL Maintainer="https://github.com/pacificclimate/osprey-flask-app" \
    Description="osprey-flask-app" \
    Vendor="pacificclimate" \
    Version="0.2.0"

# Set environment variables
ENV POETRY_VIRTUALENVS_CREATE=false 

# Install Poetry
RUN pip install -U pip && pip install poetry


# Copy project files
COPY . /app
WORKDIR /app

ENV POETRY_VIRTUALENVS_CREATE=false

RUN poetry config repositories.pcic https://pypi.pacificclimate.org/simple/ && \
    poetry lock && \
    poetry install
EXPOSE 5000
CMD ["poetry", "run", "gunicorn", "--timeout", "0", "--bind=0.0.0.0:5000", "osprey_flask_app:create_app()"]

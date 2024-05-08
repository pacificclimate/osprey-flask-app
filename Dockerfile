FROM python:3.10-slim

LABEL Maintainer="https://github.com/pacificclimate/osprey-flask-app" \
      Description="osprey-flask-app" \
      Vendor="pacificclimate" \
      Version="0.2.0"

COPY . /app
WORKDIR /app

RUN pip install pipenv==2022.10.25 && \
    pipenv install --dev

EXPOSE 5000
ENTRYPOINT ["pipenv", "run", "gunicorn", "--config", "gunicorn.conf", "--log-config", "logging.conf", "--bind=0.0.0.0:5000", "osprey_flask_app:create_app()"]

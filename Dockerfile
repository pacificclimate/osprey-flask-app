FROM python:3.8-slim

LABEL Maintainer="https://github.com/pacificclimate/osprey-flask-app" \
      Description="osprey-flask-app" \
      Vendor="pacificclimate" \
      Version="0.2.0"

COPY . /app
WORKDIR /app

RUN pip install -U pipenv && \
    pipenv install --dev

EXPOSE 5000
CMD ["pipenv", "run", "gunicorn", "--timeout", "0", "--bind=0.0.0.0:5000", "osprey_flask_app:create_app()"]

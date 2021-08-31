FROM python:3.8-alpine

ENV PIP_INDEX_URL="https://pypi.pacificclimate.org/simple/"

LABEL Maintainer="https://github.com/pacificclimate/osprey-flask-app" \
      Description="osprey-flask-app" \
      Vendor="pacificclimate" \
      Version="1.0.0"

COPY Pipfile ./

RUN pip install -U pipenv && \
    pipenv install

ADD . /app
WORKDIR /app

COPY ./osprey-flask-app /app/osprey-flask-app

EXPOSE 5000
CMD ["pipenv", "run", "gunicorn", "--timeout", "0", "--bind=0.0.0.0:5000", "osprey-flask-app:create_app()"]

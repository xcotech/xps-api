FROM python:3.6

ENV PYTHONUNBUFFERED 1

COPY . /code/
WORKDIR /code/

RUN pip install pipenv
RUN pipenv install --dev
RUN echo 'SHELL=/bin/bash pipenv shell' >> /root/.bashrc

EXPOSE 8000

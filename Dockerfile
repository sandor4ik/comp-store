FROM python:3

ENV PYHTONUNBUFFERED = 1

WORKDIR /code

COPY requirements.txt /code/

RUN pip install -r requirements.txt

COPY . /code/

RUN python manage.py collectstatic --noinput
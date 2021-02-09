FROM python:latest

WORKDIR /app/

# install some basics
RUN apk update \
    && apk add --no-cache vim curl

# install psycopg2
RUN apk update \
    && apk add --virtual build-deps gcc python3-dev musl-dev \
    && apk add postgresql-dev \
    && pip install psycopg2 \
    && pip install --upgrade incremental


ENV PIP_NO_CACHE_DIR 1

ADD ./requirements.txt ./
RUN pip install -r ./requirements.txt

# copy entrypoint.sh
ADD ./deploy/postgres/entrypoint.sh /app/entrypoint.sh


ADD ./ ./
RUN ./manage.py collectstatic --noinput

# run entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

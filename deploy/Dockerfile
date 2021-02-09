FROM python:latest

WORKDIR /app/

# install some basics
RUN apt update \
    && apt install -y vim curl

# install psycopg2 dependencies
RUN apt update \
    && apt install -y build-deps gcc python3-dev musl-dev \
    && apt install -y postgresql-dev

ENV PIP_NO_CACHE_DIR 1

ADD ./requirements.txt ./
RUN pip install -r ./requirements.txt

# copy entrypoint.sh
ADD ./deploy/postgres/entrypoint.sh /app/entrypoint.sh


ADD ./ ./
RUN ./manage.py collectstatic --noinput

# run entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

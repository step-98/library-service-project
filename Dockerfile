FROM python:3.12.12-slim
LABEL maintainer="vist98@gmail.com"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

RUN mkdir -p /app/media

RUN adduser \
    --disabled-password \
    --no-create-home \
    my_user

RUN chown -R my_user /app/media
RUN chmod -R 755 /app/media

USER my_user

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

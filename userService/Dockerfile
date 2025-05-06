FROM python:3.10
WORKDIR /app
COPY . .
RUN pip install django djangorestframework psycopg2-binary djangorestframework-simplejwt
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
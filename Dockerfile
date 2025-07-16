FROM node:20 AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM python:3.12-slim

WORKDIR /app
COPY --from=build /app/dist /app/static

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "-m", "gunicorn", "-c gunicorn.conf.py", "app:app"]
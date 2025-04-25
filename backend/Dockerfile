FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

RUN apt-get update && apt-get install -y default-jdk python3-pip && apt-get clean 

COPY . .

RUN pip install -r requirements.txt

# RUN pip install requirements.txt
EXPOSE 8000


CMD ["fastapi","run","app.py","--host","0.0.0.0","--port","8000"]

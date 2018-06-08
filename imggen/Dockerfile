#docker build -t imggen:latest imggen
#docker run -d -p 5000:5000 imggen
#docker run -d -p 5000:5000 -v "/c/Users/erwin/Desktop/Delete/docker/test:/tmp/" imggen
#docker run -d -p 5000:5000 -v "/c/Users/erwin/Desktop/Delete/docker/test:/tmp/" --privileged imggen

FROM ubuntu:latest
MAINTAINER Erwin

RUN apt-get update -y
RUN apt-get install -y sudo python-pip python-dev build-essential
#RUN useradd -m docker && echo "docker:docker" | chpasswd && adduser docker sudo

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["app.py"]
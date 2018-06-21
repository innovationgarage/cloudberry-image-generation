# cloudberry-image-generation

## Description

## Usage

### Build
docker build -t imggen:latest .

### Run
docker run -d -p 5000:5000 -v "/c/Users/erwin/Desktop/Delete/docker/test:/workdir/" --privileged imggen

### Input
The input folder has the following structure (per image):
* imagename.img
* imagename.offset
* imagename/

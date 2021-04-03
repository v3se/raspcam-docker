# raspcam-docker

Containerized Python application for Raspberry Pi with a camera module which enables browser based mjpeg video streaming. Based on an [example](https://github.com/waveform80/picamera/blob/release-1.13/docs/examples/web_streaming.py) from picamera Python library.

## Installation

Clone this repository to your Raspberry PI

```bash
git clone https://github.com/v3se/raspcam-docker
```

You can run this application either by manually building the docker image

```bash
docker build -t <tag> . 
```

or by using **[docker-compose](https://docs.docker.com/compose/install/) up** command

```bash
docker-compose up --detach
```

## Usage

The video stream is available in a simple website after you have started the container. If you used the docker-compose command to run the container, the website is available at **port 80** on your local host and is listening also all incoming connections.

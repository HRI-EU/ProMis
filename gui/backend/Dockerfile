FROM ubuntu:22.04

# APT installs and settings
RUN apt-get update -qq
RUN apt-get install -qy git curl xz-utils python3-pip python3-gdal libgdal-dev cython3

# Locales settings for Sphinx to work
RUN apt-get install -qy locales
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen

# Git and pip setup
ENV PIP_BREAK_SYSTEM_PACKAGES=1

# Get clone of repository
RUN git clone https://github.com/HRI-EU/ProMis.git
WORKDIR /ProMis
# Setting -e does not really work here
RUN pip install '.[doc,dev,nautical]'

WORKDIR /backend

COPY ./ /backend/

RUN pip install "fastapi[standard]"
RUN pip install geojson-pydantic 

CMD ["fastapi", "run", "main.py"]

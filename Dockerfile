FROM ubuntu:22.04

## APT installs and settings ##
# Resolve APT dependencies
RUN apt-get update -qq
RUN apt-get install git curl xz-utils python3-pip python3-gdal libgdal-dev -qqy

# Locales settings for Sphinx to work
RUN apt-get install -y locales
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
 && sed -i -e 's/# pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen \
 && locale-gen

## Git and pip setup ##
# Get clone of repository
RUN git clone https://github.com/HRI-EU/ProMis.git
WORKDIR /ProMis

# Install separate pip dependencies
RUN pip install pyro-ppl graphviz
RUN pip install --upgrade --force-reinstall --no-deps --no-binary :all: pysdd

# Clone and install Problog with distributional clauses
# This contains bugfixes that are not part of the official release yet
WORKDIR /ProMis/external
RUN git clone https://github.com/simon-kohaut/problog.git
RUN cd problog; git checkout dcproblog_develop
RUN cd problog; pip install .

# Set promis root-directory as workdir
WORKDIR /ProMis
RUN pip install .

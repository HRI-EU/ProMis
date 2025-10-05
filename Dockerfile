#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

FROM ubuntu:22.04

# APT installs and settings
RUN apt-get update -qq
RUN apt-get install -qy git curl xz-utils python3-pip python3-gdal libgdal-dev cython3

# Locales settings for Sphinx to work
RUN apt-get install -qy locales
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen

# Git and pip setup
ENV PIP_BREAK_SYSTEM_PACKAGES=1

# Install separate pip dependencies
RUN pip install pyro-ppl graphviz
RUN pip install --upgrade --force-reinstall --no-deps --no-binary :all: pysdd

# Get clone of repository and install with a reasoning backend
RUN git clone https://github.com/HRI-EU/ProMis.git
WORKDIR /ProMis
RUN pip install '.[doc,dev,nautical]'
RUN pip install git+https://github.com/simon-kohaut/problog.git@dcproblog_develop

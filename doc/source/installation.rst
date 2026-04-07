Installation
============

This guide covers the installation of ProMis and its dependencies.

Prerequisites
-------------

Before installing ProMis, you need to set up your environment.

**Python**

ProMis requires Python 3.10 or newer. You can download it from `python.org <https://www.python.org/downloads/>`_.

**Optional Dependencies**

*   **GUI:** To use the graphical user interface, you will need `Node.js <https://docs.npmjs.com/downloading-and-installing-node-js-and-npm>`_.
*   **Nautical Charts:** To work with nautical chart data (e.g., from S-57 files), `GDAL <https://gdal.org/en/stable/download.html>`_ is required. GDAL can be tricky to install, but here are some tips for common platforms:

    .. code-block:: bash

        # Ubuntu / Debian
        sudo apt-get update
        sudo apt-get install python3-gdal libgdal-dev

        # macOS (using Homebrew)
        brew install gdal

    For other systems, please refer to the `official GDAL documentation <https://gdal.org/en/stable/download.html>`_.

Standard Installation
---------------------

This is the recommended method for most users. It installs the latest stable version of ProMis from PyPI.

.. code-block:: bash

    pip install promis

If you plan to work with nautical charts, install the necessary extras.
Make sure you have installed GDAL first (see Prerequisites).

.. code-block:: bash

    pip install "promis[nautical]"

Developer Installation
----------------------

If you want to contribute to ProMis, you should clone the repository and install it in editable mode.
This allows you to modify the code and see your changes immediately.

.. code-block:: bash
    :linenos:

    # 1. Clone the repository
    git clone git@github.com:HRI-EU/ProMis.git
    cd ProMis

    # 2. Install in editable mode with development and documentation dependencies
    pip install -e ".[dev,doc]"

To also include dependencies for nautical applications, add the ``nautical`` extra:

.. code-block:: bash
    :linenos:

    pip install -e ".[dev,doc,nautical]"

Docker
------

We provide a Docker setup for a containerized development environment, which ensures all dependencies are handled correctly.

**Using VS Code Dev Containers**

The easiest way to get started is by using `VS Code's Dev Containers extension <https://code.visualstudio.com/docs/devcontainers/containers>`_.
Simply open the cloned repository in VS Code and, when prompted, click "Reopen in Container".
This will automatically build the Docker image and configure your environment.

**Manual Docker Build**

If you prefer to manage Docker manually, you can build and run the container from your terminal.

.. code-block:: bash
    :linenos:

    # Build the Docker image
    docker build . -t promis

    # Run the container with the local source code mounted.
    # This allows you to edit files on your host machine and run them inside the container.
    docker run -it --rm -v "$(pwd)":/workspaces/ProMis -w /workspaces/ProMis promis bash

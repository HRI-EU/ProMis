Installation
============

Requirements
------------

To use ProMis, the following requirements are needed depending on the features you want to use.

* `Python >= 3.10 <https://www.python.org/downloads/>`_ is required to run ProMis itself.
* `Node.js <https://docs.npmjs.com/downloading-and-installing-node-js-and-npm>`_ is needed to use ProMis' graphical user interface.
* `GDAL ,https://gdal.org/en/stable/download.html>`_ is necessary to work with nautical chart data.

From Pypi
---------

ProMis can be easily installed using the following commands.

.. code-block:: bash
    :linenos:

    # Installing ProMis and a probabilistic reasoning backend
    pip install promis
    pip install git+https://github.com/simon-kohaut/problog.git@dcproblog_develop


Local Installation
------------------

In case you would like to contribute to the project, the following sets up ProMis for development.

.. code-block:: bash
    :linenos:

    git clone git@github.com:HRI-EU/ProMis.git
    cd ProMis
    pip install -e ".[dev,doc]"
    pip install git+https://github.com/simon-kohaut/problog.git@dcproblog_develop

For nautical applications using marine chart data, you can install the additional dependencies with `pip install . "[nautical]"`.

Docker
------

If you have `Docker` installed on your system, we provide `vscode devcontainer` settings that can be used for dockerized development.
Otherwise, run the following commands to manually build and employ the ProMis Dockerfile.

.. code-block:: bash
    :linenos:

    # Enters the ProMis directiory, builds a new docker image and runs it in interactive mode
    docker build . -t promis
    docker run -it promis

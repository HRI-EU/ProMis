"""Sets up the ProMis package for installation."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard library
import re
import setuptools

# Find Promis version and author strings
with open("promis/__init__.py", "r", encoding="utf8") as fd:
    content = fd.read()
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', content, re.MULTILINE).group(1)
    author = re.search(r'^__author__\s*=\s*[\'"]([^\'"]*)[\'"]', content, re.MULTILINE).group(1)

# Import readme
with open("README.md", "r", encoding="utf8") as readme:
    long_description = readme.read()

setuptools.setup(
    name="promis",
    version=version,
    author=author,
    author_email="simon.kohaut@cs.tu-darmstadt.de",
    description="A Python package to apply probabilistic logic programming to navigation tasks.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=setuptools.find_packages(),
    package_data={
        "promis": ["py.typed"],  # https://www.python.org/dev/peps/pep-0561/
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=[
        # general tools
        "rich",
        # generic scientific
        "numpy",
        "scipy",
        "scikit-learn",
        "pandas",
        "matplotlib",
        # geospatial / GIS tools
        "pyproj",
        "geojson",
        "geopy",
        "shapely",
        "overpy",
        # probabilistic logic and modelling
        "pyro-ppl",
        "pysdd",
        # plotting and visualization
        "fastapi[standard]",
        "graphviz",
        "seaborn",
        "smopy",
        # networking
        "requests",
    ],
    extras_require={
        # Building the documentation locally with sphinx
        "doc": [
            "sphinx",
            "sphinx-markdown-builder",
            "sphinx_rtd_theme",
            "sphinxcontrib-programoutput",
        ],
        # Loading nautical chart data into ProMis
        # Requires GDAL to be installed on the system
        "nautical": [
            "gdal"
        ],
        # Development tools for quality assurance
        "dev": [
            # static code analysis
            "black",
            "ruff",
            # dynamic code analysis
            "pytest",
            "pytest-cov",
            "pytest-sugar",
        ],
    },
)
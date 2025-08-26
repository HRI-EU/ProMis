# -- Path setup --------------------------------------------------------------

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
import sys

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
from os.path import abspath
from os.path import dirname
from os.path import join

sys.path.insert(0, abspath(join(dirname(__file__), "../..")))  # for examples/

# ProMis
import promis  # noqa: E402

# -- Project information -----------------------------------------------------

project = "ProMis"
copyright = promis.get_author()
author = promis.get_author()

# The version info for the project, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = promis.get_version().split("-")[0]
# The full version, including alpha/beta/rc tags
release = promis.get_version()

# -- General configuration ---------------------------------------------------

primary_domain = "py"

# If this is True, todo and todolist produce output, else they produce nothing.
# The default is False.
todo_include_todos = True

language = "en"

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "nbsphinx",
    "sphinx_markdown_builder",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "sphinx.ext.doctest",
    "sphinx.ext.inheritance_diagram",
    "sphinx_rtd_theme",
    "sphinxcontrib.programoutput",
]

# Do not run notebooks as they include time-intensive computations
nbsphinx_execute = "never"
nbsphinx_pandoc = "python -m pandoc"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

source_suffix = [".rst"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "shapely": ("https://shapely.readthedocs.io/en/stable", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "scipy": ("https://docs.scipy.org/doc/scipy", None),
    "matplotlib": ("https://matplotlib.org/stable", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable", None),
    "h5py": ("https://docs.h5py.org/en/stable", None),
    "tables": ("https://www.pytables.org", None),
    "pyproj": ("https://pyproj4.github.io/pyproj/stable", None),
    "rasterio": ("https://rasterio.readthedocs.io/en/stable", None),
    "geopy": ("https://geopy.readthedocs.io/en/stable", None),
    "cartopy": ("https://scitools.org.uk/cartopy/docs/latest", None),
    "pytest": ("https://docs.pytest.org/en/stable", None),
    "pytest-cov": ("https://pytest-cov.readthedocs.io/en/stable", None),
    "hypothesis": ("https://hypothesis.readthedocs.io/en/latest", None),
    'requests': ('https://requests.readthedocs.io/en/latest/', None),
}

nitpicky = False

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes or:
# - https://sphinx-themes.org/
# - https://www.writethedocs.org/guide/tools/sphinx-themes/
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []  # '_static'
# html_favicon = "../../images/logo.png"  # TODO: Needs version of logo with drone only
html_logo = "../../images/logo.png"
html_sidebars = {"**": ["globaltoc.html", "relations.html", "sourcelink.html", "searchbox.html"]}

# -- Options for LaTeX output ---------------------------------------------

latex_engine = "pdflatex"

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    "papersize": "a4paper",
    # The font size ('10pt', '11pt' or '12pt').
    # 'pointsize': '10pt',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [("index", "promis.tex", f"{project} Documentation", author, "manual")]

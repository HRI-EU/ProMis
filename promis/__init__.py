"""ProMis - Probabilistic Mission Design using Logic Programming."""



# ProMis
from promis.coco import ConstitutionalController, DoubtDensity
from promis.promis import ProMis
from promis.star_map import StaRMap

__all__ = ["ProMis", "StaRMap", "ConstitutionalController", "DoubtDensity"]
__version__ = "2.0.0"
__author__ = "Simon Kohaut"


def get_author():
    return __author__


def get_version():
    return __version__

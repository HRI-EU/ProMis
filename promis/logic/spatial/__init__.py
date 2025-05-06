"""The ProMis spaital logic package provides probabilistic atoms for vectorized logic program."""



# ProMis
from promis.logic.spatial.depth import Depth
from promis.logic.spatial.distance import Distance
from promis.logic.spatial.over import Over
from promis.logic.spatial.relation import Relation

__all__ = ["Distance", "Over", "Depth", "Relation"]

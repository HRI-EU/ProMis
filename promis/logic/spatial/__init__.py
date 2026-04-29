"""The promis.logic.spatial package provides classes for representing probabilistic spatial relations."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# ProMis
from promis.logic.spatial.crosses import Crosses
from promis.logic.spatial.depth import Depth
from promis.logic.spatial.distance import Distance
from promis.logic.spatial.enters import Enters
from promis.logic.spatial.intersects import Intersects
from promis.logic.spatial.follows import Follows
from promis.logic.spatial.opposes import Opposes
from promis.logic.spatial.over import Over
from promis.logic.spatial.relation import Relation, ScalarRelation

__all__ = ["Crosses", "Depth", "Distance", "Enters", "Intersects", "Follows", "Opposes", "Over", "Relation", "ScalarRelation"]

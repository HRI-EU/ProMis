"""The ProMis engine for reactive probabilistic mission landscapes using Resin."""

#
# Copyright (c) Simon Kohaut, Honda Research Institute Europe GmbH, Felix Divo, and contributors
#
# This file is part of ProMis and licensed under the BSD 3-Clause License.
# You should have received a copy of the BSD 3-Clause License along with ProMis.
# If not, see https://opensource.org/license/bsd-3-clause/.
#

# Standard Library
import re
import time
from copy import deepcopy

# Third Party
import numpy as np
from numpy import array
from resin import Resin

# ProMis
from promis.geo import CartesianCollection
from promis.star_map import StaRMap


class ProMis:
    """The ProMis engine for reactive Probabilistic Mission Landscapes using Resin.

    Parses a Resin logic program, compiles it, and automatically wires all sources
    declared with a known relation type (``over``, ``distance``, ``depth``) to the
    corresponding data in the provided StaRMap.  Sources for dynamic data (e.g.
    moving agents) can be obtained via :meth:`get_writer` and written to
    independently.

    Args:
        star_map: The statistical relational map holding pre-computed relation parameters.
        logic: A Resin program string.  Every ``atom <- source(path, Type).`` declaration
            whose atom matches a relation in the StaRMap is wired up automatically.
        dimension: The number of spatial evaluation points (pixels / locations).
        max_models: The maximum number of models to enumerate when solving the Resin program.
            If exceeded, this initializer raises ``RuntimeError("Stable model limit exceeded: ...")``.
        verbose: Whether to enable verbose output from Resin.
    """

    def __init__(
        self,
        star_map: StaRMap,
        logic: str,
        dimension: int,
        max_models: int | None = None,
        verbose: bool = False,
    ) -> None:
        self.star_map = star_map
        self.logic = logic
        self.dimension = dimension

        # Parse and validate the target declaration
        target_match = re.search(r'landscape\s*->\s*target\(\"/landscape\"\)\.', logic)
        if target_match is None:
            raise ValueError(
                "No target declaration found in Resin program. "
                "Define the landscape clause and declar: landscape -> target(\"/landscape\")."
            )
        self._target_name = "/landscape"

        # Parse source declarations from paths: atom -> (relation_type, location_type, source_type)
        self._sources = {
            f"{rel}({loc})": (rel, loc, src)
            for rel, loc, src in StaRMap._parse_sources(logic)
        }

        # Compile Resin and obtain the reactive circuit
        self._resin = Resin.compile(self.logic, self.dimension, max_models=max_models, verbose=verbose)
        self._rc = self._resin.get_reactive_circuit()

        # Pre-create writers for every declared source
        self._writers = {atom: self._resin.make_writer_for(atom) for atom in self._sources}

        # Store evaluation points once initialize() is called
        self._evaluation_points = None

        # Auto-link so the star_map can write back to Resin via update()
        self.star_map._promis = self

    def set_evaluation_points(self, evaluation_points: CartesianCollection):
        """Sets a new target set of points to run inference for. 
        
        All directly written data will be associated with these points.
        The StaR Map relations are interpolated onto this collection.
        """
        
        assert len(self._evaluation_points) == self.dimension, "The number of evaluation points must match the ProMis inference dimension!"
        self._evaluation_points = evaluation_points

    def initialize(
        self,
        evaluation_points: CartesianCollection,
        interpolation_method: str = "hybrid",
    ) -> None:
        """Write StaRMap data to all auto-linked sources.

        Call this once (or whenever the set of evaluation points changes) to push
        the static, map-derived distributions into the reactive circuit before
        starting the update loop.

        Args:
            evaluation_points: The spatial locations for which to evaluate and
                write relation parameters.
            interpolation_method: Interpolation method forwarded to the StaRMap
                interpolators (e.g. ``"hybrid"``, ``"linear"``).
        """

        self._evaluation_points = evaluation_points
        coords = evaluation_points.coordinates()

        for atom, (relation_type, location_type, source_type) in self._sources.items():
            # Only write sources that are present in the StaRMap
            if (
                relation_type not in self.star_map.relations
                or location_type not in self.star_map.relations[relation_type]
            ):
                continue

            relation = self.star_map.get(relation_type, location_type)
            interp = relation.parameters.get_interpolator(interpolation_method)
            params = interp(coords)

            if source_type == "Probability":
                probs = params[:, 0].ravel().tolist()
                self._writers[atom].write(probs, time.monotonic())
            elif source_type == "Density":
                means = params[:, 0].ravel().tolist()
                stds = np.sqrt(np.maximum(params[:, 1], 1e-6)).ravel().tolist()
                self._writers[atom].write("normal", [means, stds], time.monotonic())

    def update(self) -> CartesianCollection | None:
        """Trigger a reactive circuit update and return the landscape as a collection.

        Returns:
            A :class:`~promis.geo.CartesianCollection` with the same coordinates
            as the evaluation points passed to :meth:`initialize`, where
            ``data["v0"]`` holds the per-point landscape probabilities.
            Returns ``None`` when the reactive circuit has no new output yet.
        """

        raw = self._rc.update()
        if self._target_name not in raw:
            return None

        result = deepcopy(self._evaluation_points)
        result.data["v0"] = array(raw[self._target_name])
        return result

    def adapt(self, bin_size: float, number_bins: int) -> None:
        """Adapt the reactive circuit by automatically lifting and dropping leaves.

        Delegates to the underlying reactive circuit's ``adapt`` method, which
        decides internally which leaves to lift or drop based on the provided
        frequency-binning parameters.

        Args:
            bin_size: Width of each frequency bin used for the adaptation heuristic.
            number_bins: Number of frequency bins to consider.
        """

        self._rc.adapt(bin_size, number_bins)

    def get_star_map_writer(self, relation_type: str, location_type: str):
        """Return the Resin writer for the given StaR Map relation and location type.

        Use this to push dynamic (runtime-varying) data into a source that is
        not automatically wired from the StaRMap, e.g. moving vessels or UAS.

        Args:
            relation_type: The relation name, e.g. ``"distance"``.
            location_type: The location type, e.g. ``"vessel"``.

        Returns:
            A Resin writer object with a ``write(...)`` method.

        Raises:
            KeyError: If no source for the given relation and location type was
                declared in the Resin program.
        """

        atom = f"{relation_type}({location_type})"
        return self._writers[atom]

    def make_writer(self, channel: str):
        """This is used to create a writer for non-StaR Map topics.

        When declaring a channel in a resin program, i.e.,
        `atom <- source("/channel/name", DataType).`,
        this method can be used to obtain a writer for channel = "/channel/name".
        
        Args:
            channel: The channel of the ground atom to write to.
        """
        
        return self._resin.make_writer(channel)

    def make_writer_for(self, atom: str):
        """This is used to create a writer for non-StaR Map topics.

        When declaring a channel in a resin program, i.e.,
        `atom <- source("/channel/name", DataType).`,
        this method can be used to obtain a writer for atom = "atom".

        Args:
            atom: The name of the ground atom to write to.
        """

        return self._resin.make_writer_for(atom)

    def get_reactive_circuit(self):
        """Return the underlying Resin reactive circuit."""

        return self._rc

    def get_names(self) -> list[str]:
        """Return the canonical leaf names used by the reactive circuit."""

        return self._resin.get_names()

    def get_frequencies(self) -> list[float]:
        """Return the current update frequencies of the reactive circuit leaves."""

        return self._resin.get_frequencies()

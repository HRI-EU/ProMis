# Changelog

## 4.0.0

Changes since 3.0.0.

### Breaking changes

- **Inference with Resin.** Mission rules are now written in [Resin](https://github.com/simon-kohaut/resin) and evaluated by its reactive circuits, replacing ProbLog-based inference.
  A program sends its result to the landscape channel, e.g., `landscape -> target("/landscape").`, where the atom can have any name.
- **CoCo and CoFi are separate projects.** Their modules and examples moved to their own repositories.
- **Directed planning graphs.** `RasterBand.to_graph` and `RasterBand.stack_graphs` return a `networkx.DiGraph` with one edge per direction, so moves can cost differently depending on their direction, and cells excluded by `value_filter` cannot be entered.
  The default cost model charges for entering a cell, and `cost_model` and `value_filter` receive plain floats.

### New features

- **Overture Maps.** `OvertureLoader` downloads the features within the mission area from [Overture Maps](https://overturemaps.org), and `LocalOvertureLoader` reads local GeoParquet files.
  Filters name an Overture type followed by conditions on its properties, e.g., `segment[subtype=road][class=primary]` or `place[taxonomy.primary=restaurant]` for nested properties.
  Overture Maps is now the default map source of the examples and the GUI.
- **AIS data.** `AisLoader` loads vessel positions from NOAA's Automatic Identification System data.
- **Transitional spatial relations:** `crosses`, `follows`, `opposes`, `enters`, `exits`, `intersects` and `approaches`, and a relation for features in the positive half-plane of a transition.
- **Streaming updates.** `StaRMap.update` recomputes relations, also several at once, and streams them into a linked ProMis instance, e.g., for moving agents.
  Creating and accessing Resin writers through ProMis was simplified.
- `max_models` parameter for the Resin compilation.
- `value_index` parameter for `RasterBand.to_graph` and `RasterBand.search_path`, selecting which value of the band to plan on.
- `CartesianPolygon.from_geometry` and `CartesianPolyLine.from_geometry` create shapes from shapely geometries.

### Performance

- StaR Map sampling is up to 11.7 times faster and deterministic across processes, using vectorized Shapely 2 queries and fewer R-tree constructions.
- Sampling polygons and polylines translates their whole geometry at once, which halves the time of StaR Maps over large maps.
- `import promis` takes about a second instead of about three, since PyTorch, matplotlib, scikit-learn and NetworkX are only loaded when used.
- Building planning graphs with `RasterBand.to_graph` is about 2.5 times faster.

### Bug fixes

- Path planning on rasters with fewer than 11 pixels per side produced graphs without edges.
- The A* heuristic of `RasterBand.search_path` overestimated distances, which could return suboptimal paths.
- `RasterBand.search_path` failed without an explicit `cost_model` and `value_filter`.
- `Depth.plot` failed for raster bands whose size in meters differs from their resolution.
- Loading data from OpenStreetMap failed with HTTP 406, since the Overpass API rejects generic user agents.
- A warning of the Gaussian process on Python 3.14 is suppressed.

### GUI

- Clearer layout: labelled tabs for **Rules**, **Mission area** and **Map features**, grouped settings, hints on hover, and the rules editor expanded by default.
- Map filters come with examples, syntax help and live validation, and show whether their features are loaded from Overture Maps or OpenStreetMap.
- Clicking **Run** outlines empty or invalid fields in red and marks their tabs.
- Map data and StaR Maps are cached per filter and setting, so changing only the display or a rule threshold reuses earlier results.
- The origin is chosen automatically if there is only one origin marker, and new projects start without a sample layer.
- The value filter of layers validates its input again.
- The package is about 2 MB smaller.

### Documentation and examples

- The GUI documentation was rewritten, with an overview, a guide to each part of the GUI and new screenshots.
- The usage example loads its map data from Overture Maps, and shows streaming updates with simulated drones whose safety zones move through the mission landscape.
- The bundled OpenStreetMap extracts, the New York streaming script and the GUI's Docker setup were removed.

### Packaging

- New dependencies `overturemaps` and `pyarrow`, and minimum versions `pyresin>=0.2.0` and `overturemaps>=1.0.2`.
- Project, documentation and issue links, and an SPDX license expression (`BSD-3-Clause`) in the package metadata.
- The tests are no longer installed with the package.
- The README's images are shown on PyPI.

## 3.0.0 (2026-03-30)

### New features

- The OpenStreetMap loaders load multipolygons, and a location type can be given several filters.
- `promis_gui` accepts `--host` and `--port` to choose where the GUI is served.
- The usage example runs in Google Colab.

### GUI

- A default origin marker and a default table of location types for new projects.
- SVG and PNG images as render modes for layers.
- Identifiers of map objects are stored as strings, avoiding rounding errors of large numbers in the browser.
- The value filter of layers covers small probabilities, and the map starts at a better center and zoom level.
- Fixes for marker types and empty location types.

## 2.0.0 (2025-10-10)

### Breaking changes

- `Route` was renamed to `PolyLine`.
- The core of ProMis was overhauled, with collections of spatially referenced values as the basis of StaR Maps and mission landscapes.

### New features

- **Constitutional Controller (CoCo):** doubt densities that calibrate mission landscapes to an agent's own uncertainty, path compliance, and path planning on raster bands, including graphs stacked over several settings such as speeds.
- **Adaptive sampling:** collections can be improved by adding the most informative points, e.g., by local entropy or the uncertainty of a Gaussian process.
- **Gaussian process interpolation** of collections.
- **The GUI is part of the package** and is started with `promis_gui`.

### Documentation

- Documentation on [GitHub Pages](https://hri-eu.github.io/ProMis), built with Sphinx, with an expanded API reference and installation guide.
- Reorganized examples.

## 1.0.2 (2025-05-12)

- Installation instructions for installing from PyPI and from GitHub.

## 1.0.1 (2025-05-12)

- GUI updates.

## 1.0.0 (2025-05-12)

The first release of ProMis.

- **Probabilistic Mission Design:** mission landscapes that express how likely it is that an agent satisfies its mission rules, written as probabilistic logic programs.
- **Statistical Relational Maps (StaR Maps):** spatial relations such as `distance` and `over`, estimated from Uncertainty Annotated Maps of OpenStreetMap data.
- **Constitutional Filter** for the maritime domain.
- **GUI** for designing missions on a map.

// Helpers for the map filters of location types, which select the features loaded by the backend.
// Filters starting with an Overture type are loaded from Overture Maps,
// and filters starting with a bracket from OpenStreetMap (see promis/gui/main.py).

// Overture types that can be loaded, see https://docs.overturemaps.org/schema/
export const OVERTURE_TYPES = [
  "address",
  "bathymetry",
  "building",
  "building_part",
  "connector",
  "division",
  "division_area",
  "division_boundary",
  "infrastructure",
  "land",
  "land_cover",
  "land_use",
  "place",
  "segment",
  "water",
];

// Example filters offered while editing a location type
export const FILTER_EXAMPLES = [
  { label: "Buildings", filter: "building" },
  { label: "Primary roads", filter: "segment[subtype=road][class=primary]" },
  {
    label: "Secondary roads",
    filter: "segment[subtype=road][class=secondary]",
  },
  { label: "Footways", filter: "segment[subtype=road][class=footway]" },
  {
    label: "Railways",
    filter: "segment[subtype=rail][class=standard_gauge]",
  },
  { label: "Parks", filter: "land_use[subtype=park]" },
  { label: "Water", filter: "water" },
  { label: "Restaurants", filter: "place[basic_category=restaurant]" },
  { label: "Hospitals", filter: "place[basic_category=hospital]" },
  { label: "Primary roads (OpenStreetMap)", filter: "[highway=primary]" },
];

// One bracketed condition, e.g. [key], [!key], [key=value], [key!=value], [key~regex]
const CONDITION = String.raw`\[!?"?[^"=!~\]\s]+?"?(?:(?:[!~]?=|!?~)"?[^"\]]*?"?)?\]`;
const OVERTURE_FILTER = new RegExp(`^([a-z_]+)((?:\\s*${CONDITION})*)\\s*$`);
// OpenStreetMap filters are passed on to Overpass, which also accepts quotes and spaces,
// e.g. ['highway' = 'primary'], so only the brackets are checked
const OSM_FILTER = /^(?:\s*\[[^[\]]+\])+\s*$/;

/**
 * Describes where a filter loads its features from and whether it is valid.
 * @param {string} filter - The filter of a location type.
 * @returns {{source: "none" | "overture" | "osm", error: string | null}}
 */
export function describeFilter(filter) {
  const trimmed = (filter || "").trim();
  if (trimmed === "") {
    return { source: "none", error: null };
  }
  if (trimmed.startsWith("[")) {
    return OSM_FILTER.test(trimmed)
      ? { source: "osm", error: null }
      : {
          source: "osm",
          error:
            "OpenStreetMap filters are tag conditions like [highway=primary]",
        };
  }
  const match = OVERTURE_FILTER.exec(trimmed);
  if (match === null) {
    return {
      source: "overture",
      error: /^[a-z_]+\s*\[/.test(trimmed)
        ? "Write each condition in brackets, like [class=primary]"
        : "Start with a lowercase Overture type such as building or segment",
    };
  }
  if (!OVERTURE_TYPES.includes(match[1])) {
    return {
      source: "overture",
      error: `Unknown Overture type "${match[1]}"`,
    };
  }
  return { source: "overture", error: null };
}

// Human readable name of a filter's source
export const SOURCE_NAMES = {
  none: "Picked on map",
  overture: "Overture Maps",
  osm: "OpenStreetMap",
};

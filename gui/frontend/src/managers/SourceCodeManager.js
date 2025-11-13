import { C } from "./Core.js";
import {
  updateConfigLocationTypes,
  randomId,
  updateConfigLocationTypeEntry,
  deleteConfigLocationTypeEntry,
} from "../utils/Utility.js";
import Color from "../models/Color.js";

const defaultLocationTypes = [
  {
    id: 2075396262,
    locationType: "UNKNOWN",
    filter: "",
    color: "#0000FF",
    uncertainty: 10,
  },
  {
    id: 1328715238,
    locationType: "ORIGIN",
    filter: "",
    color: "#0000FF",
    uncertainty: 10,
  },
  {
    id: 3525042322,
    locationType: "VERTIPORT",
    filter: "",
    color: "#0000FF",
    uncertainty: 10,
  },
];

const defaultSourceCode = `% UAV properties
initial_charge ~ normal(90, 5).
charge_cost ~ normal(-0.1, 0.2).
weight ~ normal(0.2, 0.1).

% Weather conditions
1/10::fog; 9/10::clear.

% Visual line of sight
0.8::vlos(X) :- 
    fog, distance(X, operator) < 50;
    clear, distance(X, operator) < 100;
    clear, over(X, bay), distance(X, operator) < 400.

% Sufficient charge to return to operator
can_return(X) :-
    B is initial_charge, O is charge_cost,
    D is distance(X, operator), 0 < B + (2 * O * D).

% Permits related to local features
permits(X) :- 
    distance(X, service) < 15; 
    distance(X, primary) < 15;
    distance(X, secondary) < 10; 
    distance(X, tertiary) < 5;
    distance(X, rail) < 5; 
    distance(X, crossing) < 5; 
    over(X, park).

% Definition of a valid mission
landscape(X) :- 
    vlos(X), weight < 25, can_return(X); 
    permits(X), can_return(X).
`;

/**
 * SourceCodeManager
 * Manages the source code, location types, and related functionalities.
 * Provides methods to set/get source code, manage location types,
 * and interact with the backend for running source code.
 */
class SourceCodeManager {
  constructor() {
    this.success = true;
    this.closed = true;
    this.locationTypes = defaultLocationTypes;
    this.source = defaultSourceCode;
  }

  setSource(source) {
    this.source = source;
  }

  getSource() {
    return this.source;
  }

  // get uncertainty value from location type
  getUncertaintyFromLocationType(locationType) {
    const matchedRow = this.locationTypes.find((row) => {
      return row.locationType === locationType;
    });
    if (matchedRow !== undefined) {
      return matchedRow.uncertainty;
    } else {
      return 0;
    }
  }

  // get color value from location type
  getColorFromLocationType(locationType) {
    const matchedRow = this.locationTypes.find((row) => {
      return row.locationType === locationType;
    });
    if (matchedRow !== undefined) {
      return matchedRow.color;
    }
    return new Error("No Color found from this location type");
  }

  // get list of location type names
  getListLocationType() {
    return this.locationTypes.map((entry) => entry.locationType);
  }

  // get default location types rows
  getDefaultLocationTypesRows() {
    const defaultLocationType = defaultLocationTypes.map(
      (loc_type) => loc_type.locationType,
    );
    return this.locationTypes.filter((row) => {
      return defaultLocationType.includes(row.locationType);
    });
  }

  // construct the request body for backend running API calls
  getRequestBody({
    origin,
    sourceCode,
    dimensions,
    resolutions,
    supportResolutions,
    sampleSize,
    interpolation,
  }) {
    // sort the location types by location type
    const sortedTypes = [...this.locationTypes].sort((a, b) =>
      a.locationType > b.locationType ? 1 : -1,
    );

    // process location types to the form that the backend expects
    let locationTypes = {};
    for (const locationType of sortedTypes) {
      //check if location type exists in the locationTypes array
      if (locationTypes[locationType.locationType] !== undefined) {
        locationTypes[locationType.locationType] += locationType.filter;
        console.log(locationTypes[locationType.locationType]);
        continue;
      }
      locationTypes[locationType.locationType] = locationType.filter;
    }

    const originLatLong = C().mapMan.latlonFromMarkerName(origin);
    const body = {
      source: sourceCode,
      origin: [originLatLong.lat, originLatLong.lng],
      dimensions: dimensions,
      resolutions: resolutions,
      location_types: locationTypes,
      support_resolutions: supportResolutions,
      sample_size: sampleSize,
      interpolation: interpolation,
    };
    return body;
  }

  // common call to backend API for loading map data, star map setup and inference.
  async intermediateCalls(
    {
      origin,
      sourceCode,
      dimensions,
      resolutions,
      supportResolutions,
      sampleSize,
      interpolation,
    },
    endpoint,
    hashValue = -1,
  ) {
    // close alert if open
    if (!this.closed) {
      this.closed = true;
    }

    const bodyParams = {
      origin,
      sourceCode,
      dimensions,
      resolutions,
      supportResolutions,
      sampleSize,
      interpolation,
    };
    const body = this.getRequestBody(bodyParams);
    //Run the source code
    const url =
      "http://localhost:8000/" +
      endpoint +
      (hashValue === -1 ? "" : "/" + hashValue);
    try {
      const response = await fetch(url, {
        method: "POST",
        body: JSON.stringify(body),
        headers: {
          "Content-Type": "application/json",
        },
      });
      if (!response.ok) {
        console.log(body);
        const result = await response.json();
        throw new Error(
          "error during calling:" +
            response.url +
            "\nreport error: " +
            response.status +
            "\n" +
            "result:" +
            "\n" +
            JSON.stringify(result),
        );
      }
      if (endpoint !== "inference") {
        const success = await response.text();
        return success;
      }
      if (endpoint === "inference") {
        const data = await response.json();
        let currentTime = new Date();
        let localesTime = currentTime.toLocaleString("en-GB");
        C().layerMan.importLayerFromSourceCode(data, { name: localesTime });
        this.success = true;
        this.closed = false;
        C().toggleDrawerSidebarRight();
        C().updateBottomBar();
      }
    } catch (error) {
      this.success = false;
      this.closed = false;
      C().updateBottomBar();
      throw error;
    }
  }

  // close the alert box
  closeAlert() {
    this.closed = true;
    C().updateBottomBar();
  }

  // update complete list of location types
  updateLocationTypes(locationTypes) {
    this.locationTypes = locationTypes;
    updateConfigLocationTypes(locationTypes);
  }

  // delete a location type by index
  deleteLocationTypeIndex(index) {
    deleteConfigLocationTypeEntry(this.locationTypes[index].id);
    C().mapMan.deleteLocationType(this.locationTypes[index].locationType);
    C().autoComplete.pop(this.locationTypes[index].locationType);
    this.locationTypes.splice(index, 1);
  }

  // add a temporary location type entry
  // used in the LocationTypeSetting component
  addTempLocationType() {
    this.locationTypes.push({
      id: randomId(),
      locationType: "",
      filter: "",
      color: Color.randomHex(),
      uncertainty: 10,
    });
  }

  // remove location types with empty location type names
  cleanLocationType() {
    this.locationTypes = this.locationTypes.filter(
      (loc_type) => loc_type.locationType !== "",
    );
  }

  // edit a location type entry
  editLocationType(locationType, index) {
    this.locationTypes[index].locationType = locationType.locationType;
    this.locationTypes[index].filter = locationType.filter;
    this.locationTypes[index].color = locationType.color;
    this.locationTypes[index].uncertainty = locationType.uncertainty;
    updateConfigLocationTypeEntry(this.locationTypes[index]);
  }
}

export default SourceCodeManager;

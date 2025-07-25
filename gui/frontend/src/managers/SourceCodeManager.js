import { C } from "./Core.js";
import { updateConfigLocationTypes, randomId, updateConfigLocationTypeEntry, deleteConfigLocationTypeEntry } from "../utils/Utility.js";
import Color from "../models/Color.js";

const defaultLocationTypes = [
  {
    "id": 2075396262,
    "locationType": "UNKNOWN",
    "filter": "",
    "color": "#0000FF",
    "uncertainty": 10
  },
  {
    "id": 1328715238,
    "locationType": "ORIGIN",
    "filter": "",
    "color": "#0000FF",
    "uncertainty": 10
  },
  {
    "id": 3525042322,
    "locationType": "VERTIPORT",
    "filter": "",
    "color": "#0000FF",
    "uncertainty": 10
  }
]

class SourceCodeManager {
  constructor() {
    this.success = true;
    this.closed = true;
    this.origin = "";
    this.locationTypes = defaultLocationTypes;
    this.interpolation = "linear";
  }

  getUncertaintyFromLocationType(locationType) {
    console.log(this.locationTypes);
    const matchedRow =  this.locationTypes.find((row) => {
      return row.locationType === locationType
    });
    if (matchedRow !== undefined) {
      return matchedRow.uncertainty;
    }
    else {
      return 0;
    }
  }

  getColorFromLocationType(locationType) {
    const matchedRow =  this.locationTypes.find((row) => {
      return row.locationType === locationType
    });
    if (matchedRow !== undefined) {
      return matchedRow.color;
    }
    return new Error("No Color found from this location type");
  }

  getListLocationType() {
    return this.locationTypes.map((entry) => entry.locationType);
  }

  getDefaultLocationTypesRows() {
    const defaultLocationType = ["UNKNOWN", "ORIGIN", "VERTIPORT"];
    return this.locationTypes.filter((row) => {
      return defaultLocationType.includes(row.locationType);
    })
  }


  getRequestBody({
    origin,
    sourceCode,
    dimensions,
    resolutions,
    supportResolutions,
    sampleSize,
    interpolation
  }) {
    // sort the location types by location type
    const sortedTypes = [...this.locationTypes].sort((a, b) => (a.locationType > b.locationType) ? 1 : -1);

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
      interpolation: interpolation
    };
    return body;
  }

  async intermediateCalls({
    origin,
    sourceCode,
    dimensions,
    resolutions,
    supportResolutions,
    sampleSize,
    interpolation
  }, endpoint, hashValue=-1) {
    // close alert if open
    if (!this.closed){
      this.closed = true;
    }

    const bodyParams = {
      origin,
      sourceCode,
      dimensions,
      resolutions,
      supportResolutions,
      sampleSize,
      interpolation
    };
    const body = this.getRequestBody(bodyParams);
    //Run the source code
    const url = "http://localhost:8000/" + endpoint + (hashValue === -1 ? "" : "/" + hashValue);
    try {
      const response = await fetch(url, {
        method: "POST",
        body: JSON.stringify(body),
        headers: {
          "Content-Type": "application/json",
        },
      });
      if (!response.ok) {
        console.log(body)
        const result = await response.json();
        throw new Error("error during calling:" + response.url + "\nreport error: " + response.status + "\n"
            + "result:" + "\n" + JSON.stringify(result)
        );
      }
      if (endpoint !== "inference") {
        const success = await response.text();
        return success;
      }
      if (endpoint === "inference") {
        const data = await response.json();
        let currentTime = new Date();
        let localesTime = currentTime.toLocaleString('en-GB');
        C().layerMan.importLayerFromSourceCode(data, { name: localesTime });
        this.success = true;
        this.closed = false;
        C().toggleDrawerSidebarRight();
        C().updateBottomBar();
      }
    }
    catch (error) {
      this.success = false;
      this.closed = false;
      C().updateBottomBar();
      throw error;
    }
  }

  closeAlert() {
    this.closed = true;
    C().updateBottomBar();
  }

  updateOrigin(origin) {
    this.origin = origin;
    C().updateBottomBar();
  }
  
  updateInterpolation(interpolation) {
    this.interpolation = interpolation;
    C().updateBottomBar();
  }

  updateLocationTypes(locationTypes) {
    this.locationTypes = locationTypes;
    updateConfigLocationTypes(locationTypes);
    // TODOS: update polygons and polylines and marker appropriately
  }

  deleteLocationTypeIndex(index) {
    deleteConfigLocationTypeEntry(this.locationTypes[index].id);
    C().mapMan.deleteLocationType(this.locationTypes[index].locationType);
    this.locationTypes.splice(index, 1);
  }

  addTempLocationType() {
    this.locationTypes.push({
      id: randomId(),
      locationType: "temp",
      filter: "",
      color: Color.randomHex(),
      uncertainty: 10
    })
  }

  editLocationType(locationType, index) {
    this.locationTypes[index].locationType = locationType.locationType;
    this.locationTypes[index].filter = locationType.filter;
    this.locationTypes[index].color = locationType.color;
    this.locationTypes[index].uncertainty = locationType.uncertainty;
    updateConfigLocationTypeEntry(this.locationTypes[index]);
  }
}

export default SourceCodeManager;

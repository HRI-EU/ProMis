import { C } from "./Core.js";
import { updateConfigLocationTypes } from "../utils/Utility.js";


class SourceCodeManager {
  constructor() {
    this.success = true;
    this.closed = true;
    this.origin = "";
    this.locationTypes = [];
    this.interpolation = "linear";
  }

  getDefaultLocationTypesRows() {
    return this.locationTypes.filter((row) => {
      const defaultLocationType = ["UNKNOWN", "ORIGIN", "VERTIPORT"];
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
}

export default SourceCodeManager;

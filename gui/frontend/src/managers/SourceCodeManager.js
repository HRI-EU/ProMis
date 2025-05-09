import { C } from "./Core.js";
import { updateConfigLocationTypes } from "../utils/Utility.js";

const defaultSourceCode = `% UAV properties
initial_charge ~ normal(90, 5).
charge_cost ~ normal(-0.1, 0.2).
weight ~ normal(0.2, 0.1).

% Weather conditions
1/10::fog; 9/10::clear.

% Visual line of sight
vlos(X) :- 
    fog, distance(X, operator) < 50;
    clear, distance(X, operator) < 100;
    clear, over(X, bay), distance(X, operator) < 400.

% Sufficient charge to return to operator
can_return(X) :-
    B is initial_charge, O is charge_cost,
    D is distance(X, operator), 0 < B + (2 * O * D).

% Permits related to local features
permits(X) :- 
    distance(X, service) < 15; distance(X, primary) < 15;
    distance(X, secondary) < 10; distance(X, tertiary) < 5;
    distance(X, crossing) < 5; distance(X, rail) < 5;
    over(X, park).

% Definition of a valid mission
landscape(X) :- 
    vlos(X), weight < 25, can_return(X); 
    permits(X), can_return(X).
`;

class SourceCodeManager {
  constructor() {
    this.hasSource = true;
    this.source = defaultSourceCode;
    this.success = true;
    this.closed = true;
    this.origin = "";
    this.edit = false;
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
    dimensionWidth
    , dimensionHeight
    , resolutionWidth
    , resolutionHeight
    , supportResolutionWidth
    , supportResolutionHeight
    , sampleSize
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

    const originLatLong = C().mapMan.latlonFromMarkerName(this.origin);
    const body = {
      source: this.source,
      origin: [originLatLong.lat, originLatLong.lng],
      dimensions: [dimensionWidth, dimensionHeight],
      resolutions: [resolutionWidth, resolutionHeight],
      location_types: locationTypes,
      support_resolutions: [supportResolutionWidth, supportResolutionHeight],
      sample_size: sampleSize,
      interpolation: this.interpolation
    };
    return body;
  }

  async intermediateCalls({
    dimensionWidth
    , dimensionHeight
    , resolutionWidth
    , resolutionHeight
    , supportResolutionWidth
    , supportResolutionHeight
    , sampleSize
  }, endpoint, hashValue=-1) {
    // close alert if open
    if (!this.closed){
      this.closed = true;
    }

    if (!this.hasSource){
      console.log("No source code!!!");
      return;
    }
    // check if origin is set
    if (this.origin === ""){
      console.log("No origin set!!!");
      return;
    }

    const bodyParams = {
      dimensionWidth
      , dimensionHeight
      , resolutionWidth
      , resolutionHeight
      , supportResolutionWidth
      , supportResolutionHeight
      , sampleSize
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
        throw new Error("error during endpoint:" + endpoint + "\nreport error: " + response.status);
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

  toggleEdit() {
    this.edit = !this.edit;
    C().updateBottomBar();
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

  /**
   * Import source code
   * @param {string} source
   */
  importSource(source) {
    
    if (source.slice(-1) == "\n") {
      source += " ";
    }

    this.hasSource = true;
    this.source = source;
    C().updateBottomBar();
  }

  //Remove the source code
  removeSource() {
    this.hasSource = false;
    this.source = "";
    C().updateBottomBar();
  }

  updateLocationTypes(locationTypes) {
    this.locationTypes = locationTypes;
    updateConfigLocationTypes(locationTypes);
    // TODOS: update polygons and polylines and marker appropriately
  }

  
}

export default SourceCodeManager;

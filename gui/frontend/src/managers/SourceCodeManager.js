import { C } from "./Core.js";
import { updateConfigLocationTypes } from "../utils/Utility.js";

class SourceCodeManager {
  constructor() {
    this.running = false;
    this.hasSource = false;
    this.source = "";
    this.success = true;
    this.closed = true;
    this.origin = "";
    this.edit = false;
    this.locationTypes = [];
  }

  //Toggle the running state of the source code
  toggleRun(dimensionWidth, dimensionHeight, resolutionWidth, resolutionHeight) {
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
    if (this.running){
      console.log("Already running!!!");
      return;
    }
    this.running = !this.running;
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
    };
    if (this.running && this.hasSource) {
      //Run the source code
      const url = "http://localhost:8000/runpromis";
      fetch(url, {
        method: "POST",
        body: JSON.stringify(body),
        headers: {
          "Content-Type": "application/json",
        },
      })
        .then((response) => response.json())
        .then((data) => {
          C().layerMan.importLayer(data, { name: "Generated Layer" });
          this.running = false;
          this.success = true;
          this.closed = false;
          C().toggleDrawerSidebarRight();
          C().updateBottomBar();
        })
        .catch((error) => {
          console.error("Error:", error.message);
          this.running = false;
          this.success = false;
          this.closed = false;
          C().updateBottomBar();
        });
    }
    C().updateBottomBar();
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

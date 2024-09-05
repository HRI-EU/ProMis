import { C } from "./Core.js";

class SourceCodeManager {
  constructor() {
    this.running = false;
    this.hasSource = false;
    this.source = "";
    this.success = true;
    this.closed = true;
    this.origin = "";
    this.start = "";
    this.edit = false;
  }

  //Toggle the running state of the source code
  toggleRun(dimensionWidth, dimensionHeight, resolutionWidth, resolutionHeight) {
    if (!this.hasSource) return;
    if (this.running) return;
    this.running = !this.running;
    const originLatLong = C().mapMan.latlonDroneFromMarkerName(this.origin);
    const body = {
      source: this.source,
      origin: [originLatLong.lat, originLatLong.lng],
      dimensions: [dimensionWidth, dimensionHeight],
      resolutions: [resolutionWidth, resolutionHeight]
    };
    if (this.start !== "") {
      const startLatLong = C().mapMan.latlonDroneFromMarkerName(this.start);
      body["start"] = [startLatLong.lat, startLatLong.lng];
    }
    if (this.running && this.hasSource) {
      //Run the source code
      const url = "http://localhost:8000/run";
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

  updateStart(start) {
    this.start = start;
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
}

export default SourceCodeManager;

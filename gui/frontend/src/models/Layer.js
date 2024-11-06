import { RenderMode } from "../managers/MapManager";

export default class Layer {
  /**
   * Check if the longitude is not NaN and is in the range [-180, 180]
   * @param {*} longitude
   * @returns {boolean} A boolean value, if the longitude is valid or not
   */
  static validLongitude(longitude) {
    return !isNaN(longitude) && longitude >= -180 && longitude <= 180;
  }

  /**
   * Check if the latitude is not NaN and is in the range [-90, 90]
   * @param {*} latitude
   * @returns {boolean} A boolean value, if the latitude is valid or not
   */
  static validLatitude(latitude) {
    return !isNaN(latitude) && latitude >= -90 && latitude <= 90;
  }

  /**
   * Check if the probability is not NaN and is in the range [0, 1]
   * @param {*} probability
   * @returns {boolean} A boolean value, if the probability is valid or not
   */
  static validProbability(probability) {
    return !isNaN(probability) && probability >= 0 && probability <= 1;
  }

  constructor(
    id,
    markers,
    hue,
    name,
    radius,
    markerDstLat,
    markerDstLng,
    markersValMinMax,
    markersLatMinMax,
    markersLngMinMax,
  ) {
    this.id = id;
    this.name = name || ""; // String type field
    this.markers = markers || []; // Array type field

    this.visible = true;
    this.settingsMenuExpanded = false;
    this.colorMenuExpanded = false;
    this.editName = false;

    this.hue = typeof hue === "number" ? hue : 0.0; // Float type field
    this.opacity = 0.3;

    this.renderMode = RenderMode.HeatmapRect;
    this.radius = radius || 1.0; // Float type field
    this.valueRange = markersValMinMax || [0, 1];
    this.markersValMinMax = markersValMinMax || [0, 1]; // [min, max] probability of markers array

    this.markersLatMinMax = markersLatMinMax || [0, 0]; // [min, max] lat of markers array
    this.markersLngMinMax = markersLngMinMax || [0, 0]; // [min, max] lng of markers array

    this.markerDstLat = markerDstLat || 0.00005;
    this.markerDstLng = markerDstLng || 0.00005;

    this.markerLayer = null;
    this.leafletOverlays = [];

    /* not used 
    this.colorMenuLatestSelection = null;
    this.colorMenuHueSlider = 0;
    */
    this.isEnable = true;
  }

  /**
   * Create a new layer from the given data
   *
   * @param {number} id
   * @param {number[][3]} data row of [lat, lng, probability] array
   * @param {number} hue color hue from 0 to 360
   * @param {string} name name of the layer
   * @param {number} radius radius of the marker
   * @returns
   */
  static parseLayer(id, data, hue, name, radius) {
    const markers = [];
    const markersValMinMax = [0, 0];
    const markersLatMinMax = [90, -90]; //Every value will be smaller than 90 and bigger than -90
    const markersLngMinMax = [180, -180];
    data.forEach((row) => {
      if (
        Layer.validLatitude(parseFloat(row[0])) &&
        Layer.validLongitude(parseFloat(row[1]))
      ) {
        markers.push({
          position: [parseFloat(row[0]), parseFloat(row[1])],
          probability: parseFloat(row[2]),
          radius: radius
        });
        //Find min max values of markers
        var val = parseFloat(row[2]);
        if (val < markersValMinMax[0]) {
          //New val min found
          markersValMinMax[0] = val;
        } else if (val > markersValMinMax[1]) {
          //New val max found
          markersValMinMax[1] = val;
        }
        var lat = parseFloat(row[0]);
        if (lat < markersLatMinMax[0]) {
          //New lat min found
          markersLatMinMax[0] = lat;
        } else if (lat > markersLatMinMax[1]) {
          //New lat max found
          markersLatMinMax[1] = lat;
        }
        var lng = parseFloat(row[1]);
        if (lng < markersLngMinMax[0]) {
          //New lng min found
          markersLngMinMax[0] = lng;
        } else if (lng > markersLngMinMax[1]) {
          //New lng max found
          markersLngMinMax[1] = lng;
        }
      }
    });

    console.log("latMinMax ", markersLatMinMax);
    console.log("lngMinMax ", markersLngMinMax);

    const markerDst = Layer.calcMarkerDst(markers, radius);
    return new Layer(
      id,
      markers,
      hue,
      name,
      radius,
      markerDst[0],
      markerDst[1],
      markersValMinMax,
      markersLatMinMax,
      markersLngMinMax,
    );
  }

  /**
   * Calculate the [lat, lng] distance based on the radius of rendered points and the first marker position
   * Distance in lat lng is not linear to meters and ratio of lat and lng changes with the position
   * Returns [0.00003, 0.00003] if no markers given
   * @param {*} markers Marker array
   * @param {*} radius Radius in meters
   * @returns {[int, int]} [x,y] array of lat,lng distances
   */
  static calcMarkerDst(markers, radius) {
    if (markers != null && markers.length > 0) {
      const latSample = markers[0].position[0];
      const markerDstLat = radius / 111111;
      const markerDstLng =
        radius / (111111 * Math.cos(latSample * (Math.PI / 180)));
      return [markerDstLat, markerDstLng];
    } else {
      return [0.00003, 0.00003];
    }
  }

  // Calculate center position [lat, lng] of given latMinMax and lngMinMax
  static calcCenterLatLng(latMinMax, lngMinMax) {
    var latCenter = latMinMax[0] + 0.5 * (latMinMax[1] - latMinMax[0]);
    var lngCenter = lngMinMax[0] + 0.5 * (lngMinMax[1] - lngMinMax[0]);
    return [latCenter, lngCenter];
  }
}

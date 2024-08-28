import L from "leaflet";
import "leaflet.heat";

import ColorHelper from "../utils/ColorHelper.js";

import { C } from "./Core.js";

import { Voronoi } from "../libs/rhill-voronoi-core.min.js";
// import icons
import drone from "../assets/icons/drone-new.png";
import landingSite from "../assets/icons/landing-pad-marker.png";

//Marker RenderMode "enum"
export class RenderMode {
  static HeatmapRect = () => "HEATMAP_RECT";
  static HeatmapCircle = () => "HEATMAP_CIRCLE";
  static Voronoi = () => "VORONOI";
}

class MapManager {
  pToSatFactor = 5; // the probability will be converted to saturation by multiplying this factor

  constructor() {
    this.map = null;
    this.initWeather = false;
    this.initToolbar = false;
    this.dynamicFeatureGroup = null;
  }

  //Called by map hook to set map reference
  setMap(map) {
    this.map = map;
    this._initMap();
  }

  /**
   * initialize the map
   */
  _initMap() {
    this.moveTo([49.8728, 8.6512]);
    this._initToolbar();
    this._initWeatherLayer();
  }

  /**
   * initialize the toolbar for the map
   */
  _initToolbar() {
    if (!this.map || this.initToolbar) return;
    var options = {
      position: "topleft", // toolbar position, options are 'topleft', 'topright', 'bottomleft', 'bottomright'
      drawText: false, // remove button to draw text
      drawMarker: false, // remove button to draw markers
      drawPolygon: false, // remove button to draw a polygon
      drawPolyline: false, // remove button to draw a polyline
      drawCircle: false, // remove button to draw a cricle
      drawCircleMarker: false, // remove button to draw a cricleMarker
      drawRectangle: false, // remove button to draw a rectangle
      cutPolygon: false, // remove a button to cut layers
      dragMode: true, // adds button to toggle global move mode
      deleteLayer: true, // adds a button to delete layers
      editMode: false, // remove button to toggle global edit mode
      rotateMode: false, // remove button to toggle rotation mode
    };

    const dynamicFeatureGroup = L.featureGroup().addTo(this.map);
    this.map.pm.setGlobalOptions({
      layerGroup: dynamicFeatureGroup,
    });
    this.dynamicFeatureGroup = dynamicFeatureGroup;
    let nameNumber = 1;

    // add leaflet.pm controls to the map
    this.map.pm.addControls(options);
    this.map.on("pm:create", function (e) {
      // update origin from source when the first drone marker is created
      const markerName = "Marker " + nameNumber++;
      // add properties to the marker
      e.layer.feature = e.layer.feature || {};
      e.layer.feature.type = "Feature";
      e.layer.feature.properties = e.layer.feature.properties || {};
      e.layer.feature.properties["shape"] = e.shape;
      e.layer.feature.properties["name"] = markerName;
      console.log("e.name", markerName);
      const firstDroneMarker = dynamicFeatureGroup.getLayers().find((layer) => {
        return layer.feature.properties["shape"] === "droneMarker";
      });
      if (firstDroneMarker) {
        C().sourceMan.updateOrigin(firstDroneMarker.feature.properties["name"]);
      }
    });
    this.map.on("pm:remove", function () {
      // update origin from source when a drone marker is removed
      const firstDroneMarker = dynamicFeatureGroup.getLayers().find((layer) => {
        return layer.feature.properties["shape"] === "droneMarker";
      });
      if (firstDroneMarker) {
        C().sourceMan.updateOrigin(firstDroneMarker.feature.properties["name"]);
      }
    });

    var droneIcon = L.icon({
      shadowUrl: null,
      iconAnchor: new L.Point(12, 12),
      iconSize: new L.Point(24, 24),
      iconUrl: drone,
    });

    var landingSiteIcon = L.icon({
      shadowUrl: null,
      iconAnchor: new L.Point(12, 12),
      iconSize: new L.Point(24, 24),
      iconUrl: landingSite,
    });

    var landingSiteMarker = this.map.pm.Toolbar.copyDrawControl("drawMarker", {
      name: "landingSiteMarker",
      title: "Landing Site Marker",
      className: "landing-site-icon",
    });
    landingSiteMarker.drawInstance.setOptions({
      markerStyle: { icon: landingSiteIcon },
    });

    var droneMarker = this.map.pm.Toolbar.copyDrawControl("drawMarker", {
      name: "droneMarker",
      title: "Drone Marker",
      className: "drone-icon",
    });
    droneMarker.drawInstance.setOptions({
      markerStyle: { icon: droneIcon },
    });
    this.initToolbar = true;
  }

  /**
   * initialize the weather layer
   */
  _initWeatherLayer() {
    if (!this.initWeather) {
      var clouds = L.OWM.clouds({
        showLegend: false,
        opacity: 0.5,
        appId: "ab828bf1285303acbf4f7b0215119208",
      });
      var cloudscls = L.OWM.cloudsClassic({
        showLegend: false,
        opacity: 0.5,
        appId: "ab828bf1285303acbf4f7b0215119208",
      });
      var precipitation = L.OWM.precipitation({
        showLegend: false,
        opacity: 0.5,
        appId: "ab828bf1285303acbf4f7b0215119208",
      });
      var precipitationcls = L.OWM.precipitationClassic({
        showLegend: false,
        opacity: 0.5,
        appId: "ab828bf1285303acbf4f7b0215119208",
      });
      var rain = L.OWM.rain({
        showLegend: false,
        opacity: 0.5,
        appId: "ab828bf1285303acbf4f7b0215119208",
      });
      var raincls = L.OWM.rainClassic({
        showLegend: false,
        opacity: 0.5,
        appId: "ab828bf1285303acbf4f7b0215119208",
      });
      var snow = L.OWM.snow({
        showLegend: false,
        opacity: 0.5,
        appId: "ab828bf1285303acbf4f7b0215119208",
      });
      var pressure = L.OWM.pressure({
        showLegend: false,
        opacity: 0.5,
        appId: "ab828bf1285303acbf4f7b0215119208",
      });
      var pressurecntr = L.OWM.pressureContour({
        showLegend: false,
        opacity: 0.5,
        appId: "ab828bf1285303acbf4f7b0215119208",
      });
      var temp = L.OWM.temperature({
        showLegend: false,
        opacity: 0.5,
        appId: "ab828bf1285303acbf4f7b0215119208",
      });
      var wind = L.OWM.wind({
        showLegend: false,
        opacity: 0.5,
        appId: "ab828bf1285303acbf4f7b0215119208",
      });

      var overlayMaps = {
        Clouds: clouds,
        "Clouds Classic": cloudscls,
        Precipitation: precipitation,
        "Precipitation Classic": precipitationcls,
        Rain: rain,
        "Rain Classic": raincls,
        Snow: snow,
        Pressure: pressure,
        "Pressure Contour": pressurecntr,
        Temperature: temp,
        Wind: wind,
      };
      L.control
        .layers(undefined, overlayMaps, { position: "bottomright" })
        .addTo(this.map);
      this.initWeather = true;
    }
  }

  /**
   * Zoom in by one step
   */
  zoomIn() {
    this.map.zoomIn();
  }

  /**
   * Zoom out by one step
   */
  zoomOut() {
    this.map.zoomOut();
  }

  /**
   * Move the map to the given position
   * @param {[lat, lon]} pos
   */
  moveTo(pos) {
    this.map.setView(pos);
  }

  /**
   * Call to remove all drawn markers of type Rectangle or Circle or Polygon
   */
  removeMarkers() {
    this.map.eachLayer((layer) => {
      if (
        layer instanceof L.Circle ||
        layer instanceof L.Rectangle ||
        layer instanceof L.Polygon
      ) {
        layer.remove();
      }
    });
  }

  /**
   * Remove old markers and redraw all markers on the map
   */
  refreshMap() {
    //Remove all old markers
    this.removeMarkers();
    //Draw all layers (in reversed order to draw top layer (position 0) last)
    C()
      .layerMan.layers.toReversed()
      .map((currentLayer, layerIndex) => {
        console.log("renderLayers currentLayer: ", currentLayer);
        if (!C().layerMan.hideAllLayers && currentLayer.visible) {
          const layerGroup = new L.LayerGroup().addTo(this.map);
          let voronoiPolygonDict = null;
          if (currentLayer.renderMode === RenderMode.Voronoi) {
            voronoiPolygonDict = this.renderLayerToVoronoi(
              currentLayer,
              layerIndex,
            );
            console.log("polygons: ", voronoiPolygonDict);
          }
          const satFactor =
            100 /
            Math.max(
              ...currentLayer.markers.map((marker) => marker.probability),
            );

          const markers = currentLayer.markers.map((marker) => {
            const positive = marker.probability >= 0;
            let sat = Math.abs(Math.round(marker.probability * satFactor));
            var hsl = ColorHelper.calcHslFromParams(
              currentLayer.hue,
              sat,
              positive,
            );

            var hsla = ColorHelper.calcHslaFromParams(
              currentLayer.hue,
              sat,
              currentLayer.opacity,
              positive,
            );

            if (
              marker.probability >= currentLayer.valueRange[0] &&
              marker.probability <= currentLayer.valueRange[1]
            ) {
              var createdMarker = null;
              switch (currentLayer.renderMode) {
                case RenderMode.HeatmapRect:
                  // Creating rectOptions
                  var rectOptions = {
                    fillColor: hsl,
                    weight: 1,
                    fillOpacity: currentLayer.opacity,
                    stroke: false,
                    pathOptions: {
                      color: hsl,
                    },
                  };
                  // Creating a rectangle
                  var rectangle = new L.rectangle(
                    this.calcRectBounds(
                      marker,
                      currentLayer.markerDstLat,
                      currentLayer.markerDstLng,
                    ),
                    rectOptions,
                  );
                  createdMarker = rectangle;
                  break;
                case RenderMode.HeatmapCircle:
                  // Creating circleOptions
                  var circleOptions = {
                    fillColor: hsl,
                    radius: currentLayer.radius,
                    fillOpacity: currentLayer.opacity,
                    stroke: false,
                    pathOptions: {
                      color: hsl,
                    },
                  };
                  // Creating a circle
                  var circle = new L.circle(marker.position, circleOptions);
                  createdMarker = circle;
                  break;
                case RenderMode.Voronoi:
                  // console.log(marker);
                  var key = JSON.stringify([
                    marker.position[0],
                    marker.position[1],
                  ]);
                  // console.log("key: ", key);
                  var voronoiPolygon = voronoiPolygonDict[key];
                  // console.log("voronoiPolygon: ", voronoiPolygon);

                  if (voronoiPolygon) {
                    // Creating polygonOptions
                    var polygonOptions = {
                      fillColor: hsl,
                      fillOpacity: currentLayer.opacity,
                      weight: 1.5,
                      color: hsla, //Outline color
                    };
                    // Creating a polygon
                    var polygon = new L.polygon(voronoiPolygon, polygonOptions);
                    createdMarker = polygon;
                  } else {
                    console.error("Voronoi polygon not found for key: ", key);
                    return null; // or handle the missing polygon in some way
                  }
              }
              layerGroup.addLayer(createdMarker);
              this.addPopup(
                createdMarker,
                marker.probability,
                marker.position[0],
                marker.position[1],
              );
              // Add feature properties to marker
              var feature = (createdMarker.feature =
                createdMarker.feature || {});
              feature.type = "Feature";
              feature.properties = feature.properties || {};
              feature.properties["value"] = marker.probability;
              feature.properties["layer"] = currentLayer.name;
              // calculate hex from hsl
              const hex = ColorHelper.hslToHex(
                currentLayer.hue,
                Math.round(marker.probability * satFactor),
                50,
              );
              feature.properties["fill"] = hex;
              feature.properties["fill-opacity"] = currentLayer.opacity;
              // add radius property if render mode is circle
              if (currentLayer.renderMode === RenderMode.HeatmapCircle) {
                feature.properties["radius"] = currentLayer.radius;
              }

              return createdMarker;
            }
          });
          currentLayer.leafletOverlays = markers;
          currentLayer.markerLayer = layerGroup;
        }
      });
  }

  /**
   * Binds popup to given element
   * @param {*} elem
   * @param {*} val
   * @param {*} lat
   * @param {*} lng
   * @returns
   */
  addPopup(elem, val, lat, lng) {
    // specify popup options
    var customOptions = {
      color: "red",
      background: "#ff0000",
      className: "stylePopup",
    };

    elem.bindPopup(
      "Val: " + val + "<br>" + "Lat: " + lat + "<br>" + "Lng: " + lng + "<br>",
      customOptions,
    );
    return elem;
  }

  /**
   * Calculate [(lat,lng), (lat,lng)] positions based on marker position and lat/lng distances to span a rectangle between those points
   * @param {*} marker marker from layer class
   * @param {*} markerDstLat
   * @param {*} markerDstLng
   * @returns [(lat,lng), (lat,lng)] position
   */
  calcRectBounds(marker, markerDstLat, markerDstLng) {
    return new L.latLngBounds(
      [marker.position[0] - markerDstLat, marker.position[1] - markerDstLng],
      [marker.position[0] + markerDstLat, marker.position[1] + markerDstLng],
    );
  }

  /**
   * render layer to voronoi tiles
   * @param {*} layer
   * @param {*} layerIndex
   * @returns array of polygons
   */
  renderLayerToVoronoi = (layer) => {
    // Extract the positions of the markers in the layer
    const positions = layer.markers.map((marker) => marker.position);
    const markerDict = {};
    const sites = positions.map((point) => ({ x: point[0], y: point[1] })); // Convert to rhill format
    const minx = Math.min(...sites.map((site) => site.x));
    const miny = Math.min(...sites.map((site) => site.y));
    const maxx = Math.max(...sites.map((site) => site.x));
    const maxy = Math.max(...sites.map((site) => site.y));
    const bbox = { xl: minx, xr: maxx, yt: miny, yb: maxy };
    var voronoi = new Voronoi();
    var result = voronoi.compute(sites, bbox);
    var cells = result.cells;

    for (let i = 0; i < cells.length; i++) {
      markerDict[JSON.stringify([cells[i].site.x, cells[i].site.y])] = cells[
        i
      ].halfedges.map((halfedge) => [
        halfedge.getStartpoint().x,
        halfedge.getStartpoint().y,
      ]);
    }

    return markerDict;
  };

  /**
   * Update the color of the markers in the layer
   * @param {*} layer
   */
  updateLayerColor(layer) {
    // calculate the satFactor based on the probability range
    let satFactor = 100 / layer.markersValMinMax[1];
    layer.markers.forEach((marker, index) => {
      // ignore markers outside the value range
      if (
        marker.probability < layer.valueRange[0] ||
        marker.probability > layer.valueRange[1]
      ) {
        return;
      }
      const positive = marker.probability >= 0;
      let sat = Math.abs(Math.round(marker.probability * satFactor));
      // calculate the new color
      var hsl = ColorHelper.calcHslFromParams(
        layer.hue,
        sat,
        positive,
      );
      layer.leafletOverlays[index].setStyle({
        fillColor: hsl,
        color: hsl,
      });
    });
  }
  
  listDroneMarkers() {
    let droneMarkers = [];
    if (!this.dynamicFeatureGroup) {
      return droneMarkers;
    }
    this.dynamicFeatureGroup.eachLayer((layer) => {
      if (layer.feature.properties["shape"] === "droneMarker") {
        droneMarkers.push(layer);
      }
    });
    return droneMarkers;
  }

  latlonDroneFromMarkerName(markerName) {
    let droneMarkers = this.listDroneMarkers();
    for (let i = 0; i < droneMarkers.length; i++) {
      if (droneMarkers[i].feature.properties["name"] === markerName) {
        return droneMarkers[i].getLatLng();
      }
    }
    return null;
  }


  recenterMap(latLong){
    console.log("recenterMap: ", latLong);
    this.map.setView(latLong);
  }
}

export default MapManager;

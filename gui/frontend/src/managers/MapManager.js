import L from "leaflet";
import "leaflet.heat";
import * as turf from "@turf/turf";

import ColorHelper from "../utils/ColorHelper.js";
import { updateDynamicLayerEntry, deleteDynamicLayerEntry, updateConfigDynamicLayers, randomId } from "../utils/Utility.js";

import { C } from "./Core.js";
import { getDefaultMarker, getDroneIcon, getLandingPadIcon } from "../utils/getIcons.js";

import { Voronoi } from "../libs/rhill-voronoi-core.min.js";

//Marker RenderMode "enum"
export class RenderMode {
  static HeatmapRect = "HEATMAP_RECT";
  static HeatmapCircle = "HEATMAP_CIRCLE";
  static Voronoi = "VORONOI";
}

class MapManager {
  pToSatFactor = 5; // the probability will be converted to saturation by multiplying this factor

  static icons = {};

  constructor() {
    this.map = null;
    this.initWeather = false;
    this.initToolbar = false;
    this.dynamicFeatureGroup = null;
    
    this.nameNumber = 1;
    this._onClickFunction = new Map();
    this.bBoxFeatureGroup = null;
    this.svgElement = null;
    this.svgOverlay = null;
  }

  getDynamicLayer(layer) {
    if (layer.feature.properties["shape"] === "Line") {
      return this.getPolyline(layer);
    }
    else if (layer.feature.properties["shape"] === "Polygon") {
      return this.getPolygon(layer);
    }
    else {
      return this.getMarker(layer);
    }
  }

  getMarker(layer) {
    return {
      id: layer.feature.properties["id"],
      name: layer.feature.properties["name"],
      latlng: [layer.getLatLng().lat, layer.getLatLng().lng],
      shape: layer.feature.properties["shape"],
      location_type: layer.feature.properties["locationType"],
      color: layer.feature.properties["color"],
    }
  }

  // get markers from map
  getMarkers() {
    // marker of type {name: string, latlng: [lat, lon], shape: string}
    let markers = [];
    if (!this.dynamicFeatureGroup) {
      return markers;
    } 
    this.dynamicFeatureGroup.eachLayer((layer) => {
      if (layer.options.pane === "markerPane") {
        markers.push(this.getMarker(layer));
      }
    });
    return markers;
  }

  getPolyline(layer) {
    return {
      id: layer.feature.properties["id"],
      latlngs: layer.getLatLngs().map((latlng) => [latlng.lat, latlng.lng]),
      location_type: layer.feature.properties["locationType"],
      color: layer.feature.properties["color"],
    }
  }

  getPolylines() {
    let polylines = [];
    if (!this.dynamicFeatureGroup) {
      return polylines;
    }
    this.dynamicFeatureGroup.eachLayer((layer) => {
      if (layer.feature.properties["shape"] === "Line") {
        polylines.push(this.getPolyline(layer));
      }
    });
    return polylines;
  }

  getPolygon(layer) {
    let holes = [];
    if (layer.getLatLngs().length > 1) {
      holes = layer.getLatLngs().slice(1).map((latlngs) => latlngs.map((latlng) => [latlng.lat, latlng.lng]));
    }
    return {
      id: layer.feature.properties["id"],
      latlngs: layer.getLatLngs()[0].map((latlng) => [latlng.lat, latlng.lng]),
      holes: holes,
      location_type: layer.feature.properties["locationType"],
      color: layer.feature.properties["color"],
    }
  }

  getPolygons() {
    let polygons = [];
    if (!this.dynamicFeatureGroup) {
      return polygons;
    }
    this.dynamicFeatureGroup.eachLayer((layer) => {
      if (layer.feature.properties["shape"] === "Polygon") {
        polygons.push(this.getPolygon(layer));
      }
    });
    return polygons;
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
    this._initToolbar();
    //this._initWeatherLayer();
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
      drawPolygon: true, // remove button to draw a polygon
      drawPolyline: true, // remove button to draw a polyline
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

    // add leaflet.pm controls to the map
    this.map.pm.addControls(options);

    this.map.on("pm:create", function ({ shape, layer }) {
      if (layer.options.pane === "markerPane") {
        MapManager._onCreatedMarker(shape, layer);
      }
      else if (shape === "Line"){
        MapManager._onCreatedLine(shape, layer);
        
      } else if (shape === "Polygon") {  
        MapManager._onCreatedPolygon(shape, layer);
      }
    });
    this.map.on("pm:remove", function ({ shape, layer }) {
      if (layer.options.pane === "markerPane") {
        // update origin from source when the removed drone marker is the origin
        if (layer.feature.properties["name"] === C().sourceMan.origin) {
          // find the first marker and set it as the new origin
          const markers = C().mapMan.listOriginMarkers();
          if (markers.length > 0) {
            C().sourceMan.updateOrigin(markers[0].feature.properties["name"]);
          } else {
            C().sourceMan.updateOrigin("");
          }
        }
        else {
          // update bottombar
          C().updateBottomBar();
        }
        
        // update the configuration data on the backend
        deleteDynamicLayerEntry(C().mapMan.getMarker(layer));
      }
      else if (shape === "Line"){
        deleteDynamicLayerEntry(C().mapMan.getPolyline(layer));
      } else if (shape === "Polygon") {  
        deleteDynamicLayerEntry(C().mapMan.getPolygon(layer));
      }
    });

    let defaultIcon = getDefaultMarker();

    MapManager.icons["defaultMarker"] = getDefaultMarker;

    var defaultMarker = this.map.pm.Toolbar.copyDrawControl("drawMarker", {
      name: "defaultMarker",
      title: "Default Marker",
      className: "leaflet-pm-icon-marker",
    });
    defaultMarker.drawInstance.setOptions({
      markerStyle: { icon: defaultIcon },
    });

    var droneIcon =  getDroneIcon();

    MapManager.icons["droneMarker"] = getDroneIcon;

    var landingSiteIcon = getLandingPadIcon();

    MapManager.icons["landingSiteMarker"] = getLandingPadIcon;

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

  static _onCreatedMarker(shape, layer) {
    // update origin from source when the first drone marker is created
    const markerName = "Marker " + C().mapMan.nameNumber++;
    //console.log(layer);
    // add properties to the marker
    if (shape === "landingSiteMarker") {
      const color = C().sourceMan.getDefaultLocationTypesRows().find((row) => row.locationType === "VERTIPORT").color;
      MapManager._initLayerProperties(layer, markerName, shape, "VERTIPORT", color);
      layer.setIcon(MapManager.icons[shape](color));
    } else {
      const color = C().sourceMan.getDefaultLocationTypesRows().find((row) => row.locationType === "UNKNOWN").color;
      MapManager._initLayerProperties(layer, markerName, shape, "UNKNOWN", color);
      layer.setIcon(MapManager.icons[shape](color));
    }
    // listen to the edit event to update the configuration data on the backend
    layer.on("pm:edit", function () {
      updateDynamicLayerEntry(C().mapMan.getMarker(layer));
      //console.log(C().mapMan.getMarkers());
      console.log("marker edited now");
    });

    // update bottombar
    C().updateBottomBar();

    // update the configuration data on the backend
    updateDynamicLayerEntry(C().mapMan.getMarker(layer));
  }

  static _onCreatedLine(shape, layer) {
    // add properties
    const color = C().sourceMan.getDefaultLocationTypesRows().find((row) => row.locationType === "UNKNOWN").color;
    MapManager._initLayerProperties(layer, "", shape, "UNKNOWN", color);
    // listen to the edit event to update the configuration data on the backend
    layer.on("pm:edit", function () {
      console.log("line edited")
      updateDynamicLayerEntry(C().mapMan.getPolyline(layer));
    });
    layer.setStyle({ color: color });
    // update the configuration data on the backend
    updateDynamicLayerEntry(C().mapMan.getPolyline(layer));
  }

  static _onCreatedPolygon(shape, layer) {
    // add properties
    const color = C().sourceMan.getDefaultLocationTypesRows().find((row) => row.locationType === "UNKNOWN").color;
    MapManager._initLayerProperties(layer, "", shape, "UNKNOWN", color);
    // listen to the edit event to update the configuration data on the backend
    layer.on("pm:edit", function () {
      updateDynamicLayerEntry(C().mapMan.getPolygon(layer));
    });
    layer.setStyle({ color: color });
    // update the configuration data on the backend
    updateDynamicLayerEntry(C().mapMan.getPolygon(layer));
  }

  static _initLayerProperties(layer, name, shape, locationType = "UNKNOWN", color = "black", id = null) {
    layer.feature = layer.feature || {};
    layer.feature.type = "Feature";
    layer.feature.properties = layer.feature.properties || {};
    if (id) {
      layer.feature.properties["id"] = id;
    } else {
      layer.feature.properties["id"] = randomId().toString();
    }
    layer.feature.properties["shape"] = shape;
    layer.feature.properties["name"] = name;
    layer.feature.properties["locationType"] = locationType;
    layer.feature.properties["color"] = color;
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
    console.log("removing...Markers");
    C().layerMan.layers.forEach((layer) => {
      if (layer.markerLayer) {
        this.map.removeLayer(layer.markerLayer);
        layer.markerLayer = null;
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
      .forEach((currentLayer, layerIndex) => {
        //console.log("renderLayers currentLayer: ", currentLayer);
        if (!C().layerMan.hideAllLayers && currentLayer.visible) {
          console.log("renderLayers currentLayer...");
          const layerGroup = new L.LayerGroup().addTo(this.map);
          let voronoiPolygonDict = null;
          if (currentLayer.renderMode === RenderMode.Voronoi) {
            voronoiPolygonDict = this.renderLayerToVoronoi(
              currentLayer,
              layerIndex,
            );
            //console.log("polygons: ", voronoiPolygonDict);
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

            /*var hsla = ColorHelper.calcHslaFromParams(
              currentLayer.hue,
              sat,
              currentLayer.opacity,
              positive,
            );*/

            if (
              marker.probability >= currentLayer.valueRange[0] - 0.000000001 &&
              marker.probability <= currentLayer.valueRange[1] + 0.000000001
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
                      stroke: false,
                      //color: hsla, //Outline color
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

  listMarkers() {
    let markers = [];
    if (!this.dynamicFeatureGroup) {
      return markers;
    }
    return this.dynamicFeatureGroup.getLayers().filter((layer) => layer.options.pane === "markerPane");
  }

  listOriginMarkers() {
    let markers = [];
    if (!this.dynamicFeatureGroup) {
      return markers;
    }
    return this.dynamicFeatureGroup.getLayers().filter((layer) => {
      return layer.options.pane === "markerPane" && layer.feature.properties["locationType"] === "ORIGIN";
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

  latlonFromMarkerName(markerName) {
    let droneMarkers = this.listMarkers();
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

  // import all marker from json config file
  importMarkers(markers) {
    if (!this.dynamicFeatureGroup) {
      return;
    }
    // add markers
    markers.forEach((marker) => {
      const markerId = marker.id;
      const markerName = marker.name;
      const markerPosition = marker.latlng;
      const markerShape = marker.shape;
      const markerColor = marker.color;
      const markerLocationType = marker.location_type;
      const markerLayer = new L.marker(markerPosition, { icon: MapManager.icons[markerShape](markerColor) });
      markerLayer.on("pm:edit", function() {
        // update the configuration data on the backend
        updateDynamicLayerEntry(C().mapMan.getMarker(markerLayer));
        console.log("marker edited");
      });
      MapManager._initLayerProperties(markerLayer, markerName, markerShape, markerLocationType, markerColor, markerId);
      this.dynamicFeatureGroup.addLayer(markerLayer);

      // update number of markers to avoid name conflicts
      // ignore if marker name is not in the format "Marker x" with x is a number
      if (markerName.startsWith("Marker ")) {
        const number = parseInt(markerName.split(" ")[1]);
        // check if the number is greater than the current nameNumber and number is a valid number
        if (!isNaN(number) && number >= this.nameNumber) {
          this.nameNumber = number + 1;
        }
      }
    });
  }

  _cleanupDynamicLayer(layers){
    if (!this.dynamicFeatureGroup) {
      return;
    }
    // remove all dynamic layers that have the same id as the layers in the list
    layers.forEach((layer) => {
      this.dynamicFeatureGroup.eachLayer((existingLayer) => {
        if (existingLayer.feature.properties["id"] === layer.id) {
          this.dynamicFeatureGroup.removeLayer(existingLayer);
        }
      });
    });
  }

  // import all external layers from backend type=1: marker, type=2: polyline, type=3: polygon
  importExternal(dynamicLayers) {
    if (!this.dynamicFeatureGroup) {
      return;
    }

    this._cleanupDynamicLayer(dynamicLayers.markers);
    this._cleanupDynamicLayer(dynamicLayers.polylines);
    this._cleanupDynamicLayer(dynamicLayers.polygons);
    
    // import markers, polylines and polygons
    this.importMarkers(dynamicLayers.markers);
    this.importPolylines(dynamicLayers.polylines);
    this.importPolygons(dynamicLayers.polygons);

  }


  // import all polylines from json config file
  importPolylines(polylines) {
    if (!this.dynamicFeatureGroup) {
      return;
    }
    // add polylines
    polylines.forEach((polyline) => {
      const polylineLayer = new L.polyline(polyline.latlngs);
      polylineLayer.on("pm:edit", function() {
        // update the configuration data on the backend
        updateDynamicLayerEntry(C().mapMan.getPolyline(polylineLayer));
      });
      MapManager._initLayerProperties(polylineLayer, "", "Line", polyline.location_type, polyline.color, polyline.id);
      // add color style to the line
      if (polyline.color) {
        polylineLayer.setStyle({
          color: polyline.color,
        });
      }

      this.dynamicFeatureGroup.addLayer(polylineLayer);
    });
  }

  // import all polygons from json config file
  importPolygons(polygons) {
    if (!this.dynamicFeatureGroup) {
      return;
    }
    // add polygons
    polygons.forEach((polygon) => {
      let polygonLatlngs = [];
      polygonLatlngs.push(polygon.latlngs);
      // add holes to the polygon
      if (polygon.holes) {
        polygonLatlngs = polygonLatlngs.concat(polygon.holes);
      }
      const polygonLayer = new L.polygon(polygonLatlngs);
      polygonLayer.on("pm:edit", function() {
        // update the configuration data on the backend
        updateDynamicLayerEntry(C().mapMan.getPolygon(polygonLayer));
      });
      MapManager._initLayerProperties(polygonLayer, "", "Polygon", polygon.location_type, polygon.color, polygon.id);
      // add color style to the polygon
      if (polygon.color) {
        polygonLayer.setStyle({
          fillColor: polygon.color,
          color: polygon.color,
        });
      }

      this.dynamicFeatureGroup.addLayer(polygonLayer);
    });
    //console.log("polygon added!!")
  }

  // initialize the location type click event listeners
  // type: all, marker, polyline, polygon, vertiport
  setLocationTypeOnClick(locationType, color, type="all") {
    if (!this.dynamicFeatureGroup) {
      return;
    }
    // remove the old click event listeners
    this._onClickFunction.forEach((value, key) => {
      key.off("click", value);
    });

    this.dynamicFeatureGroup.eachLayer((layer) => {
      const onClickFunc = function() {
        
        // update the properties of the layer
        layer.feature.properties["locationType"] = locationType;
        layer.feature.properties["color"] = color;

        // update the color of the layer for line and polygon
        if (layer.feature.properties["shape"] === "Line" || layer.feature.properties["shape"] === "Polygon") {
          layer.setStyle({
            fillColor: color,
            color: color,
          });
        }
        else {
          // update the icon of the markers
          let markerShape = layer.feature.properties["shape"];
          layer.setIcon(MapManager.icons[markerShape](color));
        }

        // update the configuration data on the backend
        updateDynamicLayerEntry(C().mapMan.getDynamicLayer(layer));
      };
      if (type === "marker"){
        if (layer.feature.properties["shape"] === "Line" || layer.feature.properties["shape"] === "Polygon") {
          return;
        }
      }
      if (type === "vertiport"){
        if (layer.feature.properties["shape"] !== "landingSiteMarker") {
          return;
        }
      }
      layer.on("click", onClickFunc);
      this._onClickFunction.set(layer, onClickFunc);
    });
  }

  // remove the location type click event listeners
  removeLocationTypeOnClick() {
    document.body.style.cursor = 'default';
    if (!this.dynamicFeatureGroup) {
      return;
    }
    this._onClickFunction.forEach((value, key) => {
      key.off("click", value);
    });
  }

  // update the color of the location type
  // used by the LocationTypeSetting component when the color is changed
  updateLocationTypeColor(locationType, color) {
    if (!this.dynamicFeatureGroup) {
      return;
    }
    this.dynamicFeatureGroup.eachLayer((layer) => {
      if (layer.feature.properties["locationType"] === locationType) {
        // update the color of the layer for line and polygon
        if (layer.feature.properties["shape"] === "Line" || layer.feature.properties["shape"] === "Polygon") {
          layer.setStyle({
            fillColor: color,
            color: color,
          });
        }
        else {
          // update the icon of the markers
          let markerShape = layer.feature.properties["shape"];
          layer.setIcon(MapManager.icons[markerShape](color));
        }


        layer.feature.properties["color"] = color;
      }
    });
    // update the configuration data on the backend
    updateConfigDynamicLayers(C().mapMan.getMarkers(), C().mapMan.getPolylines(), C().mapMan.getPolygons());
  }

  // update the location type of the markers
  // used by the LocationTypeSetting component when the location type is changed
  updateLocationType(newLocationType, oldLocationType) {
    if (!this.dynamicFeatureGroup) {
      return;
    }
    // ignore newly created location types
    // bug: the location type of the marker is empty when it is created
    // so the location type of the marker is implicitly set to a new not existing location type
    // when a new location type is created
    // this new location type choose all the markers that have empty location type
    // which is not the desired behavior
    if (oldLocationType === "") {
      return;
    }
    //console.log("oldLocationType: ", oldLocationType);
    //console.log("newLocationType: ", newLocationType);
    this.dynamicFeatureGroup.eachLayer((layer) => {
      // update the location type of the marker if it has the old location type
      if (layer.feature.properties["locationType"] === oldLocationType) {
        layer.feature.properties["locationType"] = newLocationType;
      }
    });
    // update the configuration data on the backend
    updateConfigDynamicLayers(C().mapMan.getMarkers(), C().mapMan.getPolylines(), C().mapMan.getPolygons());
  }

  deleteLocationType(locationType) {
    if (!this.dynamicFeatureGroup) {
      return;
    }
    this.dynamicFeatureGroup.eachLayer((layer) => {
      if (layer.feature.properties["locationType"] === locationType) {
        this.dynamicFeatureGroup.removeLayer(layer);
      }
    });
    // update the configuration data on the backend
    updateConfigDynamicLayers(C().mapMan.getMarkers(), C().mapMan.getPolylines(), C().mapMan.getPolygons());
  }

  _getBBox(originLatlng, width, height) {
    const origin = turf.point([originLatlng.lng, originLatlng.lat]);
    // calculate coordinates of the rectangle bounding box based on the origin and the width and height of box
    const north = turf.destination(origin, height / 2000, 0, { units: "kilometers" });
    const east = turf.destination(origin, width / 2000, 90, { units: "kilometers" });
    const south = turf.destination(origin, height / 2000, 180, { units: "kilometers" });
    const west = turf.destination(origin, width / 2000, -90, { units: "kilometers" });
    const bbox = turf.bbox(turf.featureCollection([origin, north, east, south, west]));
    return L.latLngBounds([bbox[1], bbox[0]], [bbox[3], bbox[2]]);
  }

  _createGrid(originLatlng, width, height, resolutionWidth, resolutionHeight,
              color = "#0000ff", borderWeight = 1, fillOpacity = 0.2) {
    // calculate the coordinates of the bounding box
    const bbox = this._getBBox(originLatlng, width, height);
    // calculate the width and height of each grid cell
    const cellWidth = (bbox.getEast() - bbox.getWest()) / resolutionWidth;
    const cellHeight = (bbox.getNorth() - bbox.getSouth()) / resolutionHeight;
    // create the grid
    for (let i = 0; i < resolutionWidth; i++) {
      for (let j = 0; j < resolutionHeight; j++) {
        const cell = L.rectangle(
          [
            [bbox.getSouth() + j * cellHeight, bbox.getWest() + i * cellWidth],
            [bbox.getSouth() + (j + 1) * cellHeight, bbox.getWest() + (i + 1) * cellWidth],
          ],
          { color: color, weight: borderWeight, fillOpacity: fillOpacity },
        );
        this.bBoxFeatureGroup.addLayer(cell);
      }
    }
  }

  // highlight the boundary of the selected area
  highlightBoundary(origin,
                    dimensionWidth, 
                    dimensionHeight, 
                    resolutionWidth, 
                    resolutionHeight,
                    supportResolutionWidth,
                    supportResolutionHeight,
                  ) {
    // do nothing if origin is not selected or any of the dimension or resolution is not set
    if (origin === "") {
      return;
    }
    console.log("highlightBoundary");

    // remove the old bounding box layer
    this.unhighlightBoundary();
    // create feature group to store the bounding box layer
    this.bBoxFeatureGroup = L.featureGroup().addTo(this.map);
    // calculate the bounding box
    const originLatlng = C().mapMan.latlonFromMarkerName(origin);
    const bbox = this._getBBox(originLatlng, dimensionWidth, dimensionHeight);
    // create the bounding box layer
    const bBoxLayer = L.rectangle(bbox, { color: "white", weight: 1 });
    this.bBoxFeatureGroup.addLayer(bBoxLayer);

    // create the grid
    
    this._createGrid(originLatlng, dimensionWidth, dimensionHeight, resolutionWidth, resolutionHeight, "#d9a766", 1);
    this._createGrid(originLatlng, dimensionWidth, dimensionHeight, supportResolutionWidth, supportResolutionHeight, "#31e30e", 2, 0);
    // zoom to the bounding box
    //this.map.fitBounds(bbox);
  }


  highlightBoundaryAlter(origin,
    dimensionWidth, 
    dimensionHeight, 
    resolutionWidth, 
    resolutionHeight,
    supportResolutionWidth,
    supportResolutionHeight,
  ) {
     // do nothing if origin is not selected or any of the dimension or resolution is not set
     if (origin === "") {
      return;
    }
    // remove the old bounding box layer
    this.unhighlightBoundaryAlter();

    // calculate the bounding box
    const originLatlng = C().mapMan.latlonFromMarkerName(origin);
    const bbox = this._getBBox(originLatlng, dimensionWidth, dimensionHeight);

    // create the svg overlay
    let svgElement = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svgElement.setAttribute('xmlns', "http://www.w3.org/2000/svg");
    svgElement.setAttribute('viewBox', "0 0 " + dimensionWidth + " " + dimensionHeight);

    const cellWidth = 1 / resolutionWidth;
    const cellHeight = 1 / resolutionHeight;
    const cellWidthSupport = 1 / supportResolutionWidth;
    const cellHeightSupport = 1 / supportResolutionHeight;

    const strokeWidth = 1 / (Math.max(resolutionWidth, resolutionHeight) * 50);
    const strokeWidthSupport = 1 / (Math.max(supportResolutionWidth, supportResolutionHeight) * 25);

    svgElement.innerHTML = `
      <defs>

        <pattern id="Pattern1" width="${cellWidth}" height="${cellHeight}" patternContentUnits="objectBoundingBox">
            <rect x="0" y="0" width="${cellWidth}" height="${cellHeight}" fill="#d9a766" stroke="brown" stroke-width="${strokeWidth}" fill-opacity="0.2" stroke-opacity="1"></rect>
        </pattern>

        <pattern id="Pattern2" width="${cellWidthSupport}" height="${cellHeightSupport}" patternContentUnits="objectBoundingBox">
            <rect x="0" y="0" width="${cellWidthSupport}" height="${cellHeightSupport}" fill="#31e30e" stroke="green" stroke-width="${strokeWidthSupport}" fill-opacity="0" stroke-opacity="1"></rect>
        </pattern>

      </defs>

      <rect fill="url(#Pattern1)" width="${dimensionWidth}" height="${dimensionHeight}"></rect>
      <rect fill="url(#Pattern2)" width="${dimensionWidth}" height="${dimensionHeight}"></rect>
    `;
    // create the svg overlay
    this.svgOverlay = L.svgOverlay(svgElement, bbox).addTo(this.map);

    this.svgElement = svgElement;
  }

  // remove the bounding box feature group if it exists
  unhighlightBoundary() {
    if (this.bBoxFeatureGroup) {
      console.log("unhighlightBoundary");
      this.map.removeLayer(this.bBoxFeatureGroup);
    }
  }

  unhighlightBoundaryAlter() {
    console.log("unhighlightBoundaryAlter");
    if (this.svgElement) {
      this.svgElement.remove();
      this.svgElement = null;
    }
    if (this.svgOverlay) {
      this.map.removeLayer(this.svgOverlay);
      this.svgOverlay = null;
    }
  }

  toggleDynamicOnTop(onTop) {
    if (onTop) {
      this.dynamicFeatureGroup.bringToFront();
    } else {
      this.dynamicFeatureGroup.bringToBack();
    }
  }

}

export default MapManager;

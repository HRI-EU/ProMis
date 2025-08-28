import L from "leaflet";
import { DomEvent } from "leaflet";
import "leaflet.heat";
import * as turf from "@turf/turf";

import ColorHelper from "../utils/ColorHelper.js";
import { updateDynamicLayerEntry, deleteDynamicLayerEntry, updateConfigDynamicLayers, randomId } from "../utils/Utility.js";

import { C } from "./Core.js";
import { getDefaultMarker, getDroneIcon, getLandingPadIcon, LayerType } from "../utils/getIcons.js";

import { Voronoi } from "../libs/rhill-voronoi-core.min.js";

//Marker RenderMode "enum"
export class RenderMode {
  static HeatmapRect = "HEATMAP_RECT";
  static HeatmapCircle = "HEATMAP_CIRCLE";
  static Voronoi = "VORONOI";
  static SVGImage = "SVG_IMAGE";
  static PNGImage = "PNG_IMAGE";
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
    this.circleHighlight = null;
    this.dblclickedEntity = null;
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
      std_dev: layer.feature.properties["uncertainty"],
      origin: layer.feature.properties["origin"]
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
      std_dev: layer.feature.properties["uncertainty"],
      origin: layer.feature.properties["origin"]
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
      std_dev: layer.feature.properties["uncertainty"],
      origin: layer.feature.properties["origin"]
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

    layer.on("dblclick", MapManager._ondblClickLayer);

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
    layer.on("dblclick", MapManager._ondblClickLayer);
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
    layer.on("dblclick", MapManager._ondblClickLayer);
    // update the configuration data on the backend
    updateDynamicLayerEntry(C().mapMan.getPolygon(layer));
  }

  static _initLayerProperties(layer, name, shape, locationType = "UNKNOWN", color = "black", id = null, uncertainty = null, origin=LayerType.INTERNAL) {
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
    
    if (uncertainty !== null) {
      layer.feature.properties["uncertainty"] = uncertainty;
    } else {
      const newUncertainty = C().sourceMan.getUncertaintyFromLocationType(locationType);
      layer.feature.properties["uncertainty"] = newUncertainty;
    }
    
    layer.feature.properties["color"] = color;
    layer.feature.properties["origin"] = origin;
  }

  static _ondblClickLayer(event) {
    /*
      synthesize data from layer.
      data structure:
      {
        type: "defaultMarker", "droneMarker", "landingSiteMarker", "Line", "Polygon",
        id: "unique_id", // unique identifier for the entity
        name: "name", // name of the marker
        coordinates: [latitude, longitude], // for markers
        coordinates: [[lat1, lon1], [lat2, lon2]], // for polylines/polygons
        locationType: "type_name", // for markers, polylines, polygons
        uncertainty: 0.0, // for markers, polylines, polygons
        // other properties can be added as needed
      }
    */
    DomEvent.stopPropagation(event);
    const layer = event.sourceTarget;
    C().mapMan.dblclickedEntity = layer;
    const data = MapManager._getInfoBoxDataFromLayer(layer)
    // call the onClickFunction with the data
    C().updateMapComponent(data);
  }

  static _getInfoBoxDataFromLayer(layer) {
    const properties = layer.feature.properties;
    const icon = properties["shape"];
    const id = properties["id"];
    let name = properties["name"];
    if (icon === "Line" || icon === "Polygon") {
      name = icon;
    }
    let coordinates = [];
    if (icon === "defaultMarker" || icon === "droneMarker" || icon === "landingSiteMarker") {
      coordinates = [layer.getLatLng().lat, layer.getLatLng().lng];
    } else if (icon === "Line") {
      coordinates = layer.getLatLngs().map((latlng) => [latlng.lat, latlng.lng]);
    } else if (icon === "Polygon") {
      coordinates = layer.getLatLngs()[0].map((latlng) => [latlng.lat, latlng.lng]);
    }
    
    const locationType = properties["locationType"];
    const uncertainty = properties["uncertainty"];
    const disabled = properties["origin"] === LayerType.EXTERNAL;
    const data = {
      icon,
      id,
      name,
      coordinates,
      locationType,
      uncertainty,
      disabled
    };
    return data;
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
          let svgInner = "";
          if (currentLayer.renderMode === RenderMode.PNGImage) {
            var pngCanvas = document.createElement("canvas");
            pngCanvas.width = currentLayer.width;
            pngCanvas.height = currentLayer.height;
            var pngCtx = pngCanvas.getContext("2d");
          }
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

          const markers = currentLayer.markers.map((marker, markerIndex) => {
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
              currentLayer.opacity * 0.01,
              positive,
            );

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
                    fillOpacity: currentLayer.opacity * 0.01,
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
                    fillOpacity: currentLayer.opacity * 0.01,
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
                      fillOpacity: currentLayer.opacity * 0.01,
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
                  break;
                  case RenderMode.SVGImage:
                    svgInner += `<rect x="${markerIndex % currentLayer.width}" y="${currentLayer.height - 1 - Math.floor(markerIndex / currentLayer.width)}" width="1" height="1" fill="${hsla}" />`;
                    break;
                  case RenderMode.PNGImage:
                    //TODO: implement PNG image rendering
                    pngCtx.fillStyle = hsla;
                    pngCtx.fillRect(
                      markerIndex % currentLayer.width,
                      currentLayer.height - 1 - Math.floor(markerIndex / currentLayer.width),
                      1,
                      1,
                    );
              }
              if (currentLayer.renderMode !== RenderMode.SVGImage && currentLayer.renderMode !== RenderMode.PNGImage) {
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
                feature.properties["fill-opacity"] = currentLayer.opacity * 0.01;
                // add radius property if render mode is circle
                if (currentLayer.renderMode === RenderMode.HeatmapCircle) {
                  feature.properties["radius"] = currentLayer.radius;
                }

                return createdMarker;
              }
            }
          });
          
          if (currentLayer.renderMode === RenderMode.SVGImage) {
            // create a new SVG overlay
            let svgElement = document.createElementNS("http://www.w3.org/2000/svg", "svg");
            svgElement.setAttribute("xmlns", "http://www.w3.org/2000/svg");
            svgElement.setAttribute("viewBox", `0 0 ${currentLayer.width} ${currentLayer.height}`);
            svgElement.setAttribute("width", currentLayer.width);
            svgElement.setAttribute("height", currentLayer.height);
            svgElement.innerHTML = svgInner;
            const dlon = (currentLayer.markers[1].position[1] - currentLayer.markers[0].position[1]) / 2.0;
            const dlat = (currentLayer.markers[currentLayer.width].position[0] - currentLayer.markers[0].position[0]) / 2.0;
            const southWest = L.latLng(
              currentLayer.markers[0].position[0] - dlat,
              currentLayer.markers[0].position[1] - dlon,
            );
            const markerLength = currentLayer.markers.length;
            const northEast = L.latLng(
              currentLayer.markers[markerLength - 1].position[0] + dlat,
              currentLayer.markers[markerLength - 1].position[1] + dlon,
            );
            const bbox = L.latLngBounds(
              southWest,
              northEast,
            );
            let svgO = L.svgOverlay(svgElement, bbox, { interactive: false }).addTo(this.map);
            currentLayer.markerLayer = svgO;
          }
          else if (currentLayer.renderMode === RenderMode.PNGImage) {
            // create a new image overlay
            const imageUrl = pngCanvas.toDataURL("image/png");
            const dlon = (currentLayer.markers[1].position[1] - currentLayer.markers[0].position[1]) / 2.0;
            const dlat = (currentLayer.markers[currentLayer.width].position[0] - currentLayer.markers[0].position[0]) / 2.0;
            const southWest = L.latLng(
              currentLayer.markers[0].position[0] - dlat,
              currentLayer.markers[0].position[1] - dlon,
            );
            const markerLength = currentLayer.markers.length;
            const northEast = L.latLng(
              currentLayer.markers[markerLength - 1].position[0] + dlat,
              currentLayer.markers[markerLength - 1].position[1] + dlon,
            );
            const bbox = L.latLngBounds(
              southWest,
              northEast,
            );
            const imageOverlay = L.imageOverlay(imageUrl, bbox, {
              interactive: false,
            }).addTo(this.map);
            currentLayer.leafletOverlays = pngCanvas;
            currentLayer.markerLayer = imageOverlay;
          }
          else {
            currentLayer.leafletOverlays = markers;
            currentLayer.markerLayer = layerGroup;
          }
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
    // just refresh the layer if it is not a heatmap from leaflet native (render from image)
    if (layer.renderMode === RenderMode.PNGImage || layer.renderMode === RenderMode.SVGImage) {
      this.refreshMap();
      return;
    }


    // calculate the satFactor based on the probability range
    let satFactor = 100 / layer.markersValMinMax[1];
    layer.markers.forEach((marker, index) => {
      // ignore markers outside the value range
      if (
        marker.probability < layer.valueRange[0] - 0.000000001 ||
        marker.probability > layer.valueRange[1] + 0.000000001
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
        fillOpacity: layer.opacity * 0.01,
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
      const markerOrigin = marker.origin;
      const markerLayer = new L.marker(markerPosition, { icon: MapManager.icons[markerShape](markerColor, markerOrigin), 
                                                         pmIgnore: markerOrigin === LayerType.EXTERNAL ? true : false });
      const markerUncertainty = marker.std_dev;
      markerLayer.on("pm:edit", function() {
        // update the configuration data on the backend
        updateDynamicLayerEntry(C().mapMan.getMarker(markerLayer));
        console.log("marker edited");
      });
      MapManager._initLayerProperties(markerLayer, markerName, markerShape, markerLocationType, markerColor, markerId, markerUncertainty, markerOrigin);
      this.dynamicFeatureGroup.addLayer(markerLayer);
      markerLayer.on("dblclick", MapManager._ondblClickLayer);

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

  _filterUnique(entities) { 
    let foundIds = [];
    let toBeDeletedIndex = [];
    for(var i = 0; i < entities.length; i++) {
      const currentId = entities[i].id;
      let found = false;
      for (var j = 0; j < foundIds.length; j++) {
        if (currentId === foundIds[j]) {
          found = true;
          toBeDeletedIndex.push(i);
          break;
        }
      }
      if (!found) {
        foundIds.push(currentId);
      }
    }
    return entities.filter((_, index) => {
      return !toBeDeletedIndex.includes(index);
    })
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
    this.importMarkers(this._filterUnique(dynamicLayers.markers));
    this.importPolylines(this._filterUnique(dynamicLayers.polylines));
    this.importPolygons(this._filterUnique(dynamicLayers.polygons));

  }


  // import all polylines from json config file
  importPolylines(polylines) {
    if (!this.dynamicFeatureGroup) {
      return;
    }
    // add polylines
    polylines.forEach((polyline) => {
      const polylineLayer = new L.polyline(polyline.latlngs, {pmIgnore: polyline.origin === LayerType.EXTERNAL ? true : false});
      polylineLayer.on("pm:edit", function() {
        // update the configuration data on the backend
        updateDynamicLayerEntry(C().mapMan.getPolyline(polylineLayer));
      });
      MapManager._initLayerProperties(polylineLayer, "", "Line", polyline.location_type, polyline.color, polyline.id, polyline.std_dev, polyline.origin);
      if (polyline.color) {
        polylineLayer.setStyle({
          color: polyline.color,
          weight: polyline.origin === LayerType.INTERNAL ? 3 : 5 
        });
      }

      polylineLayer.on("dblclick", MapManager._ondblClickLayer);

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
      const polygonLayer = new L.polygon(polygonLatlngs, {pmIgnore: polygon.origin === LayerType.EXTERNAL ? true : false});
      polygonLayer.on("pm:edit", function() {
        // update the configuration data on the backend
        updateDynamicLayerEntry(C().mapMan.getPolygon(polygonLayer));
      });
      MapManager._initLayerProperties(polygonLayer, "", "Polygon", polygon.location_type, polygon.color, polygon.id, polygon.std_dev, polygon.origin);
      // add color style to the polygon
      if (polygon.color) {
        polygonLayer.setStyle({
          fillColor: polygon.color,
          color: polygon.color,
          weight: polygon.origin === LayerType.INTERNAL ? 3 : 5 
        });
      }

      polygonLayer.on("dblclick", MapManager._ondblClickLayer);

      this.dynamicFeatureGroup.addLayer(polygonLayer);
    });
    //console.log("polygon added!!")
  }

  // initialize the location type click event listeners
  // type: all, marker, polyline, polygon, vertiport
  setLocationTypeOnClick(locationType, color, uncertainty, type="all") {
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
        layer.feature.properties["uncertainty"] = uncertainty;

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

  // update the location type of the markers
  // used by the LocationTypeSetting component when the location type is changed
  updateUncertainty(locationType, uncertainty) {
    if (!this.dynamicFeatureGroup) {
      return;
    }
    this.dynamicFeatureGroup.eachLayer((layer) => {
      // update the location type of the marker if it has the old location type
      if (layer.feature.properties["locationType"] === locationType) {
        layer.feature.properties["uncertainty"] = uncertainty;
        if (layer === this.dblclickedEntity) {
          const data = MapManager._getInfoBoxDataFromLayer(layer);
          C().updateMapComponent(data, 1);
        }
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
    console.log("originLatlng: ", originLatlng);
    const origin = turf.point([originLatlng.lng, originLatlng.lat]);
    // calculate coordinates of the rectangle bounding box based on the origin and the width and height of box
    const north = turf.destination(origin, height / 2000, 0, { units: "kilometers" });
    const east = turf.destination(origin, width / 2000, 90, { units: "kilometers" });
    const south = turf.destination(origin, height / 2000, 180, { units: "kilometers" });
    const west = turf.destination(origin, width / 2000, -90, { units: "kilometers" });
    const bbox = turf.bbox(turf.featureCollection([origin, north, east, south, west]));
    return L.latLngBounds([bbox[1], bbox[0]], [bbox[3], bbox[2]]);
  }

  highlightBoundaryAlter(origin,
    dimensions, 
    resolutions, 
    supportResolutions
  ) {
     // do nothing if origin is not selected or any of the dimension or resolution is not set
     if (origin === "") {
      return;
    }

    // remove the old bounding box layer
    this.unhighlightBoundaryAlter();

    const dimensionWidth = dimensions[0];
    const dimensionHeight = dimensions[1];
    const resolutionWidth = resolutions[0];
    const resolutionHeight = resolutions[1];
    const supportResolutionWidth = supportResolutions[0];
    const supportResolutionHeight = supportResolutions[1];

    // do nothing if any of the dimensions or resolutions is not a number or less than or equal to zero
    if (
      isNaN(dimensionWidth) || dimensionWidth <= 0 ||
      isNaN(dimensionHeight) || dimensionHeight <= 0 ||
      isNaN(resolutionWidth) || resolutionWidth <= 0 ||
      isNaN(resolutionHeight) || resolutionHeight <= 0 ||
      isNaN(supportResolutionWidth) || supportResolutionWidth <= 0 ||
      isNaN(supportResolutionHeight) || supportResolutionHeight <= 0
    ) {
      return;
    }

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

  setMapCircleHighlight(coordinate) {
    this.removeCircleHighlight();
    if (this.map !== null)
      this.circleHighlight = L.circleMarker(coordinate, {radius: 2, color:"red"}).addTo(this.map);
  }

  removeCircleHighlight(){
    if (this.circleHighlight !== null) {
      this.map.removeLayer(this.circleHighlight);
    }
  }

  uncertaintyChange(uncertainty){
    if (this.dblclickedEntity !== null){
      const oldUncertainty = this.dblclickedEntity.feature.properties.uncertainty;
      if (oldUncertainty !== uncertainty){
        this.dblclickedEntity.feature.properties.uncertainty = uncertainty;
        updateDynamicLayerEntry(this.getDynamicLayer(this.dblclickedEntity));
      }
    }
  }

  locationTypeChange(locationType){
    if (this.dblclickedEntity !== null) {
      const oldLocationType = this.dblclickedEntity.feature.properties.locationType;
      if (oldLocationType !== locationType){
        this.dblclickedEntity.feature.properties.locationType = locationType;

        // update color
        const color = C().sourceMan.getColorFromLocationType(locationType);
        this.dblclickedEntity.feature.properties.color = color;
        // update the color of the layer for line and polygon
        if (this.dblclickedEntity.feature.properties["shape"] === "Line" || this.dblclickedEntity.feature.properties["shape"] === "Polygon") {
          this.dblclickedEntity.setStyle({
            fillColor: color,
            color: color,
          });
        }
        else {
          // update the icon of the markers
          let markerShape = this.dblclickedEntity.feature.properties["shape"];
          this.dblclickedEntity.setIcon(MapManager.icons[markerShape](color));
        }


        updateDynamicLayerEntry(this.getDynamicLayer(this.dblclickedEntity));
      }
    }
  }

}

export default MapManager;

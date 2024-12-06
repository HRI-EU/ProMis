import L from "leaflet";
import "leaflet.heat";

import ColorHelper from "../utils/ColorHelper.js";
import { updateConfig, updateConfigPolygons, updateConfigPolylines, updateConfigDynamicLayers } from "../utils/Utility.js";

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
    this._isinitMarker = false;
    this._isinitLine = false;
    this._isinitPolygon = false;
    this._onClickFunction = new Map();
  }

  // get markers from map
  getMarkers() {
    // marker of type {name: string, latlng: [lat, lon], shape: string}
    let markers = [];
    if (!this.dynamicFeatureGroup) {
      return markers;
    } 
    this.dynamicFeatureGroup.eachLayer((layer) => {
      if (layer.options.pane == "markerPane") {
        markers.push({
          name: layer.feature.properties["name"],
          latlng: [layer.getLatLng().lat, layer.getLatLng().lng],
          shape: layer.feature.properties["shape"],
          location_type: layer.feature.properties["locationType"],
          color: layer.feature.properties["color"],
        });
      }
    });
    return markers;
  }

  getPolylines() {
    let polylines = [];
    if (!this.dynamicFeatureGroup) {
      return polylines;
    }
    this.dynamicFeatureGroup.eachLayer((layer) => {
      if (layer.feature.properties["shape"] === "Line") {
        polylines.push({
          latlngs: layer.getLatLngs().map((latlng) => [latlng.lat, latlng.lng]),
          location_type: layer.feature.properties["locationType"],
          color: layer.feature.properties["color"],
        });
      }
    });
    return polylines;
  }

  getPolygons() {
    let polygons = [];
    if (!this.dynamicFeatureGroup) {
      return polygons;
    }
    this.dynamicFeatureGroup.eachLayer((layer) => {
      if (layer.feature.properties["shape"] === "Polygon") {
        polygons.push({
          latlngs: layer.getLatLngs()[0].map((latlng) => [latlng.lat, latlng.lng]),
          location_type: layer.feature.properties["locationType"],
          color: layer.feature.properties["color"],
        });
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
    this.moveTo([49.8728, 8.6512]);
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
      if (layer.options.pane == "markerPane") {
        MapManager._onCreatedMarker(shape, layer);
      }
      else if (shape == "Line"){
        MapManager._onCreatedLine(shape, layer);
        
      } else if (shape == "Polygon") {  
        MapManager._onCreatedPolygon(shape, layer);
      }
    });
    this.map.on("pm:remove", function ({ shape, layer }) {
      if (layer.options.pane == "markerPane") {
        // update origin from source when the removed drone marker is the origin
        if (layer.feature.properties["name"] === C().sourceMan.origin) {
          // find the first marker and set it as the new origin
          const markers = C().mapMan.listMarkers();
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
        updateConfig(C().layerMan.layers, C().mapMan.getMarkers());
      }
      else if (shape == "Line"){
        updateConfigPolylines(C().mapMan.getPolylines());
      } else if (shape == "Polygon") {  
        updateConfigPolygons(C().mapMan.getPolygons());
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
    MapManager._initLayerProperties(layer, markerName, shape);
    // listen to the edit event to update the configuration data on the backend
    layer.on("pm:edit", function () {
      updateConfig(C().layerMan.layers, C().mapMan.getMarkers());
      //console.log(C().mapMan.getMarkers());
      console.log("marker edited now");
    });

    // update bottombar
    C().updateBottomBar();

    // update the configuration data on the backend
    updateConfig(C().layerMan.layers, C().mapMan.getMarkers());
  }

  static _onCreatedLine(shape, layer) {
    // add properties
    MapManager._initLayerProperties(layer, "", shape);
    // listen to the edit event to update the configuration data on the backend
    layer.on("pm:edit", function () {
      console.log("line edited")
      updateConfigPolylines(C().mapMan.getPolylines());
    });
    layer.setStyle({ color: "#000000" });
    // update the configuration data on the backend
    updateConfigPolylines(C().mapMan.getPolylines());
  }

  static _onCreatedPolygon(shape, layer) {
    // add properties
    MapManager._initLayerProperties(layer, "", shape);
    // listen to the edit event to update the configuration data on the backend
    layer.on("pm:edit", function () {
      updateConfigPolygons(C().mapMan.getPolygons());
    });
    layer.setStyle({ color: "#000000" });
    // update the configuration data on the backend
    updateConfigPolygons(C().mapMan.getPolygons());
  }

  static _initLayerProperties(layer, name, shape, locationType = "", color = "#000000") {
    layer.feature = layer.feature || {};
    layer.feature.type = "Feature";
    layer.feature.properties = layer.feature.properties || {};
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
      .map((currentLayer, layerIndex) => {
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

  listMarkers() {
    let markers = [];
    if (!this.dynamicFeatureGroup) {
      return markers;
    }
    return this.dynamicFeatureGroup.getLayers().filter((layer) => layer.options.pane == "markerPane");
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
    if (this._isinitMarker) {
      return;
    }
    // add markers
    markers.forEach((marker) => {
      const markerName = marker.name;
      const markerPosition = marker.latlng;
      const markerShape = marker.shape;
      const markerColor = marker.color;
      const markerLocationType = marker.location_type;
      const markerLayer = new L.marker(markerPosition, { icon: MapManager.icons[markerShape](markerColor) });
      markerLayer.on("pm:edit", function() {
        // update the configuration data on the backend
        updateConfig(C().layerMan.layers, C().mapMan.getMarkers());
        console.log("marker edited");
      });
      MapManager._initLayerProperties(markerLayer, markerName, markerShape, markerLocationType, markerColor);
      this.dynamicFeatureGroup.addLayer(markerLayer);

      // update number of markers to avoid name conflicts
      this.nameNumber = Math.max(this.nameNumber, parseInt(markerName.split(" ")[1]) + 1);
    });
    this._isinitMarker = true;
  }

  // import all polylines from json config file
  importPolylines(polylines) {
    if (!this.dynamicFeatureGroup) {
      return;
    }
    if (this._isinitLine) {
      return;
    }
    // add polylines
    polylines.forEach((polyline) => {
      const polylineLayer = new L.polyline(polyline.latlngs);
      polylineLayer.on("pm:edit", function() {
        // update the configuration data on the backend
        updateConfigPolylines(C().mapMan.getPolylines());
      });
      MapManager._initLayerProperties(polylineLayer, "", "Line", polyline.location_type, polyline.color);
      // add color style to the line
      if (polyline.color) {
        polylineLayer.setStyle({
          color: polyline.color,
        });
      }

      this.dynamicFeatureGroup.addLayer(polylineLayer);
    });
    this._isinitLine = true;
  }

  // import all polygons from json config file
  importPolygons(polygons) {
    if (!this.dynamicFeatureGroup) {
      return;
    }
    if (this._isinitPolygon) {
      return;
    }
    // add polygons
    polygons.forEach((polygon) => {
      const polygonLayer = new L.polygon(polygon.latlngs);
      polygonLayer.on("pm:edit", function() {
        // update the configuration data on the backend
        updateConfigPolygons(C().mapMan.getPolygons());
      });
      MapManager._initLayerProperties(polygonLayer, "", "Polygon", polygon.location_type, polygon.color);
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
    this._isinitPolygon = true;
  }

  // initialize the location type click event listeners
  setLocationTypeOnClick(locationType, color) {
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
        updateConfigDynamicLayers(C().mapMan.getMarkers(), C().mapMan.getPolylines(), C().mapMan.getPolygons());
      };
      layer.on("click", onClickFunc);
      this._onClickFunction.set(layer, onClickFunc);
    });
  }

  // remove the location type click event listeners
  removeLocationTypeOnClick() {
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

}

export default MapManager;

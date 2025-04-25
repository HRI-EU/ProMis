import Layer from "../models/Layer.js";
import { C } from "./Core.js";
import { RenderMode } from "./MapManager.js";
import { updateTotalConfig, updateLayerConfig, deleteLayerConfig, randomId } from "../utils/Utility.js";

class LayerManager {
  constructor() {
    this.layers = [];
    this.hideAllLayers = false;
  }

  //Toggle all layers visibility
  toggleAllLayers() {
    this.hideAllLayers = !this.hideAllLayers;
    this.layers.forEach((layer) => {
      layer.visible = !this.hideAllLayers;
    });
    C().updateSidebarRight();
    C().mapMan.refreshMap();
  }

  //Import all layers from json file
  importAllLayers(layers) {
    for (let i = 0; i < layers.length; i++) {
      if (layers[i].renderMode === undefined)
        layers[i].renderMode = RenderMode.Voronoi;
      layers[i].markerLayer = null;
      layers[i].leafletOverlays = [];
      layers[i].settingsMenuExpanded = false;
      layers[i].colorMenuExpanded = false;
    }
    this.layers = layers;
    // check if all layers are hidden
    this.hideAllLayers = this.layers.every((layer) => !layer.visible);
    C().updateSidebarRight();
    C().mapMan.refreshMap();
  }

  /**
   *
   * @param {number[][3]} data data from the csv file
   * @param {*} fileInfo file information to get name
   */
  importLayer(data, fileInfo) {
    const uniqueId = randomId();
    const layer = Layer.parseLayer(uniqueId, data, 180.0, fileInfo.name, 5);
    this.layers.push(layer);
    this.hideAllLayers = false;
    C().updateSidebarRight();
    C().mapMan.refreshMap();
    updateLayerConfig(layer);
  }

  importLayerFromSourceCode(data, fileInfo) {
    const uniqueId = randomId();
    const layer = Layer.parseLayer(uniqueId, data, 180.0, fileInfo.name, 5, true);
    this.layers.splice(0, 0, layer);
    this.hideAllLayers = false;
    C().updateSidebarRight();
    C().mapMan.refreshMap();
    updateTotalConfig(this.layers);
  }

  /**
   * Delete all previously added layers from the map and from the SidebarLeft
   */
  deleteAllLayers() {
    this.layers = [];
    C().updateSidebarRight();
    C().mapMan.refreshMap();
    updateTotalConfig(this.layers);
  }

  //Delete layer with this layerId
  deleteLayer(layerId) {
    C().mapMan.removeMarkers();
    var pos = LayerManager.findLayerPos(this.layers, layerId);
    this.layers = this.layers.filter((layer) => layer.id !== layerId);
    // check if all layers are hidden
    this.hideAllLayers = this.layers.every((layer) => !layer.visible);
    C().updateSidebarRight();
    C().mapMan.refreshMap();
    deleteLayerConfig(pos);
  }

  //Change layer name
  toggleEditName(layerId, layerName) {
    var pos = LayerManager.findLayerPos(this.layers, layerId);
    this.layers[pos].editName = !this.layers[pos].editName;
    this.layers[pos].name = layerName;
    C().updateSidebarRight();
    updateLayerConfig(this.layers[pos]);
  }

  //Toggle layer visibility
  changeLayerVisibility(layerId, visible) {
    if (visible) {
      this.hideAllLayers = false;
    }
    if (!visible && this.layers.every((layer) => (layer.id === layerId) || !layer.visible)) {
      this.hideAllLayers = true;
    }
    var pos = LayerManager.findLayerPos(this.layers, layerId);
    this.layers[pos].visible = visible;
    C().updateSidebarRight();
    C().mapMan.refreshMap();
    updateLayerConfig(this.layers[pos]);
  }

  //Toggle settings menu
  changeLayerSettingsExpanded(layerId, expanded) {
    var pos = LayerManager.findLayerPos(this.layers, layerId);
    if (expanded) {
      this.layers[pos].colorMenuExpanded = false;
    }
    this.layers[pos].settingsMenuExpanded = expanded;
    C().updateSidebarRight();
  }

  //Toggle color menu
  changeLayerColorsExpanded(layerId, expanded) {
    var pos = LayerManager.findLayerPos(this.layers, layerId);
    if (expanded) {
      this.layers[pos].settingsMenuExpanded = false;
    }
    this.layers[pos].colorMenuExpanded = expanded;
    C().updateSidebarRight();
  }

  //Change layer color
  changeLayerColor(layerId, hue) {
    var pos = LayerManager.findLayerPos(this.layers, layerId);
    this.layers[pos].hue = hue;
    C().updateSidebarRight();
    if (this.layers[pos].visible){
      C().mapMan.updateLayerColor(this.layers[pos]);
    }
  }

  //Change layer opacity
  changeLayerOpacity(layerId, opacity) {
    var pos = LayerManager.findLayerPos(this.layers, layerId);
    this.layers[pos].opacity = opacity;
    C().updateSidebarRight();
    C().mapMan.refreshMap();
    updateLayerConfig(this.layers[pos]);
  }

  //Change layer render mode
  changeLayerRenderMode(layerId, renderMode) {
    var pos = LayerManager.findLayerPos(this.layers, layerId);
    this.layers[pos].renderMode = renderMode;
    C().updateSidebarRight();
    C().mapMan.refreshMap();
    updateLayerConfig(this.layers[pos]);
  }

  //Change layer radius
  changeLayerRadius(layerId, radius) {
    var pos = LayerManager.findLayerPos(this.layers, layerId);
    this.layers[pos].radius = radius;
    var markerDst = Layer.calcMarkerDst(this.layers[pos].markers, radius);
    this.layers[pos].markerDstLat = markerDst[0];
    this.layers[pos].markerDstLng = markerDst[1];
    C().updateSidebarRight();
    C().mapMan.refreshMap();
    updateLayerConfig(this.layers[pos]);
  }

  //Change layer value range
  changeLayerValueRange(layerId, valueRange) {
    var pos = LayerManager.findLayerPos(this.layers, layerId);
    this.layers[pos].valueRange = valueRange;
    C().updateSidebarRight();
    C().mapMan.refreshMap();
    updateLayerConfig(this.layers[pos]);
  }

  //If within bounds, switch layer with previous in array (moves layer in sidebar upwards)
  moveLayerUp(layerId) {
    var pos = LayerManager.findLayerPos(this.layers, layerId);
    if (pos > 0) {
      console.log("up before ", this.layers);

      // remove `from` item and store it
      var f = this.layers.splice(pos, 1)[0];
      // insert stored item into position `to`
      this.layers.splice(pos - 1, 0, f);

      console.log("up after ", this.layers);

      //var lay = this.layers[pos];
      //this.layers[pos] = this.layers[pos-1];
      //this.layers[pos-1] = lay;
      C().updateSidebarRight();
      C().mapMan.refreshMap();
      updateTotalConfig(this.layers);
    }
  }

  //If within bounds, switch layer with next in array (moves layer in sidebar downwards)
  moveLayerDown(layerId) {
    var pos = LayerManager.findLayerPos(this.layers, layerId);
    if (pos < this.layers.length) {
      console.log("down before ", this.layers);

      // remove `from` item and store it
      var f = this.layers.splice(pos, 1)[0];
      // insert stored item into position `to`
      this.layers.splice(pos + 1, 0, f);

      console.log("down after ", this.layers);

      //var lay = this.layers[pos];
      //this.layers[pos] = this.layers[pos+1];
      //this.layers[pos+1] = lay;
      C().updateSidebarRight();
      C().mapMan.refreshMap();
      updateTotalConfig(this.layers);
    }
  }

  //Moves map to center pos [lat, lng] of given layer
  moveToLayerCenter(layerId) {
    var pos = LayerManager.findLayerPos(this.layers, layerId);
    var centerLatLng = Layer.calcCenterLatLng(
      this.layers[pos].markersLatMinMax,
      this.layers[pos].markersLngMinMax,
    );
    C().mapMan.moveTo(centerLatLng);
    //console.log("centerLatLng is ", centerLatLng );
  }

  /**
   * Get layer by id
   * @param {number} layerId
   * @returns {Layer | undefined} Layer object or undefined if not found
   */
  getLayerById(layerId) {
    return LayerManager.findLayer(this.layers, layerId);
  }

  /**
   * Export layer to GeoJSON
   * @param {number} layerId
   * @returns {object} GeoJSON object
   */
  exportGeoJSON(layerId) {
    return LayerManager.findLayer(this.layers, layerId).markerLayer.toGeoJSON();
  }

  /**
   * Export all layers to GeoJSON including markers
   * @returns {object} GeoJSON object
   */
  exportAllGeoJSON() {
    const dynamicFeatureGroup = C().mapMan.dynamicFeatureGroup;
    if (
      this.layers.length === 0 &&
      dynamicFeatureGroup.getLayers().length === 0
    ) {
      return null;
    }
    var geoJSON = {
      type: "FeatureCollection",
      features: [],
    };
    this.layers.forEach((layer) => {
      // ignore hided layers
      if (layer.markerLayer === null) {
        return;
      }
      geoJSON.features.push(...layer.markerLayer.toGeoJSON().features);
    });
    geoJSON.features.push(...dynamicFeatureGroup.toGeoJSON().features);
    return geoJSON;
  }

  //Takes layers array and layerId, returns layer or undefined
  static findLayer(layers, layerId) {
    return layers[this.findLayerPos(layers, layerId)];
  }

  //Takes layers array and layerId, returns layer pos in array or -1 if not found
  static findLayerPos(layers, layerId) {
    return layers.findIndex((layer) => layer.id === layerId);
  }
}

export default LayerManager;

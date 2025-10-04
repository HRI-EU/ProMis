import L from "leaflet";

import ColorHelper from "../utils/ColorHelper.js";
import { RenderMode } from "../managers/MapManager";

import { Voronoi } from "../libs/rhill-voronoi-core.min.js";

class BaseRender {

    layerGroup = new L.LayerGroup();

    constructor() {
        if (this.constructor == BaseRender) {
            throw new Error("Base Render can't be instantiated");
        }
    }

    // eslint-disable-next-line no-unused-vars
    render(currentLayer) {
        throw new Error("Method render() is not implemented!");
    }

    satFactor(currentLayer) {
        const satFactor = 100 / currentLayer.markersValMinMax[1];
        return satFactor;
    }
}

class LeafletNativeRender extends BaseRender{

    constructor() {
        super();
        if (this.constructor == LeafletNativeRender) {
            throw new Error("LeafletNativeRender can't be instantiated");
        }
    }

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

    commonEnd(satFactor, currentLayer, createdMarker, marker) {
        this.layerGroup.addLayer(createdMarker);
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

export class HeatmapRectRender extends LeafletNativeRender {
    constructor(map, layerGroup) {
        super();
        this.map = map;
        this.layerGroup = layerGroup;
    }

    calcRectBounds(marker, markerDstLat, markerDstLng) {
        return new L.latLngBounds(
            [marker.position[0] - markerDstLat, marker.position[1] - markerDstLng],
            [marker.position[0] + markerDstLat, marker.position[1] + markerDstLng],
        );
    }

    render(currentLayer) {
        const satFactor = this.satFactor(currentLayer);
        const markers = currentLayer.markers.map((marker) => {
            const positive = marker.probability >= 0;
            let sat = Math.abs(Math.round(marker.probability * satFactor));
            var hsl = ColorHelper.calcHslFromParams(
                currentLayer.hue,
                sat,
                positive,
            );
            if (
              marker.probability >= currentLayer.valueRange[0] - 0.000000001 &&
              marker.probability <= currentLayer.valueRange[1] + 0.000000001
            ) {
                var createdMarker = null;
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
                return this.commonEnd(satFactor, currentLayer, createdMarker, marker);
            }
        });
        currentLayer.leafletOverlays = markers;
        currentLayer.markerLayer = this.layerGroup;
    }
}

export class HeatmapCircleRender extends LeafletNativeRender {
    constructor(map, layerGroup) {
        super();
        this.map = map;
        this.layerGroup = layerGroup;
    }

    render(currentLayer) {
        const satFactor = this.satFactor(currentLayer);
        const markers = currentLayer.markers.map((marker) => {
            const positive = marker.probability >= 0;
            let sat = Math.abs(Math.round(marker.probability * satFactor));
            var hsl = ColorHelper.calcHslFromParams(
                currentLayer.hue,
                sat,
                positive,
            );
            if (
              marker.probability >= currentLayer.valueRange[0] - 0.000000001 &&
              marker.probability <= currentLayer.valueRange[1] + 0.000000001
            ) {
                var createdMarker = null;
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
                return this.commonEnd(satFactor, currentLayer, createdMarker, marker);
            }
        });
        currentLayer.leafletOverlays = markers;
        currentLayer.markerLayer = this.layerGroup;
    }
}

export class VoronoiRender extends LeafletNativeRender {
    constructor(map, layerGroup) {
        super();
        this.map = map;
        this.layerGroup = layerGroup;
    }

    renderLayerToVoronoi(layer) {
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
    }
    

    render(currentLayer) {
        const satFactor = this.satFactor(currentLayer);
        let voronoiPolygonDict = this.renderLayerToVoronoi(currentLayer);
        const markers = currentLayer.markers.map((marker) => {
            const positive = marker.probability >= 0;
            let sat = Math.abs(Math.round(marker.probability * satFactor));
            var hsl = ColorHelper.calcHslFromParams(
                currentLayer.hue,
                sat,
                positive,
            );
            if (
              marker.probability >= currentLayer.valueRange[0] - 0.000000001 &&
              marker.probability <= currentLayer.valueRange[1] + 0.000000001
            ) {
                var createdMarker = null;
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
                return this.commonEnd(satFactor, currentLayer, createdMarker, marker);
            }
        });
        currentLayer.leafletOverlays = markers;
        currentLayer.markerLayer = this.layerGroup;
    }
}

export class SVGImageRender extends BaseRender {
    constructor(map, layerGroup) {
        super();
        this.map = map;
        this.layerGroup = layerGroup;
    }

    render(currentLayer) {
        const satFactor = this.satFactor(currentLayer);
        let svgInner = "";
        currentLayer.markers.forEach((marker, markerIndex) => {
            const positive = marker.probability >= 0;
            let sat = Math.abs(Math.round(marker.probability * satFactor));
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
                svgInner += `<rect x="${markerIndex % currentLayer.width}" y="${currentLayer.height - 1 - Math.floor(markerIndex / currentLayer.width)}" width="1" height="1" fill="${hsla}" />`;
            }
        });
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
}


export class PNGImageRender extends BaseRender {
    constructor(map, layerGroup) {
        super();
        this.map = map;
        this.layerGroup = layerGroup;
    }

    render(currentLayer) {
        var pngCanvas = document.createElement("canvas");
        pngCanvas.width = currentLayer.width;
        pngCanvas.height = currentLayer.height;
        var pngCtx = pngCanvas.getContext("2d");
        const satFactor = this.satFactor(currentLayer);
        currentLayer.markers.forEach((marker, markerIndex) => {
            const positive = marker.probability >= 0;
            let sat = Math.abs(Math.round(marker.probability * satFactor));
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
                pngCtx.fillStyle = hsla;
                pngCtx.fillRect(
                    markerIndex % currentLayer.width,
                    currentLayer.height - 1 - Math.floor(markerIndex / currentLayer.width),
                    1,
                    1,
                );
            }
        });
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
}

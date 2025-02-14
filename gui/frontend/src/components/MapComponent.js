// MapComponent.js
import React, { useEffect } from "react";
import L from "leaflet";
import "leaflet.heat";
import "../libs/leaflet-openweathermap.js";
import "../libs/leaflet-openweathermap.css";
import "leaflet/dist/leaflet.css";
import "@geoman-io/leaflet-geoman-free";
import "@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css";
import { Container } from "react-bootstrap";

import { C } from "../managers/Core.js";
import "./MapComponent.css";
import { getConfig } from "../utils/Utility.js";

//UI
import SidebarRight from "./SidebarRight.js";
import SidebarLeft from "./SidebarLeft.js";
import BottomBar from "./BottomBar.js";
import DynamicLayerInteractive from "./DynamicLayerInteractive.js";

//import WeatherInfoBox from "./WeatherInfoBox.js";

function MapComponent() {
  var map = null;

  const defaultCenter = [49.8728, 8.6512];

  let didInit = false;

  useEffect(() => {
    if (didInit)
      return;

    map = L.map("map", {
      preferCanvas: true,
      center: defaultCenter,
      zoom: 13,
      zoomSnap: 0.2,
      maxZoom: 20,
    });
    

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxNativeZoom: 19,
      maxZoom: 20,
    }).addTo(map);

    MapHook();

    // hide zoom control
    const zoomControl = document.querySelector(".leaflet-control-zoom");
    if (zoomControl) {
      zoomControl.style.visibility = "hidden";
    }

    didInit = true;
  }, []); // Empty dependency array ensures the effect runs once after the initial render

  //This function is called within a MapContainer. It will pass the map reference to the MapManager
  function MapHook() {

    C().mapMan.setMap(map);
    // Load the configuration data from the backend
    getConfig().then((configs) => {
      if (configs === null) {
        return null;
      }
      const config = configs[0];
      if (config !== null) {
        const layers = config.layers;
        const markers = config.markers;
        C().layerMan.importAllLayers(layers);
        C().mapMan.importMarkers(markers);
        if (config.polylines !== undefined) {
          const polylines = config.polylines;
          C().mapMan.importPolylines(polylines);
        }
        if (config.polygons !== undefined) {
          const polygons = config.polygons;
          C().mapMan.importPolygons(polygons);
        }
      }
      const location_type_table = configs[1];
      if (location_type_table !== null) {
        if (location_type_table.table === undefined || location_type_table.table.length === 0) {
          return null;
        }
        // iterate over locationTypes and change location_type field to locationType
        location_type_table.table.forEach((locationType) => {
          locationType.locationType = locationType.location_type;
          delete locationType.location_type;
        });

        C().sourceMan.locationTypes = location_type_table.table;
      }
    });
    
    return null;
  }

  return (
    <Container
      fluid
      className="map-container"
      style={{ margin: 0, padding: 0 }}
    >
      <SidebarLeft />

      <BottomBar />

      <div
        id="map"
        style={{ height: "100vh", width: "100%" }}
      >
      </div>

      <SidebarRight />
      {/* <WeatherInfoBox /> */}
      
      <DynamicLayerInteractive />

    </Container>
  );
}

export default MapComponent;

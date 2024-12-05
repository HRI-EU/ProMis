// MapComponent.js
import React, { useEffect, useRef } from "react";
import { MapContainer, TileLayer } from "react-leaflet";
import { useMap } from "react-leaflet";
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

//import WeatherInfoBox from "./WeatherInfoBox.js";

function MapComponent() {
  const mapRef = useRef();

  const defaultCenter = [49.8728, 8.6512];

  let onlyOnce = false;

  useEffect(() => {
    // Hide Leaflet map zoom control buttons after the map is rendered
    const hideZoomControl = () => {
      const zoomControl = document.querySelector(".leaflet-control-zoom");
      if (zoomControl) {
        zoomControl.style.visibility = "hidden";
      }
    };

    hideZoomControl();

    // Clean up the effect when the component is unmounted
    return () => {
      const zoomControl = document.querySelector(".leaflet-control-zoom");
      if (zoomControl) {
        zoomControl.style.visibility = "visible";
      }
    };
  }, []); // Empty dependency array ensures the effect runs once after the initial render

  //This function is called within a MapContainer. It will pass the map reference to the MapManager
  function MapHook() {
    if (onlyOnce) {
      return null;
    }
    const map = useMap();
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
    onlyOnce = true;
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

      <MapContainer
        preferCanvas={true}
        style={{ height: "100vh", width: "100%" }}
        ref={mapRef}
        center={defaultCenter}
        zoom={13}
        zoomSnap={0.2}
        maxZoom={20}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          maxNativeZoom='19'
          maxZoom={20}
        />
        <MapHook />
      </MapContainer>

      <SidebarRight />
      {/* <WeatherInfoBox /> */}
    </Container>
  );
}

export default MapComponent;

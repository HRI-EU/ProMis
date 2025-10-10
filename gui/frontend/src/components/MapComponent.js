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
import { establishWebsocket } from "../utils/Utility.js";

//UI
import SidebarRight from "./SidebarRight.js";
import SidebarLeft from "./SidebarLeft.js";
import BottomBar from "./bottombar/BottomBar.js";
import DynamicLayerInteractive from "./DynamicLayerInteractive.js";

//import WeatherInfoBox from "./WeatherInfoBox.js";

function MapComponent() {
  var map = null;

  const defaultCenter = [49.877, 8.653];


  /*
    represent a dynamic layer entity info
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
  const [infoBoxState, setInfoBoxState] = React.useState({
    id: "0",
    icon: "defaultMarker",
    name: "Marker 0",
    coordinates: [0, 0],
    locationType: "UNKNOWN",
    uncertainty: 10,
    toggle: false,
    hidden: true,
    disabled: false
  });

  let didInit = false;

  useEffect(() => {
    if (didInit)
      return;

    map = L.map("map", {
      preferCanvas: true,
      center: defaultCenter,
      zoom: 15,
      zoomSnap: 0.2,
      maxZoom: 20,
    });
    

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxNativeZoom: 19,
      maxZoom: 20,
    }).addTo(map);

    MapHook();

    C().addMapComponentCallback(changeState);

    // add interval to check for external updates
    webSocketConnect();

    // hide zoom control
    const zoomControl = document.querySelector(".leaflet-control-zoom");
    if (zoomControl) {
      zoomControl.style.visibility = "hidden";
    }

    didInit = true;
  }, []); // Empty dependency array ensures the effect runs once after the initial render


  // This function is called by the MapManager to trigger a state change of info box
  // Ensure toggle is toggled (when type = 0), type is set when we want to change display entity without forcing info box to appear
  // and hidden is set to false (to ensure info box alway appear especially when close info box and choosing the same entity)
  function changeState(entity, type=0) {
    if (type!==0) {
      setInfoBoxState((prevEntity) => {
        return {...entity, 
          toggle: prevEntity.toggle,
          hidden: false
        }
      });
    } else {
      setInfoBoxState((prevEntity) => {
        return {...entity, 
          toggle: !prevEntity.toggle,
          hidden: false
        }
      });
    }
  }


  //This function is called within a MapContainer. It will pass the map reference to the MapManager
  function MapHook() {

    C().mapMan.setMap(map);
    // Load the configuration data from the backend
    getConfig().then((configs) => {
      if (configs === null) {
        return null;
      }
      const layer_config = configs[0];
      const dynamic_layer = configs[1];
      const location_type_table = configs[2];
      if (layer_config !== null) {
        // change field name of layer_config from snake_case to camelCase
        // iterate over layer_config and change field name from snake_case to camelCase
        for (const layer of layer_config) {
          for (var prop in layer) {
            if (Object.prototype.hasOwnProperty.call(layer, prop)) {
              // check if the property name is in snake_case
              if (prop.includes("_")) {
                // change the property name to camelCase
                const newProp = prop.replace(/_([a-z])/g, (g) => g[1].toUpperCase());
                layer[newProp] = layer[prop];
                delete layer[prop];
              }
            }
          }
        }
        

        C().layerMan.importAllLayers(layer_config);
      }
      if (location_type_table !== null) {
        if (location_type_table === undefined || location_type_table.length === 0) {
          return null;
        }
        // iterate over locationTypes and change location_type field to locationType
        location_type_table.forEach((locationType) => {
          locationType.locationType = locationType.location_type;
          locationType.uncertainty = locationType.std_dev;
          delete locationType.location_type;
          delete locationType.std_dev;
        });

        C().sourceMan.locationTypes = location_type_table;
        C().autoComplete.flush();
        C().autoComplete.push_list(location_type_table.map((loc_type) => loc_type.locationType));
      }
      if (dynamic_layer !== null) {
        const markers = dynamic_layer.markers;
        const polylines = dynamic_layer.polylines;
        const polygons = dynamic_layer.polygons;
        C().mapMan.importMarkers(markers);
        C().mapMan.importPolylines(polylines);
        C().mapMan.importPolygons(polygons);
      }
    });
    
    return null;
  }

  function webSocketConnect() {
    const websocket = establishWebsocket()
    websocket.addEventListener("message", (e) => {
      if (e.data == "ping") {
        return;
      }
      const flterMessage = JSON.parse(e.data);
      const message = JSON.parse(flterMessage);
      if (message.filter !== undefined) {
        // handle location type tab
        const location_type_entry = message
        // iterate over locationTypes and change location_type field to locationType
        location_type_entry.locationType = location_type_entry.location_type;
        delete location_type_entry.location_type;
        C().sourceMan.locationTypes.push(location_type_entry)
      }
      else {
        // handle entity change
        C().mapMan.importExternalEntity(message);
      }
    })
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
      
      <DynamicLayerInteractive 
        {...infoBoxState}
      />

    </Container>
  );
}

export default MapComponent;

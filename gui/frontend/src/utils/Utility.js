/**
 * Calculate the distance between two points on the earth in meters
 * @param {*} lat1 The latitude of the first point
 * @param {*} lon1 The longitude of the first point
 * @param {*} lat2 The latitude of the second point
 * @param {*} lon2 The longitude of the second point
 * @returns The distance between the two points in meters
 * @description The function uses the Haversine formula
 * The formula is taken from https://www.movable-type.co.uk/scripts/latlong.html
 */
export function haversineDistance(lat1, lon1, lat2, lon2) {
  // Radius of the Earth in kilometers
  const R = 6371;

  // Convert latitude and longitude from degrees to radians
  const lat1Rad = toRadians(lat1);
  const lon1Rad = toRadians(lon1);
  const lat2Rad = toRadians(lat2);
  const lon2Rad = toRadians(lon2);

  // Differences in coordinates
  const dLat = lat2Rad - lat1Rad;
  const dLon = lon2Rad - lon1Rad;

  // Haversine formula
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1Rad) * Math.cos(lat2Rad) * Math.sin(dLon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  // Distance in kilometers
  const distance = R * c;
  return distance * 1000;
}

/**
 * Convert degrees to radians
 * @param {*} degrees
 * @returns The value in radians
 * @description The function is taken from https://www.movable-type.co.uk/scripts/latlong.html
 * The function is used in the haversineDistance function
 */
export function toRadians(degrees) {
  return degrees * (Math.PI / 180);
}

export function findMaxProb(markers) {
  return Math.max(...markers.map((marker) => marker.probability));
}

export function randomId() {
  var array = new Uint32Array(1);
  window.crypto.getRandomValues(array);
  return array[0];
}

// function to get configuration json data from backend
export async function getConfig() {
  const url = "http://localhost:8000/app_config";
  // fetch configuration data from backend, convert to json, handle errors
  let config = null;
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error("Failed to fetch configuration data");
    }

    const json = await response.json();
    config = json;
  } catch (error) {
    console.error(error.message);
  }
  return config;
}

function prepareLayer(layer){
  layer.markerLayer = null;
  layer.leafletOverlays = [];
}

function prepareLayers(layers){
  layers.forEach((layer) => {
    prepareLayer(layer);
  });
}

function revertLayer(layer, markerLayer, leafletOverlays){
  layer.markerLayer = markerLayer;
  layer.leafletOverlays = leafletOverlays;
}

function revertLayers(layers, markerLayers, leafletOverlays){
  // add markerLayer back to layers
  layers.forEach((layer, index) => {
    revertLayer(layer, markerLayers[index], leafletOverlays[index]);
  });
}

function layerToBody(layer){
  const body = JSON.stringify(layer, function (key, value) {
    if (value && typeof value === 'object' && key === "") {
      var replacement = {};
      for (var k in value) {
        if (Object.hasOwnProperty.call(value, k)) {
          const camelToSnakeCase = str => str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);
          const snake_k = camelToSnakeCase(k);
          replacement[snake_k] = value[k];
        }
      }
      return replacement;
    }
    return value;
  }, 2);
  return body;
}

// function to update the configuration data on the backend
export async function updateLayerConfig(layer) {
  const url = "http://localhost:8000/update_layer_config_entry";
  
  // prepare layer for serialization
  const markerLayer = layer.markerLayer;
  const leafletOverlay = layer.leafletOverlays;
  prepareLayer(layer);

  const layerCpy = structuredClone(layer);

  // revert layer back to original state
  revertLayer(layer, markerLayer, leafletOverlay);

  const body = layerToBody(layerCpy)
  
  // send the updated configuration data to the backend
  try {
    const response = await fetch(url, {
      method: "POST",
      body: body,
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error("Failed to update layer config entry");
    }
  } catch (error) {
    console.error(error.message);
  }
  
}

// function to delete the configuration data on the backend
export async function deleteLayerConfig(layerPos) {
  const url = "http://localhost:8000/delate_layer_config_entry";

  // add layer position as path parameter
  const urlWithPos = url + "/" + layerPos;
  
  
  // send the updated configuration data to the backend
  try {
    const response = await fetch(urlWithPos, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error("Failed to delete layer config entry");
    }
  } catch (error) {
    console.error(error.message);
  }
  
}

// function to update the configuration data on the backend
export async function updateTotalConfig(layers) {
  const url = "http://localhost:8000/update_total_layer_config";
  
  // prepare layers for serialization
  const markerLayers = layers.map((layer) => layer.markerLayer);
  const leafletOverlays = layers.map((layer) => layer.leafletOverlays);
  prepareLayers(layers);

  const layersCpy = structuredClone(layers);

  // revert layers back to original state
  revertLayers(layers, markerLayers, leafletOverlays);
  // create the configuration data


  let body = "[";
  layersCpy.forEach((layer) => {
    body += layerToBody(layer);
    body += ',';
  })
  body = body.slice(0, -1)
  body += ']';
  // send the updated configuration data to the backend
  try {
    const response = await fetch(url, {
      method: "POST",
      body: body,
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error("Failed to update configuration data");
    }
  } catch (error) {
    console.error(error.message);
  }
  
}

export async function updateDynamicLayerEntry(entry){
  const url = "http://localhost:8000/update_dynamic_layer_entry";
  try {
    const response = await fetch(url, {
      method: "POST",
      body: JSON.stringify(entry, null, 2),
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error("Failed to update configuration data");
    }
  } catch (error) {
    console.error(error.message);
  }
}

export async function deleteDynamicLayerEntry(entry){
  const url = "http://localhost:8000/delete_dynamic_layer_entry";
  try {
    const response = await fetch(url, {
      method: "POST",
      body: JSON.stringify(entry, null, 2),
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error("Failed to update configuration data");
    }
  } catch (error) {
    console.error(error.message);
  }
}



export async function updateConfigDynamicLayers(markers, polylines, polygons){
  const url = "http://localhost:8000/update_total_dynamic_layer";
  try {
    const response = await fetch(url, {
      method: "POST",
      body: JSON.stringify({markers, polylines, polygons}, null, 2),
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error("Failed to update configuration data");
    }
  } catch (error) {
    console.error(error.message);
  }
}

export async function updateConfigLocationTypes(locationTypes){
  const url = "http://localhost:8000/update_total_location_type_table";
  //console.log(locationTypes);
  const locationTypesCpy = structuredClone(locationTypes);
  // iterate over locationTypes and change locationType field to location_type
  locationTypesCpy.forEach((locationType) => {
    locationType.location_type = locationType.locationType;
    delete locationType.locationType;
  });
  try {
    const response = await fetch(url, {
      method: "POST",
      body: JSON.stringify(locationTypesCpy, null, 2),
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error("Failed to update configuration data");
    }
  } catch (error) {
    console.error(error.message);
  }
}


export async function checkExternalUpdate() {
  const url = "http://localhost:8000/external_update";
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error("Failed to check for external update");
    }

    const json = await response.json();
    return json;
  } catch (error) {
    console.error(error.message);
  }
}

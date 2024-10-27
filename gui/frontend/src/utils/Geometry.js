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
  const R = 6371; // 6371 km

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

/**
 * Convert radians to degrees
 * @param {*} radians
 * @returns The value in degrees
 * @description The function is taken from https://www.movable-type.co.uk/scripts/latlong.html
 * The function is used in the haversineDistance function
 */
export function toDegrees(radians) {
  return radians * (180 / Math.PI);
}

/**
 * Convert latitude and longitude to Web Mercator coordinates
 * @param {*} latitude
 * @param {*} longitude
 * @returns An object with the x and y coordinates
 * @description The function is taken from https://www.movable-type.co.uk/scripts/latlong.html
 */
export function latLonToWebMercator(latitude, longitude) {
  const earthRadius = 6378137; // Earth radius in meters
  const x = longitude * ((earthRadius * Math.PI) / 180.0);
  const y =
    Math.log(Math.tan(((90 + latitude) * Math.PI) / 360.0)) *
    ((earthRadius * Math.PI) / 180.0);

  return { x: x, y: y };
}

/**
 * Calculate the distance between two points on the earth in meters
 * @param {*} point1 The latitude and longitude of the first point
 * @param {*} point2 The latitude and longitude of the second point
 * @returns The distance between the two points in meters
 * @description The function uses the Haversine formula
 * The formula is taken from https://www.movable-type.co.uk/scripts/latlong.html
 */
export function haversineDistanceBetweenPoints(point1, point2) {
  return haversineDistance(point1[0], point1[1], point2[0], point2[1]);
}

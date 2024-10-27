import React from "react";

import { C } from "../managers/Core.js";

import Popover from "@mui/material/Popover";
import Typography from "@mui/material/Typography";
import Fab from "@mui/material/Fab";

//icons
import WbSunnyOutlinedIcon from "@mui/icons-material/WbSunnyOutlined";
import ThermostatIcon from "@mui/icons-material/Thermostat";
import WaterDropIcon from "@mui/icons-material/WaterDrop";
import CompressIcon from "@mui/icons-material/Compress";
import { Container } from "react-bootstrap";

export default function WeatherInfoBox() {
  // anchorEl is used to anchor the popover to the fab button
  const [anchorEl, setAnchorEl] = React.useState(null);

  // handle click event for the fab button
  const handleClick = (event) => {
    // get map location
    const mapCenter = C().mapMan.map.getCenter();
    const location = [mapCenter.lat, mapCenter.lng];
    weatherData(location);
    setAnchorEl(event.currentTarget);
  };

  // handle close event for the popover
  const handleClose = () => {
    setAnchorEl(null);
  };
  const [temperature, setTemperature] = React.useState(0);
  const [precipitation, setPrecipitation] = React.useState(0);
  const [surfacePressure, setSurfacePressure] = React.useState(0);

  /**
   * fetch weather data from dwd api. Example:
   * curl --request GET \
   * --url https://api.brightsky.dev/current_weather?lat={location[0]}&lon={location[1]} \
   * --header 'Accept: application/json'
   * @param {[lat, lon]} location
   * @returns
   */
  const weatherData = async (location) => {
    const response = await fetch(
      `https://api.brightsky.dev/current_weather?lat=${location[0]}&lon=${location[1]}`,
      {
        headers: {
          Accept: "application/json",
        },
      },
    );
    const data = await response.json();

    if (!response.ok) {
      console.error("Error fetching weather data:", data);
      // set unknown values if the weather data could not be fetched
      setTemperature(undefined);
      setPrecipitation(undefined);
      setSurfacePressure(undefined);
      return;
    }

    // get weather data for the current hour
    let temperature = data.weather.temperature;
    let precipitation = data.weather.precipitation_60;
    let surfacePressure = data.weather.pressure_msl;
    setTemperature(temperature);
    setPrecipitation(precipitation);
    setSurfacePressure(surfacePressure);
  };

  // open is true if the anchorEl is not null
  const open = Boolean(anchorEl);

  return (
    <div>
      <Fab
        onClick={handleClick}
        style={{
          color: "white",
          backgroundColor: "black",
          position: "absolute",
          bottom: "12px",
          left: "12px",
        }}
      >
        <WbSunnyOutlinedIcon />
      </Fab>
      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{
          vertical: "bottom",
          horizontal: "right",
        }}
        transformOrigin={{
          vertical: "bottom",
          horizontal: "left",
        }}
      >
        <Container
          style={{
            backgroundColor: "black",
          }}
        >
          <div
            style={{
              display: "flex",
              flexDirection: "row",
              justifyContent: "center",
              alignItems: "center",
            }}
          >
            <Typography color="common.white" sx={{ ml: 1, p: 1 }}>
              Weathers
            </Typography>
          </div>
          <Typography color="common.white" sx={{ ml: 1, p: 1 }}>
            <ThermostatIcon />: {temperature}°C
          </Typography>
          <Typography color="common.white" sx={{ ml: 1, p: 1 }}>
            <WaterDropIcon />: {precipitation} mm
          </Typography>
          <Typography color="common.white" sx={{ ml: 1, p: 1 }}>
            <CompressIcon />: {surfacePressure} hPa
          </Typography>
        </Container>
      </Popover>
    </div>
  );
}

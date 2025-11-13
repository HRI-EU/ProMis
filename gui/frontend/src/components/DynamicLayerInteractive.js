import { C } from "../managers/Core.js";

import React from "react";
import PropTypes from "prop-types";

import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import {
  Box,
  Grid2,
  IconButton,
  MenuItem,
  Paper,
  Select,
  SvgIcon,
  FormControl,
  InputLabel,
  Tooltip,
} from "@mui/material";
import LightbulbIcon from "@mui/icons-material/Lightbulb";
import LightbulbOutlinedIcon from "@mui/icons-material/LightbulbOutlined";
import PolylineIcon from "@mui/icons-material/Polyline";
import PentagonIcon from "@mui/icons-material/Pentagon";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import CloseOutlinedIcon from "@mui/icons-material/CloseOutlined";
import {
  getLandingPadIconJSX,
  getDefaultMarkerJSX,
  getDroneIconJSX,
} from "../utils/getIcons.js";

const darkTheme = createTheme({
  palette: {
    mode: "dark",
  },
});

const fontSize = "0.95rem";


/*
  This Component includes the lightbolt button in middle left to put geo-entity to front or back
  and the interactive pop up (when double-clicking an geo-entity) on top left to display and adjust geo-entitys properties like id,
  coordinates, location type and uncertainty.
  props: these are information for the interactive pop up
    id: id of the chosen entity
    icon ("defaultMarker" | "droneMarker" | "landingSiteMarker" | "Line" | "Polygon"): icon of the entity
    name (str): name of the entity
    coordinates ([lat, lng] | [[lat, lng]]): coordinate of the entity
    locationType (str): location type of the entity
    toggle (bool): use for forcing the pop-up to appear (change its state to trigger pop up)
    hidden (bool): set true upon first render to ensure pop up stays hidden
    disabled (bool): if location type and uncertainty edit is disabled.
*/
export default function DynamicLayerInteractive({
  id,
  icon,
  name,
  coordinates,
  locationType,
  uncertainty,
  toggle,
  hidden,
  disabled,
}) {
  // state var to set entity layer on top
  const [dynamicOnTop, setDynamicOnTop] = React.useState(false);
  // state for uncertainty number input
  const [uncertaintyInput, setUncertaintyInput] = React.useState(uncertainty);
  // state for current displayed latlng pair for entitys that have multi coordinate (line, polygon)
  const [currentCoordinateIndex, setCurrentCoordinateIndex] = React.useState(0);
  // state for the location type drop down input
  const [locationTypeInput, setLocationTypeInput] =
    React.useState(locationType);

  // state for changing input color of uncertainty if it is differ from default location type uncertainty
  const [isUniqueUncertainty, setIsUniqueUncertainty] = React.useState(false);
  // state to hide pop up when close
  const [visible, setVisible] = React.useState(false);

  // update coordinate indicator when change coordinate
  React.useEffect(() => {
    if (!isTypeMarker()) {
      C().mapMan.setMapCircleHighlight(coordinates[currentCoordinateIndex]);
    } else {
      C().mapMan.removeCircleHighlight();
    }
  }, [currentCoordinateIndex]);

  // debounce input effect (update backend and changing color)
  React.useEffect(() => {
    const delayInputTimeoutId = setTimeout(() => {
      C().mapMan.uncertaintyChange(uncertaintyInput);
      // check if uncertainty is different from default uncertainty of location type
      const defaultUncertainty =
        C().sourceMan.getUncertaintyFromLocationType(locationTypeInput);
      if (uncertaintyInput !== defaultUncertainty) {
        setIsUniqueUncertainty(true);
      } else {
        setIsUniqueUncertainty(false);
      }
    }, 500);
    return () => clearTimeout(delayInputTimeoutId);
  }, [uncertaintyInput]);

  // updates state when change entity
  React.useEffect(() => {
    setCurrentCoordinateIndex(0);
    if (!isTypeMarker()) {
      C().mapMan.setMapCircleHighlight(coordinates[0]);
    } else {
      C().mapMan.removeCircleHighlight();
    }
    setUncertaintyInput(uncertainty);
    setLocationTypeInput(locationType);
  }, [id]);

  // force pop up to appear when receving toggle input
  React.useEffect(() => {
    setVisible(true);
  }, [toggle]);

  // clean up coordinate indicator when pop up not visible
  React.useEffect(() => {
    if (!visible) {
      C().mapMan.removeCircleHighlight();
    } else {
      if (!isTypeMarker()) {
        C().mapMan.setMapCircleHighlight(coordinates[currentCoordinateIndex]);
      } else {
        C().mapMan.removeCircleHighlight();
      }
    }
  }, [visible]);

  React.useEffect(() => {
    setUncertaintyInput(uncertainty);
  }, [uncertainty]);

  React.useEffect(() => {
    setLocationTypeInput(locationType);
  }, [locationType]);

  function isTypeMarker() {
    return (
      icon === "defaultMarker" ||
      icon === "droneMarker" ||
      icon === "landingSiteMarker"
    );
  }

  function getIconJSX(iconType) {
    switch (iconType) {
      case "defaultMarker":
        return getDefaultMarkerJSX("#ffffff");
      case "droneMarker":
        return getDroneIconJSX("#ffffff");
      case "landingSiteMarker":
        return getLandingPadIconJSX("#ffffff");
      case "Line":
        return <PolylineIcon style={{ color: "#ffffff" }} />;
      case "Polygon":
        return <PentagonIcon style={{ color: "#ffffff" }} />;
      default:
        return getDefaultMarkerJSX("#ffffff");
    }
  }

  // return a string [lat, lng] to display
  function getCurrentDisplayCoordinate() {
    if (typeof coordinates[0] !== "number") {
      if (coordinates[currentCoordinateIndex] === undefined) {
        return `NA`;
      }
      return `[${coordinates[currentCoordinateIndex][0].toFixed(
        3,
      )}, ${coordinates[currentCoordinateIndex][1].toFixed(3)}]`;
    } else
      return `[${coordinates[0].toFixed(3)}, ${coordinates[1].toFixed(3)}]`;
  }

  // used for coordinate switch button
  function nextCoordinate() {
    setCurrentCoordinateIndex((prev) => (prev + 1) % coordinates.length);
  }

  // location type change handle
  function onLocationTypeChange(event) {
    const newLocationType = event.target.value;
    setLocationTypeInput(newLocationType);
    // update internal and color
    C().mapMan.locationTypeChange(newLocationType);
    // set default uncertainty from loc type
    setUncertaintyInput(
      C().sourceMan.getUncertaintyFromLocationType(newLocationType),
    );
  }

  // returns array of location type to display for select input
  function createSelectItems() {
    let items = [];
    const locationTypeList = C().sourceMan.getListLocationType();
    // remove VERIPORT if not of type landing site
    if (icon !== "landingSiteMarker") {
      const index = locationTypeList.indexOf("VERTIPORT");
      if (index > -1) {
        locationTypeList.splice(index, 1);
      } 
    }
    for (var i = 0; i < locationTypeList.length; i++) {
      items.push(
        <MenuItem key={`select-item-key-${i}`} value={locationTypeList[i]}>
          {locationTypeList[i]}
        </MenuItem>,
      );
    }
    return items;
  }

  /* Entity Main Content */
  const entityGrid = (
    <Grid2
      container
      spacing={2}
      padding={2}
      sx={{
        fontSize: fontSize,
      }}
    >
      {/* Icon and Name */}
      <Grid2 size={3}>
        <SvgIcon>{getIconJSX(icon)}</SvgIcon>
      </Grid2>
      <Grid2 size={9}>
        <div
          style={{
            color: "white",
            fontSize: "16px",
            fontWeight: "bold",
            textAlign: "center",
          }}
        >
          {name}
        </div>
      </Grid2>
      {/* Horizontal line */}
      <Grid2
        size={12}
        style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.73)" }}
      ></Grid2>
      {/* Id Field */}
      <Grid2 size={3}>
        <div
          style={{
            color: "white",
            textAlign: "left",
          }}
        >
          {`Id:`}
        </div>
      </Grid2>
      <Grid2 size={9}>
        <div
          style={{
            color: "white",
            textAlign: "right",
          }}
        >
          {id}
        </div>
      </Grid2>
      {/* Coordinate Field */}
      <Grid2 size={5}>
        <div
          style={{
            color: "white",
            textAlign: "left",
          }}
        >
          {`Coordinates:`}
        </div>
      </Grid2>
      <Grid2 size={7}>
        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
          }}
        >
          <div
            style={{
              color: "white",
              textAlign: "right",
            }}
          >
            {getCurrentDisplayCoordinate()}
          </div>
          {isTypeMarker() ? null : (
            <IconButton
              aria-label="next coordinate"
              variant="outlined"
              sx={{
                width: 20,
                height: 20,
                marginLeft: "5px",
                paddingBottom: "4px",
              }}
              color="primary"
              onClick={nextCoordinate}
            >
              <ChevronRightIcon />
            </IconButton>
          )}
        </div>
      </Grid2>
      {/* Location Type Select Input */}
      <Grid2>
        <Box
          sx={{
            minWidth: 120,
          }}
        >
          <FormControl
            sx={{
              width: "100%",
              fontSize: fontSize,
            }}
          >
            <InputLabel
              sx={{
                color: "rgba(255, 255, 255, 0.7)",
                fontSize: fontSize,
              }}
            >
              Location Type
            </InputLabel>
            <Select
              label="Location Type"
              value={locationTypeInput}
              onChange={onLocationTypeChange}
              size="small"
              sx={{
                fontSize: fontSize,
              }}
              disabled={disabled}
            >
              {createSelectItems()}
            </Select>
          </FormControl>
        </Box>
      </Grid2>
      {/* Uncertainty Field Input */}
      <Grid2>
        <Tooltip title="Uncertainty">
          <Box
            sx={{
              maxWidth: 80,
              fontSize: fontSize,
            }}
          >
            <TextField
              type="number"
              value={uncertaintyInput}
              onChange={(e) => setUncertaintyInput(parseFloat(e.target.value))}
              size="small"
              label={
                <Typography variant="body2" color="textSecondary">
                  σ (m)
                </Typography>
              }
              fullWidth
              disabled={disabled}
              sx={{
                input: {
                  color: isUniqueUncertainty ? "white" : "gray",
                },
              }}
              slotProps={{
                htmlInput: {
                  style: {
                    fontSize: fontSize,
                  },
                },
              }}
            />
          </Box>
        </Tooltip>
      </Grid2>
    </Grid2>
  );

  const onDynamicClick = () => {
    setDynamicOnTop(!dynamicOnTop);
    C().mapMan.toggleDynamicOnTop(dynamicOnTop);
  };

  return (
    <div>
      {/* Toggle entity to front or back interface */}
      <div
        className="leaflet-control"
        style={{
          position: "absolute",
          top: "320px",
          left: "10px",
          zIndex: 1001,
          border: "2px solid rgba(0,0,0,0.2)",
        }}
      >
        <IconButton
          aria-label="highlight"
          className="leaflet-buttons-control-button"
          style={{
            backgroundColor: "white",
            color: "#495057",
            borderRadius: 0,
            width: "30px",
            height: "30px",
          }}
          onClick={onDynamicClick}
        >
          {dynamicOnTop ? <LightbulbIcon /> : <LightbulbOutlinedIcon />}
        </IconButton>
      </div>

      {/* Top-Left Pop Up Interface */}
      {!hidden && visible ? (
        <ThemeProvider theme={darkTheme}>
          <Paper
            elevation={0}
            sx={{
              position: "absolute",
              top: "10px",
              left: "60px",
              zIndex: 1001,
              maxWidth: "270px",
              maxHeight: "400px",
              backgroundColor: "#0D0F21",
            }}
          >
            {entityGrid}
            <IconButton
              aria-label="close info box"
              size="small"
              sx={{
                position: "absolute",
                top: "3px",
                right: "3px",
              }}
              onClick={() => setVisible(false)}
            >
              <CloseOutlinedIcon />
            </IconButton>
          </Paper>
        </ThemeProvider>
      ) : null}
    </div>
  );
}

// props validation
DynamicLayerInteractive.propTypes = {
  id: PropTypes.string.isRequired,
  icon: PropTypes.string.isRequired,
  name: PropTypes.string.isRequired,
  coordinates: PropTypes.arrayOf(PropTypes.number).isRequired,
  locationType: PropTypes.string.isRequired,
  uncertainty: PropTypes.number.isRequired,
  toggle: PropTypes.bool.isRequired,
  hidden: PropTypes.bool,
  disabled: PropTypes.bool,
};

import { C } from "../managers/Core.js";

import React from "react";
import PropTypes from 'prop-types';

import TextField from '@mui/material/TextField';
import Typography from "@mui/material/Typography";
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { Box, Grid2, IconButton, MenuItem, Paper, Select, SvgIcon, FormControl, InputLabel, Tooltip } from "@mui/material";
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import LightbulbOutlinedIcon from '@mui/icons-material/LightbulbOutlined';
import PolylineIcon from '@mui/icons-material/Polyline';
import PentagonIcon from '@mui/icons-material/Pentagon';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import CloseOutlinedIcon from '@mui/icons-material/CloseOutlined';
import { getLandingPadIconJSX, getDefaultMarkerJSX, getDroneIconJSX } from "../utils/getIcons.js";

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
});

const fontSize = "0.95rem"

export default function DynamicLayerInteractive({id, icon, name, coordinates, locationType, uncertainty, toggle, hidden, disabled}) {
    const [dynamicOnTop, setDynamicOnTop] = React.useState(false);
    const [uncertaintyInput, setUncertaintyInput] = React.useState(uncertainty);
    const [currentCoordinateIndex, setCurrentCoordinateIndex] = React.useState(0);
    const [locationTypeInput, setLocationTypeInput] = React.useState(locationType);
    const [isUniqueUncertainty, setIsUniqueUncertainty] = React.useState(false);
    const [visible, setVisible] = React.useState(false);

    React.useEffect(() => {
      if (!isTypeMarker()){
        C().mapMan.setMapCircleHighlight(coordinates[currentCoordinateIndex]);
      } else {
        C().mapMan.removeCircleHighlight();
      }
    }, [currentCoordinateIndex])

    // debounce input effect
    React.useEffect(() => {
      const delayInputTimeoutId = setTimeout(() => {
        C().mapMan.uncertaintyChange(uncertaintyInput);
        // check if uncertainty is different from default uncertainty of location type
        const defaultUncertainty = C().sourceMan.getUncertaintyFromLocationType(locationTypeInput);
        if (uncertaintyInput !== defaultUncertainty) {
          setIsUniqueUncertainty(true);
        } else {
          setIsUniqueUncertainty(false);
        }
      }, 500)
      return () => clearTimeout(delayInputTimeoutId);
    }, [uncertaintyInput]);

    React.useEffect(() => {
      setCurrentCoordinateIndex(0);
      if (!isTypeMarker()){
        C().mapMan.setMapCircleHighlight(coordinates[0]);
      } else {
        C().mapMan.removeCircleHighlight();
      }
      setUncertaintyInput(uncertainty);
    }, [id])

    React.useEffect(() => {
      setVisible(true);
    }, [toggle])

    React.useEffect(() => {
      if (!visible){
        C().mapMan.removeCircleHighlight();
      } else {
        if (!isTypeMarker()){
          C().mapMan.setMapCircleHighlight(coordinates[currentCoordinateIndex]);
        } else {
          C().mapMan.removeCircleHighlight();
        }
      }
    }, [visible]);

    React.useEffect(() => {
      setUncertaintyInput(uncertainty);
    }, [uncertainty])

    React.useEffect(() => {
      setLocationTypeInput(locationType);
    }, [locationType])
    
    function isTypeMarker(){
      return icon === "defaultMarker" || icon === "droneMarker" || icon === "landingSiteMarker"
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

    function getCurrentDisplayCoordinate() {
      if (typeof coordinates[0] !== "number"){
        if (coordinates[currentCoordinateIndex] === undefined) {
          return `NA`;
        }
        return `[${coordinates[currentCoordinateIndex][0].toFixed(3)}, ${coordinates[currentCoordinateIndex][1].toFixed(3)}]`;
      }
      else
        return `[${coordinates[0].toFixed(3)}, ${coordinates[1].toFixed(3)}]`;
    }

    function nextCoordinate(){
      setCurrentCoordinateIndex((prev) => (prev + 1) % coordinates.length);
    }

    function onLocationTypeChange(event) {
      const newLocationType = event.target.value;
      setLocationTypeInput(newLocationType);
      C().mapMan.locationTypeChange(newLocationType);
      setUncertaintyInput(C().sourceMan.getUncertaintyFromLocationType(newLocationType));
    }

    function createSelectItems() {
      let items = [];
      const locationTypeList = C().sourceMan.getListLocationType();
      for (var i = 0; i < locationTypeList.length; i++) {
        items.push(<MenuItem key={`select-item-key-${i}`}
          value={locationTypeList[i]}
        >
          {locationTypeList[i]}
        </MenuItem>)
      }
      return items;
    }

    // create a grid with icon depending on the type of entity
    const entityGrid =
      <Grid2 container spacing={2} padding={2}
        sx={{
          fontSize: fontSize
        }}
      >
        <Grid2 size={3}>
          <SvgIcon>
            {getIconJSX(icon)}
          </SvgIcon>
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
        {/*horizontal line*/}
        <Grid2 size={12} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.73)" }}></Grid2>
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
              justifyContent: "flex-end"
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
            {isTypeMarker() ? null : <IconButton
              aria-label="next coordinate"
              variant="outlined"
              sx={{
                width: 20,
                height: 20,
                marginLeft: "5px",
                paddingBottom: "4px"
              }}
              color="primary"
              onClick={nextCoordinate}
            >
              <ChevronRightIcon/>
            </IconButton>}
          </div>
        </Grid2>
        <Grid2
        >
          <Box
            sx={{
              minWidth: 120
            }}
          >
            <FormControl
              sx={{
                width: "100%",
                fontSize: fontSize
              }}
            >
              <InputLabel
                  sx={{ 
                    color: "rgba(255, 255, 255, 0.7)",
                    fontSize: fontSize
                  }}
              >Location Type</InputLabel>
              <Select
                label="Location Type"
                value={locationTypeInput}
                onChange={onLocationTypeChange}
                size="small"
                sx={{
                  fontSize: fontSize
                }}
                disabled={disabled}
              >
                {createSelectItems()}
              </Select>
            </FormControl>
          </Box>
        </Grid2>
        <Grid2 
        >
          <Tooltip title = "Uncertainty">
            <Box sx={{
              maxWidth:80,
              fontSize: fontSize
            }}
            >
              <TextField
                type="number"
                value={uncertaintyInput}
                onChange={(e) => setUncertaintyInput(parseFloat(e.target.value))}
                size="small"
                label={<Typography variant="body2" color="textSecondary">σ (m)</Typography>}
                fullWidth
                disabled={disabled}
                sx={{
                  input:{
                    color: isUniqueUncertainty ? "white" : "gray"
                  }
                }}
                slotProps={{
                  htmlInput: {
                    style: {
                      fontSize: fontSize
                    }
                  }
                }}
              />
            </Box>
          </Tooltip>
        </Grid2>
      </Grid2>;

    const onDynamicClick = () => {
      setDynamicOnTop(!dynamicOnTop);
      C().mapMan.toggleDynamicOnTop(dynamicOnTop);
    }

    return (
      <div>
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
          <IconButton aria-label="highlight" 
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
        
        {
          !hidden && visible ? 
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
                  backgroundColor: "#0D0F21"
                }}
              >
                {entityGrid}
                <IconButton
                  aria-label="close info box"
                  size="small"
                  sx={{
                    position: "absolute",
                    top: "3px",
                    right: "3px"
                  }}
                  onClick={() => setVisible(false)}
                >
                  <CloseOutlinedIcon/>
                </IconButton>
              </Paper>
            </ThemeProvider>
          : null
        }
      </div>
    )
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
  disabled: PropTypes.bool
};

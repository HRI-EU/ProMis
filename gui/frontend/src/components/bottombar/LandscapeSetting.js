import * as React from "react";
import PropTypes from "prop-types";

import Grid from "@mui/material/Grid2";
import { FormControl, InputLabel, MenuItem, Select } from "@mui/material";
import TextField from "@mui/material/TextField";

import { C } from "../../managers/Core";

/*
    React function component for landscape setting in bottom bar.

    @param {string} origin
    @param {(int, int)} dimensions
    @param {(int, int)} resolutions
    @param {(int, int)} supportResolutions
    @param {int} sampleSize
    @param {bool} highlightOriginElement
    @param {function(LandscapeSetting)} onEdit
*/
export default function LandscapeSetting({
  origin,
  dimensions,
  resolutions,
  supportResolutions,
  sampleSize,
  interpolation,
  highlightOriginElement,
  onEdit,
}) {
  let landscapeSetting = {
    origin: origin,
    dimensions: dimensions,
    resolutions: resolutions,
    supportResolutions: supportResolutions,
    sampleSize: sampleSize,
    interpolation: interpolation,
  };

  const inputSize = 100;

  // create origin select items from existing origin markers
  function createOriginSelectItems() {
    let items = [];
    const markers = C().mapMan.listOriginMarkers();
    for (let i = 0; i < markers.length; i++) {
      items.push(
        <MenuItem key={i + 1} value={markers[i].feature.properties["name"]}>
          {markers[i].feature.properties["name"]}
        </MenuItem>,
      );
    }
    return items;
  }

  // create interpolation select items
  function createInterpolationItems() {
    let items = ["linear", "nearest", "gaussian_process"];
    return items.map((item, index) => {
      return (
        <MenuItem key={index} value={item}>
          {item}
        </MenuItem>
      );
    });
  }

  function handleOriginChange(event) {
    //update origin
    landscapeSetting.origin = event.target.value;
    onEdit(landscapeSetting);

    // get marker with this origin name
    const latLon = C().mapMan.latlonFromMarkerName(event.target.value);
    // recenter map
    C().mapMan.recenterMap(latLon);
  }

  return (
    <Grid
      container
      spacing={2}
      direction="column"
      alignItems="start"
      justifyContent="center"
      m={1}
      style={{ marginLeft: "38px", width: "90%" }}
    >
      {/* First Row: Origin, Dimensions, Sample Size */}
      <Grid
        container
        size={12}
        direction="row"
        justifyContent="start"
        alignItems="center"
        spacing={2}
      >
        {/* Origin Selection Input */}
        <Grid container size={4}>
          <FormControl
            sx={{ minWidth: 125 }}
            size="small"
            error={highlightOriginElement}
          >
            <InputLabel style={{ color: "#ffffff" }}>Origin</InputLabel>
            <Select
              label="Origin"
              variant="outlined"
              value={origin}
              onChange={handleOriginChange}
            >
              {createOriginSelectItems()}
            </Select>
          </FormControl>
        </Grid>
        {/* Dimensions Input */}
        <Grid
          container
          direction="row"
          justifyContent="start"
          alignItems="center"
          spacing={0}
          size={5}
        >
          <Grid>
            {/* Width Input */}
            <TextField
              type="number"
              size="small"
              label="Width (m)"
              variant="outlined"
              value={dimensions[0]}
              onFocus={() =>
                C().mapMan.highlightBoundaryAlter(
                  origin,
                  dimensions,
                  resolutions,
                  supportResolutions,
                )
              }
              onChange={(e) => {
                const newValue = e.target.value;
                const newDimensions = [newValue, dimensions[1]];
                landscapeSetting.dimensions = newDimensions;
                onEdit(landscapeSetting);
                C().mapMan.highlightBoundaryAlter(
                  origin,
                  newDimensions,
                  resolutions,
                  supportResolutions,
                );
              }}
              onBlur={() => {
                C().mapMan.unhighlightBoundaryAlter();
              }}
              sx={{
                width: inputSize,
              }}
            />
          </Grid>
          <div
            style={{
              marginLeft: "2px",
              color: "#ffffff",
            }}
          >
            x
          </div>
          <Grid>
            {/* Height Input */}
            <TextField
              type="number"
              size="small"
              label="Height (m)"
              variant="outlined"
              value={dimensions[1]}
              onFocus={() =>
                C().mapMan.highlightBoundaryAlter(
                  origin,
                  dimensions,
                  resolutions,
                  supportResolutions,
                )
              }
              onChange={(e) => {
                const newValue = e.target.value;
                const newDimensions = [dimensions[0], newValue];
                landscapeSetting.dimensions = newDimensions;
                onEdit(landscapeSetting);
                C().mapMan.highlightBoundaryAlter(
                  origin,
                  newDimensions,
                  resolutions,
                  supportResolutions,
                );
              }}
              onBlur={() => {
                C().mapMan.unhighlightBoundaryAlter();
              }}
              sx={{
                width: inputSize,
              }}
            />
          </Grid>
        </Grid>

        {/* Sample Size Input */}
        <Grid size={3} container>
          <TextField
            type="number"
            size="small"
            variant="outlined"
            label="Sampled Maps"
            value={sampleSize}
            onChange={(e) => {
              landscapeSetting.sampleSize = e.target.value;
              onEdit(landscapeSetting);
            }}
            sx={{
              width: 125,
            }}
          />
        </Grid>
      </Grid>
      {/* Second Row: Resolutions, Support Resolutions and Interpolation */}
      <Grid
        container
        size={12}
        direction="row"
        justifyContent="start"
        justifyItems="start"
        alignItems="center"
        spacing={2}
      >
        {/* Resolutions Input */}
        <Grid alignItems={"center"} size={4} sx={{ display: "flex" }}>
          <TextField
            type="number"
            size="small"
            variant="outlined"
            label="Inference"
            value={resolutions[0]}
            onFocus={() =>
              C().mapMan.highlightBoundaryAlter(
                origin,
                dimensions,
                resolutions,
                supportResolutions,
              )
            }
            onChange={(e) => {
              const newValue = e.target.value;
              const newResolutions = [newValue, resolutions[1]];
              landscapeSetting.resolutions = newResolutions;
              onEdit(landscapeSetting);
              C().mapMan.highlightBoundaryAlter(
                origin,
                dimensions,
                newResolutions,
                supportResolutions,
              );
            }}
            onBlur={() => {
              C().mapMan.unhighlightBoundaryAlter();
            }}
            sx={{
              width: inputSize,
            }}
          />
          <div
            style={{
              marginLeft: "2px",
              color: "#ffffff",
            }}
          >
            x
          </div>
          <TextField
            type="number"
            size="small"
            variant="outlined"
            label="Grid"
            value={resolutions[1]}
            onFocus={() =>
              C().mapMan.highlightBoundaryAlter(
                origin,
                dimensions,
                resolutions,
                supportResolutions,
              )
            }
            onChange={(e) => {
              const newValue = e.target.value;
              const newResolutions = [resolutions[0], newValue];
              landscapeSetting.resolutions = newResolutions;
              onEdit(landscapeSetting);
              C().mapMan.highlightBoundaryAlter(
                origin,
                dimensions,
                newResolutions,
                supportResolutions,
              );
            }}
            onBlur={() => {
              C().mapMan.unhighlightBoundaryAlter();
            }}
            sx={{
              width: inputSize,
            }}
          />
        </Grid>
        {/* Support Resolutions Input */}
        <Grid
          container
          direction="row"
          justifyContent="start"
          alignItems="center"
          spacing={0}
          size={5}
        >
          <TextField
            type="number"
            size="small"
            variant="outlined"
            label="Interpolation"
            value={supportResolutions[0]}
            onFocus={() =>
              C().mapMan.highlightBoundaryAlter(
                origin,
                dimensions,
                resolutions,
                supportResolutions,
              )
            }
            onChange={(e) => {
              const newValue = e.target.value;
              const newSupportResolutions = [newValue, supportResolutions[1]];
              landscapeSetting.supportResolutions = newSupportResolutions;
              onEdit(landscapeSetting);
              C().mapMan.highlightBoundaryAlter(
                origin,
                dimensions,
                resolutions,
                newSupportResolutions,
              );
            }}
            onBlur={() => {
              C().mapMan.unhighlightBoundaryAlter();
            }}
            sx={{
              width: inputSize,
            }}
          />
          <div
            style={{
              marginLeft: "2px",
              color: "#ffffff",
            }}
          >
            x
          </div>
          <TextField
            type="number"
            size="small"
            variant="outlined"
            label="Grid"
            value={supportResolutions[1]}
            onFocus={() =>
              C().mapMan.highlightBoundaryAlter(
                origin,
                dimensions,
                resolutions,
                supportResolutions,
              )
            }
            onChange={(e) => {
              const newValue = e.target.value;
              const newSupportResolutions = [supportResolutions[0], newValue];
              landscapeSetting.supportResolutions = newSupportResolutions;
              onEdit(landscapeSetting);
              C().mapMan.highlightBoundaryAlter(
                origin,
                dimensions,
                resolutions,
                newSupportResolutions,
              );
            }}
            onBlur={() => {
              C().mapMan.unhighlightBoundaryAlter();
            }}
            sx={{
              width: inputSize,
            }}
          />
        </Grid>
        {/* Interpolation Method Selection */}
        <Grid size={3} container>
          <FormControl sx={{ minWidth: 125 }} size="small">
            <InputLabel style={{ color: "rgba(255, 255, 255, 0.7)" }}>
              Interpolation
            </InputLabel>
            <Select
              label="Interpolation"
              variant="outlined"
              value={interpolation}
              onChange={(event) => {
                landscapeSetting.interpolation = event.target.value;
                onEdit(landscapeSetting);
              }}
            >
              {createInterpolationItems()}
            </Select>
          </FormControl>
        </Grid>
      </Grid>
    </Grid>
  );
}

LandscapeSetting.propTypes = {
  origin: PropTypes.string.isRequired,
  dimensions: PropTypes.arrayOf(PropTypes.string).isRequired,
  resolutions: PropTypes.arrayOf(PropTypes.string).isRequired,
  supportResolutions: PropTypes.arrayOf(PropTypes.string).isRequired,
  sampleSize: PropTypes.string.isRequired,
  interpolation: PropTypes.string.isRequired,
  highlightOriginElement: PropTypes.bool,
  onEdit: PropTypes.func.isRequired,
};

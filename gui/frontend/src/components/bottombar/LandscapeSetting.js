import * as React from "react";
import PropTypes from "prop-types";

import Grid from "@mui/material/Grid2";
import {
  Box,
  FormControl,
  FormHelperText,
  InputLabel,
  MenuItem,
  Select,
  InputAdornment,
  Typography,
} from "@mui/material";
import TextField from "@mui/material/TextField";

import { C } from "../../managers/Core";
import Hint from "../Hint";

// names and explanations of the interpolation methods
const INTERPOLATION_METHODS = [
  {
    value: "linear",
    label: "Linear",
    description: "Blends between neighboring inference cells",
  },
  {
    value: "nearest",
    label: "Nearest",
    description: "Copies the closest inference cell, fastest",
  },
  {
    value: "gaussian_process",
    label: "Gaussian process",
    description: "Smooth fit with uncertainty, slowest",
  },
];

// heading of a group of settings, with an explanation as tooltip
function GroupTitle({ title, help }) {
  return (
    <Box sx={{ display: "flex", alignItems: "center", color: "#ffffff" }}>
      <Typography variant="subtitle2">{title}</Typography>
      <Hint title={help} sx={{ marginLeft: "6px" }} />
    </Box>
  );
}

GroupTitle.propTypes = {
  title: PropTypes.string.isRequired,
  help: PropTypes.string.isRequired,
};

/*
    React function component for landscape setting in bottom bar.

    @param {string} origin
    @param {(int, int)} dimensions
    @param {(int, int)} resolutions
    @param {(int, int)} supportResolutions
    @param {int} sampleSize
    @param {object} errors - Invalid inputs to outline, or null to outline none
    @param {function(LandscapeSetting)} onEdit
*/
export default function LandscapeSetting({
  origin,
  dimensions,
  resolutions,
  supportResolutions,
  sampleSize,
  interpolation,
  errors,
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

  const inputSize = 88;

  // create origin select items from existing origin markers
  function createOriginSelectItems() {
    const markers = C().mapMan.listOriginMarkers();
    if (markers.length === 0) {
      return [
        <MenuItem key={0} value="" disabled sx={{ whiteSpace: "normal" }}>
          No origin yet: place a marker on the map, then pick it under Map
          features → ORIGIN
        </MenuItem>,
      ];
    }
    return markers.map((marker, i) => (
      <MenuItem key={i + 1} value={marker.feature.properties["name"]}>
        {marker.feature.properties["name"]}
      </MenuItem>
    ));
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

  // highlight the mission area and grids on the map while editing them
  function highlightBoundary(
    newDimensions = dimensions,
    newResolutions = resolutions,
    newSupportResolutions = supportResolutions,
  ) {
    C().mapMan.highlightBoundaryAlter(
      origin,
      newDimensions,
      newResolutions,
      newSupportResolutions,
    );
  }

  // a number input that highlights the mission area while focused
  function numberField(label, value, onChange, error = false) {
    return (
      <TextField
        type="number"
        size="small"
        label={label}
        variant="outlined"
        value={value}
        onFocus={() => highlightBoundary()}
        onChange={(e) => onChange(e.target.value)}
        onBlur={() => C().mapMan.unhighlightBoundaryAlter()}
        error={error}
        sx={{ width: inputSize }}
      />
    );
  }

  // two number inputs for a (width, height) or (columns, rows) pair
  function pairField(labels, values, onChange, pairErrors = [false, false]) {
    return (
      <Box sx={{ display: "flex", alignItems: "center" }}>
        {numberField(
          labels[0],
          values[0],
          (v) => onChange([v, values[1]]),
          pairErrors[0],
        )}
        <div style={{ margin: "0px 4px", color: "#ffffff" }}>×</div>
        {numberField(
          labels[1],
          values[1],
          (v) => onChange([values[0], v]),
          pairErrors[1],
        )}
      </Box>
    );
  }

  return (
    <Grid
      container
      spacing={2}
      wrap="nowrap"
      direction="row"
      alignItems="start"
      justifyContent="start"
      m={1}
      style={{ marginLeft: "38px", width: "90%" }}
    >
      {/* Mission area: origin and dimensions */}
      <Grid container direction="column" spacing={1.5}>
        <GroupTitle
          title="Mission area"
          help="The rectangle around the origin marker in which map features are loaded and the mission landscape is computed. Origins are markers of the type ORIGIN, see Map features."
        />
        <FormControl
          sx={{ width: 2 * inputSize + 20 }}
          size="small"
          error={Boolean(errors?.origin)}
        >
          <InputLabel style={{ color: "#ffffff" }}>Origin</InputLabel>
          <Select
            label="Origin"
            variant="outlined"
            sx={{ textAlign: "left" }}
            value={origin}
            onChange={handleOriginChange}
            MenuProps={{ PaperProps: { sx: { maxWidth: 260 } } }}
          >
            {createOriginSelectItems()}
          </Select>
          {errors?.origin ? (
            <FormHelperText>Choose an origin marker</FormHelperText>
          ) : null}
        </FormControl>
        {pairField(
          ["Width (m)", "Height (m)"],
          dimensions,
          (newDimensions) => {
            landscapeSetting.dimensions = newDimensions;
            onEdit(landscapeSetting);
            highlightBoundary(newDimensions);
          },
          errors?.dimensions,
        )}
      </Grid>

      {/* Inference: support grid and number of sampled maps */}
      <Grid container direction="column" spacing={1.5}>
        <GroupTitle
          title="Inference"
          help="Spatial relations such as distance(primary) are estimated on this grid of cells, from randomly shifted variants of the map. Finer grids and more samples are more accurate but slower."
        />
        {pairField(
          ["Columns", "Rows"],
          supportResolutions,
          (newSupportResolutions) => {
            landscapeSetting.supportResolutions = newSupportResolutions;
            onEdit(landscapeSetting);
            highlightBoundary(dimensions, resolutions, newSupportResolutions);
          },
          errors?.supportResolutions,
        )}
        <TextField
          type="number"
          size="small"
          variant="outlined"
          label="Sampled maps"
          slotProps={{
            input: {
              endAdornment: (
                <InputAdornment position="end">
                  <Hint title="How many randomly shifted variants of the map are sampled to estimate each relation, according to the uncertainties of the map features" />
                </InputAdornment>
              ),
            },
          }}
          error={Boolean(errors?.sampleSize)}
          value={sampleSize}
          onChange={(e) => {
            landscapeSetting.sampleSize = e.target.value;
            onEdit(landscapeSetting);
          }}
          sx={{ width: 2 * inputSize + 20 }}
        />
      </Grid>

      {/* Display: output grid and interpolation */}
      <Grid container direction="column" spacing={1.5}>
        <GroupTitle
          title="Display"
          help="The computed landscape is interpolated from the inference grid onto this finer grid of cells for display on the map, using the chosen interpolation method."
        />
        {pairField(
          ["Columns", "Rows"],
          resolutions,
          (newResolutions) => {
            landscapeSetting.resolutions = newResolutions;
            onEdit(landscapeSetting);
            highlightBoundary(dimensions, newResolutions);
          },
          errors?.resolutions,
        )}
        <FormControl sx={{ width: 2 * inputSize + 20 }} size="small">
          <InputLabel style={{ color: "rgba(255, 255, 255, 0.7)" }}>
            Interpolation
          </InputLabel>
          <Select
            label="Interpolation"
            variant="outlined"
            sx={{ textAlign: "left" }}
            value={interpolation}
            onChange={(event) => {
              landscapeSetting.interpolation = event.target.value;
              onEdit(landscapeSetting);
            }}
            renderValue={(value) =>
              INTERPOLATION_METHODS.find((method) => method.value === value)
                ?.label ?? value
            }
          >
            {INTERPOLATION_METHODS.map((method) => (
              <MenuItem key={method.value} value={method.value}>
                <Box>
                  <Typography variant="body2">{method.label}</Typography>
                  <Typography variant="caption" sx={{ opacity: 0.7 }}>
                    {method.description}
                  </Typography>
                </Box>
              </MenuItem>
            ))}
          </Select>
        </FormControl>
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
  errors: PropTypes.object,
  onEdit: PropTypes.func.isRequired,
};

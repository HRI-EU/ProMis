import { C } from "../../managers/Core";

import {
  Autocomplete,
  Box,
  Button,
  Chip,
  Grid2,
  Paper,
  Tab,
  Tabs,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import SaveIcon from "@mui/icons-material/Save";
import AddCircleOutlineOutlinedIcon from "@mui/icons-material/AddCircleOutlineOutlined";
import PanToolAltIcon from "@mui/icons-material/PanToolAlt";
import KeyboardReturnIcon from "@mui/icons-material/KeyboardReturn";
import { SliderPicker } from "react-color";
import React from "react";
import PropTypes from "prop-types";

import {
  FILTER_EXAMPLES,
  SOURCE_NAMES,
  describeFilter,
} from "../../utils/MapFilter";
import Hint from "../Hint";

// explanations of the built-in location types
const DEFAULT_TYPE_DESCRIPTIONS = {
  UNKNOWN: "Objects drawn on the map that have not been given a type yet.",
  ORIGIN:
    "Markers of this type can be chosen as the center of the mission area. Pick a marker on the map to make it an origin.",
  VERTIPORT: "Vertiports for take-off and landing, picked on the map.",
};

// cheat sheet for the filter syntax, shown as a tooltip
const FILTER_HELP = (
  <Box sx={{ fontSize: 12, lineHeight: 1.6 }}>
    <b>Overture Maps</b> (default): an Overture type, then optional conditions
    <br />
    <code>building</code>, <code>segment[subtype=road][class=primary]</code>,{" "}
    <code>place[basic_category=restaurant]</code>
    <br />
    Types: building, segment, land_use, land_cover, water, place, …
    <br />
    <br />
    <b>OpenStreetMap</b>: tag conditions in brackets
    <br />
    <code>[highway=primary]</code>, <code>[leisure=park]</code>
    <br />
    <br />
    Conditions: <code>[key]</code> exists, <code>[key=value]</code>,{" "}
    <code>[key!=value]</code>, <code>[key~regex]</code>. Several conditions must
    all hold.
  </Box>
);

// small button with a text label, used for the location type actions
function ActionButton({ icon, label, tooltip, onClick }) {
  return (
    <Tooltip title={tooltip}>
      <Button
        size="small"
        variant="outlined"
        startIcon={icon}
        onClick={onClick}
        sx={{ textTransform: "none", borderRadius: "16px" }}
      >
        {label}
      </Button>
    </Tooltip>
  );
}

ActionButton.propTypes = {
  icon: PropTypes.node.isRequired,
  label: PropTypes.string.isRequired,
  tooltip: PropTypes.string.isRequired,
  onClick: PropTypes.func.isRequired,
};

// explanations of where the features of a location type come from
const SOURCE_HINTS = {
  none: "Without a filter, only the objects picked on the map have this type",
  overture: "Features matching the filter are loaded from Overture Maps",
  osm: "Features matching the filter are loaded from OpenStreetMap",
};

// chip naming where the features of a filter are loaded from
function SourceChip({ filter }) {
  const { source } = describeFilter(filter);
  return (
    <Tooltip title={SOURCE_HINTS[source]}>
      <Chip
        size="small"
        variant="outlined"
        label={SOURCE_NAMES[source]}
        color={source === "none" ? "default" : "info"}
        sx={{ cursor: "help" }}
      />
    </Tooltip>
  );
}

SourceChip.propTypes = {
  filter: PropTypes.string,
};

/**
 * TabPanel component for rendering tab content.
 * @param {*} props
 * props.children - The content to be displayed within the tab panel.
 * props.value - The current selected tab index.
 * props.other - Additional properties to be spread onto the div.
 * @returns JSX.Element
 */
function TabPanel(props) {
  const { children, value, other } = props;
  return (
    <div
      role="tabpanel"
      id={`vertical-tabpanel-${value}`}
      aria-labelledby={`vertical-tab-${value}`}
      {...other}
    >
      {
        <Box
          sx={{
            p: 2,
            paddingTop: 0,
            marginRight: 3,
          }}
        >
          <Grid2 container justifyContent="flex-start" spacing={2}>
            {children}
          </Grid2>
        </Box>
      }
    </div>
  );
}

TabPanel.propTypes = {
  children: PropTypes.node,
  value: PropTypes.number.isRequired,
  other: PropTypes.object,
};

/**
 * LocationTypeSettingTabs component for managing location type settings.
 * Main features:
 * - Display tabs for each location type.
 * - Allow adding, editing, deleting location types.
 * - Enable choosing location types on the map.
 * @returns JSX.Element
 */
export default function LocationTypeSettingTabs({ showErrors }) {
  // tab state for selected tab index corresponding to location type array in source manager
  const [tabState, setTabState] = React.useState(0);
  // edit mode state for toggling between view and edit mode
  const [editMode, setEditMode] = React.useState(false);
  // choose mode state for toggling location type selection on the map
  const [chooseMode, setChooseMode] = React.useState(false);
  // highlight state for indicating invalid input during editing
  const [highlight, setHighlight] = React.useState(false);

  // following state for managing current editable location type fields
  // color state for managing the color of the location type
  const [color, setColor] = React.useState("#0000FF");
  // locationType state for managing the name of the location type
  const [locationType, setLocationType] = React.useState("");
  // filter state for managing the map filter string of the location type
  const [filter, setFilter] = React.useState("");
  // uncertainty state for managing the uncertainty value of the location type
  const [uncertainty, setUncertainty] = React.useState(10);

  // cleanup on unmount: remove any map click handlers and clean location type data
  // to prevent empty or inconsistent location type entries
  React.useEffect(() => {
    return () => {
      C().mapMan.removeLocationTypeOnClick();
      C().sourceMan.cleanLocationType();
    };
  }, []);

  // create location type items based on location types in source manager
  function createTabItems() {
    let items = [];
    const locTypes = C().sourceMan.locationTypes;
    for (let i = 0; i < locTypes.length; i++) {
      const id = `vertical-tab-${i}`;
      const invalid =
        showErrors && describeFilter(locTypes[i].filter).error !== null;
      const ariaControl = `vertical-tabpanel-${i}`;
      items.push(
        <Tab
          label={locTypes[i].locationType}
          id={id}
          aria-controls={ariaControl}
          key={`tab-key-${i}`}
          sx={{
            textTransform: "none",
            minHeight: 40,
            ...(invalid && {
              color: "error.main",
              outline: "1px solid",
              outlineColor: "error.main",
              outlineOffset: "-6px",
              borderRadius: "8px",
            }),
          }}
        ></Tab>,
      );
    }
    return items;
  }

  // delete the currently selected location type tab
  function onDelete() {
    C().sourceMan.deleteLocationTypeIndex(tabState);
    setTabState(tabState - 1);
    C().mapMan.updateInfoBox();
  }

  // check if the tab at index i is a default location type tab
  function isDefaultTab(i) {
    const defaultLocationType = ["UNKNOWN", "ORIGIN", "VERTIPORT"];
    return defaultLocationType.includes(
      C().sourceMan.locationTypes[i].locationType,
    );
  }

  // reset editable fields to the values of the location type at the given index
  function resetEditableField(index) {
    setLocationType(C().sourceMan.locationTypes[index].locationType);
    setFilter(C().sourceMan.locationTypes[index].filter);
    setColor(C().sourceMan.locationTypes[index].color);
    setUncertainty(C().sourceMan.locationTypes[index].uncertainty);
  }

  // pure function to check if the current location type can be saved
  // checks for non-empty and uniqueness among other location types
  function saveable(locationType, locationTypesExcludeSelf) {
    return !(
      locationType === "" ||
      locationTypesExcludeSelf
        .map((row) => row.locationType)
        .includes(locationType)
    );
  }

  // handle saving edits to the current location type tab
  function onEdit() {
    if (!editMode) {
      resetEditableField(tabState);
      setEditMode(true);
      return;
    }
    // saving edits
    const tabEntry = C().sourceMan.locationTypes[tabState];
    const oldLocationType = tabEntry.locationType;
    const oldColor = tabEntry.color;
    const oldUncertainty = tabEntry.uncertainty;
    const locationTypesExcludeSelf = C().sourceMan.locationTypes.filter(
      (type) => type.id !== tabEntry.id,
    );

    // validate location type and filter before saving
    if (
      !saveable(locationType, locationTypesExcludeSelf) ||
      describeFilter(filter).error !== null
    ) {
      setHighlight(true);
      setTimeout(() => {
        setHighlight(false);
      }, 1000);
      return false;
    }

    // apply changes to map and source manager
    if (oldLocationType !== locationType) {
      C().mapMan.updateLocationType(locationType, oldLocationType);
      if (oldLocationType !== "") {
        C().autoComplete.replace(oldLocationType, locationType);
      } else {
        C().autoComplete.push(locationType);
      }
    }
    if (oldColor != color) {
      C().mapMan.updateLocationTypeColor(locationType, color);
    }
    if (oldUncertainty != uncertainty) {
      C().mapMan.updateUncertainty(locationType, uncertainty);
    }
    C().sourceMan.editLocationType(
      {
        locationType: locationType,
        filter: filter,
        color: color,
        uncertainty: uncertainty,
      },
      tabState,
    );
    C().mapMan.updateInfoBox();
    // refresh the error markers of the bottom bar
    C().updateBottomBar();
    setEditMode(false);
    return true;
  }

  // add a new temporary location type tab and switch to edit mode
  function onAddTab() {
    const index = C().sourceMan.locationTypes.length;
    C().sourceMan.addTempLocationType();
    setTabState(index);
    resetEditableField(index);
    setEditMode(true);
  }

  // handle choosing location type on the map
  function onChoose() {
    if (chooseMode) {
      C().mapMan.removeLocationTypeOnClick();
      setChooseMode(false);
      return;
    }
    const tabEntry = C().sourceMan.locationTypes[tabState];
    const locationTypeEntry = tabEntry.locationType;
    let type = "all";
    if (locationTypeEntry === "ORIGIN") {
      type = "marker";
    } else if (locationTypeEntry === "VERTIPORT") {
      type = "vertiport";
    }
    C().mapMan.setLocationTypeOnClick(
      tabEntry.locationType,
      tabEntry.color,
      tabEntry.uncertainty,
      type,
    );
    setChooseMode(true);
  }

  // render a labeled field of the location type panel
  function field(label, content, size = 6) {
    return (
      <Grid2
        container
        size={size}
        sx={{ color: "white" }}
        justifyContent="flex-start"
        alignItems="center"
        spacing={1}
        wrap="nowrap"
      >
        <Grid2 sx={{ minWidth: 95 }}>
          <Typography variant="body2" sx={{ color: "rgba(255,255,255,0.7)" }}>
            {label}
          </Typography>
        </Grid2>
        <Grid2 sx={{ minWidth: 0 }}>{content}</Grid2>
      </Grid2>
    );
  }

  // render the map filter, as an editable field with examples or as text with its source
  function filterField(i) {
    const locTypes = C().sourceMan.locationTypes;
    const filterLabel = (
      <>
        Map filter
        <Hint title={FILTER_HELP} />
      </>
    );

    // built-in types are only picked on the map
    if (isDefaultTab(i)) {
      return null;
    }

    if (editMode) {
      const { error } = describeFilter(filter);
      return field(
        filterLabel,
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <Autocomplete
            freeSolo
            size="small"
            options={FILTER_EXAMPLES}
            getOptionLabel={(option) =>
              typeof option === "string" ? option : option.filter
            }
            renderOption={(props, option) => (
              <li {...props} key={option.filter}>
                <Box>
                  <Typography variant="body2">{option.label}</Typography>
                  <Typography
                    variant="caption"
                    sx={{ fontFamily: "monospace", opacity: 0.7 }}
                  >
                    {option.filter}
                  </Typography>
                </Box>
              </li>
            )}
            inputValue={filter}
            onInputChange={(event, value) => setFilter(value)}
            sx={{ width: 360 }}
            renderInput={(params) => (
              <TextField
                {...params}
                placeholder="e.g. segment[subtype=road][class=primary]"
                error={error !== null}
                helperText={error ?? undefined}
                slotProps={{
                  input: {
                    ...params.InputProps,
                    sx: { fontFamily: "monospace", fontSize: 13 },
                  },
                }}
              />
            )}
          />
          <SourceChip filter={filter} />
        </Box>,
        12,
      );
    }

    const { error } = describeFilter(locTypes[i].filter);
    const invalid = showErrors && error !== null;
    return field(
      filterLabel,
      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        {locTypes[i].filter !== "" ? (
          <Tooltip title={invalid ? `${error}. Click Edit to fix it.` : ""}>
            <Typography
              variant="body2"
              sx={{
                fontFamily: "monospace",
                ...(invalid && {
                  color: "error.main",
                  border: "1px solid",
                  borderColor: "error.main",
                  borderRadius: "4px",
                  padding: "2px 6px",
                }),
              }}
            >
              {locTypes[i].filter}
            </Typography>
          </Tooltip>
        ) : null}
        <SourceChip filter={locTypes[i].filter} />
      </Box>,
      12,
    );
  }

  // create tab panels based on location types in source manager
  function createTabPanels() {
    const i = tabState;
    const locTypes = C().sourceMan.locationTypes;
    if (i < 0 || i >= locTypes.length) {
      return null;
    }
    const pickTooltip =
      locTypes[i].locationType === "ORIGIN"
        ? "Click markers on the map to make them origins of the mission area"
        : "Click markers, lines or polygons on the map to assign them this type";

    return (
      <TabPanel value={tabState} key={`tab-panel-key-${i}`}>
        {/* Action Buttons */}
        <Grid2 size={12} container justifyContent="flex-start" spacing={1}>
          {!editMode && !chooseMode ? (
            <ActionButton
              icon={<AddCircleOutlineOutlinedIcon />}
              label="New type"
              tooltip="Add a new location type, e.g. for roads or parks"
              onClick={onAddTab}
            />
          ) : null}
          {chooseMode ? null : (
            <ActionButton
              icon={editMode ? <SaveIcon /> : <EditIcon />}
              label={editMode ? "Save" : "Edit"}
              tooltip={
                editMode
                  ? "Save the changes to this location type"
                  : "Change the name, filter, color or uncertainty"
              }
              onClick={onEdit}
            />
          )}
          {editMode ? null : (
            <ActionButton
              icon={chooseMode ? <KeyboardReturnIcon /> : <PanToolAltIcon />}
              label={chooseMode ? "Done picking" : "Pick on map"}
              tooltip={
                chooseMode ? "Stop assigning objects on the map" : pickTooltip
              }
              onClick={onChoose}
            />
          )}
          {isDefaultTab(i) || editMode || chooseMode ? null : (
            <ActionButton
              icon={<DeleteIcon />}
              label="Delete"
              tooltip="Delete this location type"
              onClick={onDelete}
            />
          )}
        </Grid2>

        {/* Tab Content */}
        {field(
          <>
            Name
            <Hint title="Use this name in your rules, e.g. distance(primary)" />
          </>,
          editMode && !isDefaultTab(i) ? (
            <TextField
              size="small"
              variant="outlined"
              value={locationType}
              onChange={(e) => setLocationType(e.target.value)}
              placeholder="e.g. primary"
              helperText={
                highlight ? "Names must be unique and not empty" : undefined
              }
              sx={{ width: 160 }}
              error={highlight}
            />
          ) : (
            <Typography sx={{ fontFamily: "monospace" }}>
              {locTypes[i].locationType}
              {isDefaultTab(i) ? (
                <Hint
                  title={DEFAULT_TYPE_DESCRIPTIONS[locTypes[i].locationType]}
                />
              ) : null}
            </Typography>
          ),
        )}
        {field(
          "Color",
          editMode ? (
            <Box sx={{ width: "175px", marginLeft: "2px" }}>
              <SliderPicker
                width="175px"
                color={color}
                onChange={(color) => {
                  setColor(color.hex);
                }}
              />
            </Box>
          ) : (
            <Paper
              elevation={3}
              sx={{
                width: "20px",
                height: "20px",
                backgroundColor: locTypes[i].color,
                borderStyle: "solid",
                borderWidth: "1px",
                borderColor: "white",
              }}
            ></Paper>
          ),
        )}
        {filterField(i)}
        {field(
          <>
            Uncertainty
            <Hint title="Standard deviation of the random shifts applied to these features, modelling how accurate the map data is" />
          </>,
          editMode ? (
            <TextField
              size="small"
              variant="outlined"
              type="number"
              value={uncertainty}
              onChange={(e) => {
                setUncertainty(e.target.value);
              }}
              slotProps={{ input: { endAdornment: "m" } }}
              sx={{ width: 110 }}
            />
          ) : (
            <Typography>{locTypes[i].uncertainty} m</Typography>
          ),
        )}
      </TabPanel>
    );
  }

  return (
    <Box sx={{ display: "flex", height: 230 }}>
      <Tabs
        orientation="vertical"
        variant="scrollable"
        value={tabState}
        onChange={(event, newValue) => {
          if (editMode) {
            if (onEdit()) {
              setTabState(newValue);
            }
            return;
          }
          if (chooseMode) {
            onChoose();
          }
          setTabState(newValue);
        }}
        sx={{
          borderRight: 1,
          borderColor: "divider",
          color: "white",
          minWidth: 120,
        }}
      >
        {createTabItems()}
      </Tabs>
      {createTabPanels()}
    </Box>
  );
}

LocationTypeSettingTabs.propTypes = {
  showErrors: PropTypes.bool,
};

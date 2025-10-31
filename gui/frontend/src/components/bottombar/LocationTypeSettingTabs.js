import { C } from "../../managers/Core";

import {
  Box,
  Grid2,
  IconButton,
  Paper,
  Tab,
  Tabs,
  TextField,
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
export default function LocationTypeSettingTabs() {
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
  // filter state for managing the osm-filter string of the location type
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

    // validate location type before saving
    if (!saveable(locationType, locationTypesExcludeSelf)) {
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

  // create tab panels based on location types in source manager
  function createTabPanels() {
    const i = tabState;
    const locTypes = C().sourceMan.locationTypes;
    return i > -1 ? (
      <TabPanel value={tabState} key={`tab-panel-key-${i}`}>
        <Grid2 size={12} container justifyContent="flex-start">
          {/* Action Buttons */}
          {!editMode && !chooseMode ? (
            // Add Tab Button
            <Grid2>
              <IconButton
                variant="outlined"
                sx={{
                  width: "20px",
                  height: "20px",
                }}
                onClick={onAddTab}
              >
                <AddCircleOutlineOutlinedIcon />
              </IconButton>
            </Grid2>
          ) : null}
          {chooseMode ? null : (
            // Edit Button
            <Grid2>
              <IconButton
                variant="outlined"
                sx={{
                  width: "20px",
                  height: "20px",
                }}
                onClick={onEdit}
              >
                {editMode ? <SaveIcon /> : <EditIcon />}
              </IconButton>
            </Grid2>
          )}
          {editMode ? null : (
            // Choose Button
            <Grid2>
              <IconButton
                variant="outlined"
                sx={{
                  width: "20px",
                  height: "20px",
                }}
                onClick={onChoose}
              >
                {chooseMode ? <KeyboardReturnIcon /> : <PanToolAltIcon />}
              </IconButton>
            </Grid2>
          )}
          {isDefaultTab(i) || editMode || chooseMode ? null : (
            // Delete Button
            <Grid2>
              <IconButton
                variant="outlined"
                sx={{
                  width: "20px",
                  height: "20px",
                }}
                onClick={onDelete}
              >
                <DeleteIcon />
              </IconButton>
            </Grid2>
          )}
        </Grid2>
        {/* Tab Content */}
        <Grid2 // Location Type Field
          container
          id="location-type-field"
          sx={{
            color: "white",
          }}
          justifyContent="flex-start"
          alignItems="center"
          spacing={1}
          size={6}
        >
          <Grid2>
            <Typography>Location Type:</Typography>
          </Grid2>
          <Grid2>
            {editMode && !isDefaultTab(i) ? (
              <TextField
                size="small"
                variant="outlined"
                value={locationType}
                onChange={(e) => setLocationType(e.target.value)}
                sx={{
                  width: "125px",
                }}
                error={highlight}
              />
            ) : (
              <Typography>{locTypes[i].locationType}</Typography>
            )}
          </Grid2>
        </Grid2>
        <Grid2
          container // Filter Field
          id="Filter-field"
          sx={{
            color: "white",
          }}
          justifyContent="flex-start"
          alignItems="center"
          spacing={1}
          size={6}
        >
          <Grid2>
            <Typography>Filter:</Typography>
          </Grid2>
          <Grid2>
            {editMode && !isDefaultTab(i) ? (
              <TextField
                size="small"
                variant="outlined"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                sx={{
                  width: "125px",
                }}
              />
            ) : (
              <Typography>
                {locTypes[i].filter != "" ? locTypes[i].filter : "Empty"}
              </Typography>
            )}
          </Grid2>
        </Grid2>
        <Grid2 // Color Field
          container
          id="color-field"
          sx={{
            color: "white",
          }}
          justifyContent={"flex-start"}
          alignContent={"center"}
          spacing={1}
          size={6}
        >
          <Grid2>
            <Typography>Color:</Typography>
          </Grid2>
          <Grid2
            container
            justifyContent={"flex-start"}
            alignContent={"center"}
          >
            {editMode ? (
              <Box
                sx={{
                  width: "175px",
                  marginLeft: "2px",
                }}
              >
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
            )}
          </Grid2>
        </Grid2>
        <Grid2
          container // Uncertainty Field
          id="Uncertainty-field"
          sx={{
            color: "white",
          }}
          justifyContent={"flex-start"}
          alignContent={"center"}
          spacing={1}
          size={6}
        >
          <Grid2 justifyContent={"flex-start"} alignContent={"center"}>
            <Typography>Uncertainty:</Typography>
          </Grid2>
          <Grid2>
            {editMode ? (
              <TextField
                size="small"
                variant="outlined"
                value={uncertainty}
                onChange={(e) => {
                  setUncertainty(e.target.value);
                }}
                sx={{
                  width: "125px",
                }}
              />
            ) : (
              <Typography>{locTypes[i].uncertainty}</Typography>
            )}
          </Grid2>
        </Grid2>
      </TabPanel>
    ) : null;
  }

  return (
    <Box sx={{ display: "flex", height: 150 }}>
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

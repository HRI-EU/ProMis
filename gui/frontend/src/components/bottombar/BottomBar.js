import * as React from "react";
import "./BottomBar.css";
import "highlight.js/styles/atom-one-dark.css";
import { C } from "../../managers/Core";
import SourceCodeInterface from "./SourceCodeInterface";
import LandscapeSetting from "./LandscapeSetting";

//MUI elements
import Box from "@mui/material/Box";
import Drawer from "@mui/material/Drawer";
//import Button from "@mui/material/Button";
import LoadingButton from "@mui/lab/LoadingButton";
import Fab from "@mui/material/Fab";
import Grid from "@mui/material/Grid2";
import Alert from "@mui/material/Alert";
import IconButton from "@mui/material/IconButton";
import Collapse from "@mui/material/Collapse";
import Button from "@mui/material/Button";
import Tooltip from "@mui/material/Tooltip";
import Badge from "@mui/material/Badge";
import { ThemeProvider } from "@mui/material";
import { createTheme } from "@mui/material/styles";

//Icon imports
import TerminalIcon from "@mui/icons-material/TerminalRounded";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreRounded from "@mui/icons-material/ExpandMoreRounded";
import PlayCircleIcon from "@mui/icons-material/PlayCircleOutline";
import CloseIcon from "@mui/icons-material/CloseRounded";
import CropFreeIcon from "@mui/icons-material/CropFree";
import CategoryIcon from "@mui/icons-material/CategoryOutlined";
import MapIcon from "@mui/icons-material/Map";
import PolylineIcon from "@mui/icons-material/Polyline";
import PsychologyIcon from "@mui/icons-material/Psychology";
import LocationTypeSettingTabs from "./LocationTypeSettingTabs";
import { describeFilter } from "../../utils/MapFilter";

// explanations of the menus, shown when hovering them
const MENU_HINTS = {
  Rules:
    "The mission rules in Resin. Declare a source for each relation you use, e.g. distance(primary), " +
    'and send the result to target("/landscape").',
  "Mission area": "Where the mission landscape is computed, and how finely.",
  "Map features":
    "The location types your rules refer to, e.g. primary in distance(primary), " +
    "loaded from map data or picked on the map.",
};

const darkTheme = createTheme({
  palette: {
    mode: "dark",
  },
});

/*
  Component for the bootom bar:
    - include states for:
      - drawer like state (top, left, bottom, right)
      - update for external update
      - landscapeSetting for setting tab
      - toogled state for toggling between tab
      - running state for displaying (loading map data, star map and inference state)
    - Main responsibility:
      - Setup child component (LandscapeSetting, LocationTypeSettingTab, SourceCodeInterface)
      - Setting up run call to backend
 */
export default class BottomBar extends React.Component {
  constructor() {
    super();
    this.state = {
      top: false,
      left: false,
      bottom: false,
      right: false,
      update: 0,
      landscapeSetting: {
        origin: "",
        dimensions: ["1024", "1024"],
        resolutions: ["100", "100"],
        supportResolutions: ["25", "25"],
        sampleSize: "25",
        interpolation: "linear",
      },
      runningParamsToggled: false,
      sourceCodeToggled: true,
      locationTabsToggled: false,
      runningState: 0,
      // whether to outline invalid inputs, set when a run is started with invalid inputs
      showErrors: false,
    };
  }

  // the current rules, from the editor if it was opened already
  currentSource = () => {
    const codeEditor = C().getCodeEditor();
    return codeEditor !== null
      ? codeEditor.getValue()
      : C().sourceMan.getSource();
  };

  // check all inputs needed for a run, true marks an invalid or empty input
  validate = () => {
    const setting = this.state.landscapeSetting;
    const isPositive = (value) => value !== "" && Number(value) > 0;
    const isCount = (value) =>
      isPositive(value) && Number.isInteger(Number(value));
    const errors = {
      rules: this.currentSource().trim() === "",
      origin: setting.origin === "",
      dimensions: setting.dimensions.map((value) => !isPositive(value)),
      supportResolutions: setting.supportResolutions.map(
        (value) => !isCount(value),
      ),
      sampleSize: !isCount(setting.sampleSize),
      resolutions: setting.resolutions.map((value) => !isCount(value)),
      mapFeatures: C().sourceMan.locationTypes.some(
        (entry) => describeFilter(entry.filter).error !== null,
      ),
    };
    errors.missionArea =
      errors.origin ||
      errors.sampleSize ||
      [
        ...errors.dimensions,
        ...errors.supportResolutions,
        ...errors.resolutions,
      ].some(Boolean);
    errors.any = errors.rules || errors.missionArea || errors.mapFeatures;
    return errors;
  };

  inputSize = 100;

  // function to update the UI through core call
  updateUI = () => {
    this.setState({ update: this.state.update + 1 });
    // check origin, and choose it when there is only one origin marker
    const markers = C().mapMan.listOriginMarkers();
    const markersName = markers.map(
      (marker) => marker.feature.properties["name"],
    );
    if (markersName.indexOf(this.state.landscapeSetting.origin) === -1) {
      this.setState({
        landscapeSetting: {
          ...this.state.landscapeSetting,
          origin: markersName.length === 1 ? markersName[0] : "",
        },
      });
    }
    //console.log("updateUI()! " + this.state.update);
  };

  // function to toggle the drawer
  toggleDrawer = (anchor, open) => (event) => {
    if (
      event.type === "keydown" &&
      (event.key === "Tab" || event.key === "Shift")
    ) {
      return;
    }

    this.setState({ ...this.state, [anchor]: open });
    // reset the toggled states when the bottom bar is closed so that choosing action is reset
    if (!open) {
      // set all toggled states to false
      this.setState({
        runningParamsToggled: false,
        locationTabsToggled: false,
        sourceCodeToggled: false,
      });
    } else {
      // set source code to be toggled by default
      this.setState({
        runningParamsToggled: false,
        locationTabsToggled: false,
        sourceCodeToggled: true,
      });
    }
  };

  // Toggle the running state of the source code
  toggleRun = async () => {
    // check all inputs, and outline the invalid ones until they are fixed
    const errors = this.validate();
    if (errors.any) {
      const panels = [
        ["sourceCodeToggled", errors.rules],
        ["runningParamsToggled", errors.missionArea],
        ["locationTabsToggled", errors.mapFeatures],
      ];
      // stay on the opened menu if it has errors, otherwise open the first one with errors
      const opened = panels.find(([key]) => this.state[key]);
      const [panel] =
        opened !== undefined && opened[1]
          ? opened
          : panels.find(([, hasErrors]) => hasErrors);
      this.setState({
        showErrors: true,
        sourceCodeToggled: panel === "sourceCodeToggled",
        runningParamsToggled: panel === "runningParamsToggled",
        locationTabsToggled: panel === "locationTabsToggled",
      });
      return;
    }
    const sourceCode = this.currentSource();
    // set running state to loading map data
    this.setState({ runningState: 1, showErrors: false });

    // prepare the run parameters
    let runParam = {
      origin: this.state.landscapeSetting.origin,
      sourceCode: sourceCode,
      dimensions: this.state.landscapeSetting.dimensions,
      resolutions: this.state.landscapeSetting.resolutions,
      supportResolutions: this.state.landscapeSetting.supportResolutions,
      sampleSize: this.state.landscapeSetting.sampleSize,
      interpolation: this.state.landscapeSetting.interpolation,
    };

    // call the backend to run the source code
    try {
      const mapHashData = await C().sourceMan.intermediateCalls(
        runParam,
        "loadmapdata",
      );
      // the backend names its cached results by hashes, returned as JSON strings
      const mapHashValue = JSON.parse(mapHashData);
      this.setState({ runningState: 2 });
      const starmapHashData = await C().sourceMan.intermediateCalls(
        runParam,
        "starmap",
        mapHashValue,
      );
      const starmapHashValue = JSON.parse(starmapHashData);
      this.setState({ runningState: 3 });
      await C().sourceMan.intermediateCalls(
        runParam,
        "inference",
        starmapHashValue,
      );
      this.setState({ runningState: 0 });
    } catch (error) {
      console.error(error.message);
    }
  };

  // function to toggle running parameters tab
  toggleRunningParams = () => {
    // if the location type setting is toggled, close it
    if (this.state.locationTabsToggled) {
      this.setState({ locationTabsToggled: false });
    }
    // if the source code is toggled, close it
    if (this.state.sourceCodeToggled) {
      this.setState({ sourceCodeToggled: false });
    }
    // toggle the running parameters
    this.setState({ runningParamsToggled: !this.state.runningParamsToggled });
  };

  // function to toggle source code tab
  toggleSourceCode = () => {
    // if the location type setting is toggled, close it
    if (this.state.locationTabsToggled) {
      this.setState({ locationTabsToggled: false });
    }
    // if the running parameters is toggled, close it
    if (this.state.runningParamsToggled) {
      this.setState({ runningParamsToggled: false });
    }
    // toggle the source code
    this.setState({ sourceCodeToggled: !this.state.sourceCodeToggled });
  };

  // function to toggle location type tab
  toggleLocationTabs = () => {
    // if the running parameters is toggled, close it
    if (this.state.runningParamsToggled) {
      this.setState({ runningParamsToggled: false });
    }
    // if the source code is toggled, close it
    if (this.state.sourceCodeToggled) {
      this.setState({ sourceCodeToggled: false });
    }

    this.setState({ locationTabsToggled: !this.state.locationTabsToggled });
  };

  // function to get running icons based on state
  getRunningIcons = (state) => {
    if (state > 3 || state < 0) {
      throw new Error("Invalid state");
    }
    const playCircle = <PlayCircleIcon style={{ color: "#ffffff" }} />;
    const mapIcon = <MapIcon style={{ color: "#ffffff" }} />;
    const polylineIcon = <PolylineIcon style={{ color: "#ffffff" }} />;
    const psychologyIcon = <PsychologyIcon style={{ color: "#ffffff" }} />;
    const icons = [playCircle, mapIcon, polylineIcon, psychologyIcon];
    return icons[state];
  };

  // function to get running labels based on state
  getRunningLabels = (state) => {
    if (state > 3 || state < 0) {
      throw new Error("Invalid state");
    }
    const labels = [
      "Run",
      "Loading Map Data",
      "Calculating StarMap",
      "Inference",
    ];
    return labels[state];
  };

  // function to handle landscape setting edit, passed to LandscapeSetting component
  landscapeEdit = (landscapeSetting) => {
    this.setState({
      landscapeSetting: {
        ...landscapeSetting,
      },
    });
  };

  // labeled button to switch between the menus of the bottom bar
  menuButton = (label, icon, active, onClick, ariaLabel, hasErrors) => (
    <Grid>
      <Tooltip title={MENU_HINTS[label]}>
        <Button
          onClick={onClick}
          startIcon={
            <Badge
              variant="dot"
              color="error"
              invisible={!(this.state.showErrors && hasErrors)}
            >
              {icon}
            </Badge>
          }
          aria-label={ariaLabel}
          size="small"
          sx={{
            color: active ? "#ffffff" : "#ffffff99",
            textTransform: "none",
            borderRadius: "16px",
            backgroundColor: active ? "#7e86bd33" : "transparent",
            "&:hover": { backgroundColor: "#7e86bd22" },
          }}
        >
          {label}
        </Button>
      </Tooltip>
    </Grid>
  );

  runningParams = (errors) => (
    <ThemeProvider theme={darkTheme}>
      <LandscapeSetting
        {...this.state.landscapeSetting}
        errors={this.state.showErrors ? errors : null}
        onEdit={this.landscapeEdit}
      />
    </ThemeProvider>
  );

  // panel that will appear when the bottom bar is clicked
  list = (errors) => (
    <Box
      role="presentation"
      style={{
        backgroundColor: "#0D0F21",
        height: "100%",
        borderRadius: "24px 24px 0px 0px",
        overflowY: "hidden",
        overflowX: "hidden",
        width: "100%",
        marginLeft: "auto",
        marginRight: "auto",
        scrollbarWidth: "none",
        msOverflowStyle: "none",
      }}
    >
      <Grid
        container
        spacing={0}
        direction="column"
        alignItems="start"
        justifyContent="start"
        m={0}
        sx={{ display: "flex" }}
      >
        <Grid // contains menu buttons for source, landscape settings, location type and run interface
          container
          spacing={0}
          direction="row"
          alignItems="center"
          justifyContent="start"
          m={0}
          style={{
            paddingTop: "10px",
            paddingLeft: "32px",
            PaddingRight: "32px",
          }}
          size={12}
        >
          <Grid
            container
            spacing={1}
            direction="row"
            alignItems="center"
            justifyContent="start"
            m={0}
            size={8}
          >
            {this.menuButton(
              "Rules",
              <TerminalIcon />,
              this.state.sourceCodeToggled,
              this.toggleSourceCode,
              "Open source editor menu",
              errors.rules,
            )}
            {this.menuButton(
              "Mission area",
              <CropFreeIcon />,
              this.state.runningParamsToggled,
              this.toggleRunningParams,
              "Open landscape setting menu",
              errors.missionArea,
            )}
            {this.menuButton(
              "Map features",
              <CategoryIcon />,
              this.state.locationTabsToggled,
              this.toggleLocationTabs,
              "Open location type menu",
              errors.mapFeatures,
            )}
          </Grid>

          <Grid // contains run button
            container
            spacing={0}
            direction="row"
            alignItems="center"
            justifyContent="flex-end"
            size={4}
            style={{
              paddingRight: "32px",
            }}
          >
            <Collapse
              in={!C().sourceMan.closed}
              collapsedSize={0}
              orientation="horizontal"
            >
              <Alert // alert for success or error after running
                severity={C().sourceMan.success ? "success" : "error"}
                style={{
                  minWidth: "80px",
                  marginLeft: "30px",
                }}
                sx={{
                  padding: "3px 10px 3px 10px",
                }}
                variant="filled"
                action={
                  <IconButton
                    aria-label="close"
                    color="inherit"
                    size="small"
                    onClick={() => {
                      C().sourceMan.closeAlert();
                      if (!C().sourceMan.success) {
                        this.setState({ runningState: 0 });
                      }
                    }}
                  >
                    <CloseIcon fontSize="inherit" />
                  </IconButton>
                }
              >
                {C().sourceMan.success ? "Success" : "Error"}
              </Alert>
            </Collapse>

            <ThemeProvider theme={darkTheme}>
              <Tooltip title="Loads the map features, estimates the spatial relations of your rules and computes the mission landscape">
                <span>
                  <LoadingButton // run button
                    loading={this.state.runningState !== 0}
                    loadingPosition="start"
                    startIcon={this.getRunningIcons(this.state.runningState)}
                    onClick={this.toggleRun}
                    variant="outlined"
                    size="small"
                    sx={{
                      color: "#ffffff",
                      borderColor: "#7e86bd22",
                      borderRadius: "24px",
                    }}
                  >
                    {this.getRunningLabels(this.state.runningState)}
                  </LoadingButton>
                </span>
              </Tooltip>
              <Tooltip title="Hide panel">
                <IconButton // collapse button
                  aria-label="Hide panel"
                  onClick={this.toggleDrawer("bottom", false)}
                  size="small"
                  style={{ color: "#ffffff", marginLeft: "8px" }}
                >
                  <ExpandMoreRounded />
                </IconButton>
              </Tooltip>
            </ThemeProvider>
          </Grid>
        </Grid>

        {
          // logic to display landscape settings
          this.state.runningParamsToggled ? this.runningParams(errors) : null
        }

        {
          // logic to display source editor menu
          this.state.sourceCodeToggled ? (
            <SourceCodeInterface showErrors={this.state.showErrors} />
          ) : null
        }

        {
          // logic to display source editor menu
          this.state.locationTabsToggled ? (
            <ThemeProvider theme={darkTheme}>
              <LocationTypeSettingTabs showErrors={this.state.showErrors} />
            </ThemeProvider>
          ) : null
        }
      </Grid>
    </Box>
  );

  render() {
    //Update reference
    C().addRefBottomBar(this.updateUI);

    return (
      <div
        style={{
          position: "absolute",
          bottom: 4,
          width: "100%",
          marginLeft: "auto",
          marginRight: "auto",
        }}
      >
        <Fab
          variant="extended"
          aria-label="add"
          onClick={this.toggleDrawer("bottom", true)}
          style={{
            color: "#ffffff",
            backgroundColor: "#0D0F21",
            width: "100px",
          }}
        >
          <ExpandLessIcon />
        </Fab>

        <React.Fragment key={"bottom"}>
          <Drawer
            variant="persistent"
            anchor={"bottom"}
            open={this.state["bottom"]}
            onClose={this.toggleDrawer("bottom", false)}
            PaperProps={{
              elevation: 2,
              square: false,
              style: {
                backgroundColor: "transparent",
                width: "50%",
                borderRadius: "24px 24px 0px 0px",
                marginLeft: "auto",
                marginRight: "auto",
              },
            }}
          >
            {this.list(this.validate())}
          </Drawer>
        </React.Fragment>
      </div>
    );
  }
}

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
import { ThemeProvider } from "@mui/material";
import { createTheme } from "@mui/material/styles";

//Icon imports
import TerminalIcon from "@mui/icons-material/TerminalRounded";
import TerminalTwoToneIcon from "@mui/icons-material/TerminalTwoTone";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreRounded from "@mui/icons-material/ExpandMoreRounded";
import PlayCircleIcon from "@mui/icons-material/PlayCircleOutline";
import CloseIcon from "@mui/icons-material/CloseRounded";
import FormatListBulletedIcon from "@mui/icons-material/FormatListBulleted";
import ListAltOutlinedIcon from "@mui/icons-material/ListAltOutlined";
import MapIcon from "@mui/icons-material/Map";
import PolylineIcon from "@mui/icons-material/Polyline";
import PsychologyIcon from "@mui/icons-material/Psychology";
import CalendarViewMonthIcon from "@mui/icons-material/CalendarViewMonth";
import CalendarViewMonthTwoToneIcon from "@mui/icons-material/CalendarViewMonthTwoTone";
import LocationTypeSettingTabs from "./LocationTypeSettingTabs";

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
    };
  }

  highlightOriginElement = false;
  highlightSourceElement = false;

  inputSize = 100;

  // function to update the UI through core call
  updateUI = () => {
    this.setState({ update: this.state.update + 1 });
    // check origin
    const markers = C().mapMan.listOriginMarkers();
    const markersName = markers.map(
      (marker) => marker.feature.properties["name"],
    );
    if (markersName.indexOf(this.state.landscapeSetting.origin) === -1) {
      this.setState({
        landscapeSetting: {
          ...this.state.landscapeSetting,
          origin: "",
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
    // check if source code is available
    const sourceCode = C().getCodeEditor().getValue();
    if (sourceCode === "") {
      // toggle source code and hide running params and location type
      this.setState({
        sourceCodeToggled: true,
        runningParamsToggled: false,
        locationTabsToggled: false,
      });
      this.highlightSourceElement = true;
      this.updateUI();
      setTimeout(() => {
        this.highlightSourceElement = false;
        this.updateUI();
      }, 1000);
      return;
    }
    // check if origin is set
    if (this.state.landscapeSetting.origin === "") {
      this.highlightOriginElement = true;
      // toggle running params to show origin
      this.setState({
        runningParamsToggled: true,
        locationTabsToggled: false,
        sourceCodeToggled: false,
      });

      this.updateUI();
      setTimeout(() => {
        this.highlightOriginElement = false;
        this.updateUI();
      }, 1000);
      return;
    }
    // set running state to loading map data
    this.setState({ runningState: 1 });

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
      const mapHashValue = Number(mapHashData);
      this.setState({ runningState: 2 });
      const starmapHashData = await C().sourceMan.intermediateCalls(
        runParam,
        "starmap",
        mapHashValue,
      );
      const starmapHashValue = Number(starmapHashData);
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

  runningParams = () => (
    <ThemeProvider theme={darkTheme}>
      <LandscapeSetting
        {...this.state.landscapeSetting}
        highlightOriginElement={this.highlightOriginElement}
        onEdit={this.landscapeEdit}
      />
    </ThemeProvider>
  );

  // panel that will appear when the bottom bar is clicked
  list = () => (
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
            size={4}
          >
            <Grid size={2}>
              <IconButton // source editor expand button
                onClick={() => {
                  this.toggleSourceCode();
                }}
                style={{ color: "#eeeeee", fontSize: 12 }}
                aria-label="Open source editor menu"
              >
                {this.state.sourceCodeToggled ? (
                  <TerminalTwoToneIcon />
                ) : (
                  <TerminalIcon />
                )}
              </IconButton>
            </Grid>

            <Grid size={2}>
              <IconButton // landscape setting expand button
                onClick={() => {
                  this.toggleRunningParams();
                }}
                style={{ color: "#eeeeee", fontSize: 12 }}
                aria-label="Open landscape setting menu"
              >
                {this.state.runningParamsToggled ? (
                  <CalendarViewMonthTwoToneIcon />
                ) : (
                  <CalendarViewMonthIcon />
                )}
              </IconButton>
            </Grid>

            <Grid size={2}>
              <IconButton // location type menu expand button
                onClick={() => {
                  this.toggleLocationTabs();
                }}
                style={{ color: "#eeeeee", fontSize: 12 }}
                aria-label="Open location type menu"
              >
                {this.state.locationTabsToggled ? (
                  <ListAltOutlinedIcon />
                ) : (
                  <FormatListBulletedIcon />
                )}
              </IconButton>
            </Grid>
          </Grid>

          <Grid // contains run button
            container
            spacing={0}
            direction="row"
            alignItems="center"
            justifyContent="flex-end"
            size={8}
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
            </ThemeProvider>
          </Grid>
        </Grid>

        {
          // logic to display landscape settings
          this.state.runningParamsToggled ? this.runningParams() : null
        }

        {
          // logic to display source editor menu
          this.state.sourceCodeToggled ? (
            <SourceCodeInterface
              highlightSourceElement={this.highlightSourceElement}
            />
          ) : null
        }

        {
          // logic to display source editor menu
          this.state.locationTabsToggled ? (
            <ThemeProvider theme={darkTheme}>
              <LocationTypeSettingTabs />
            </ThemeProvider>
          ) : null
        }
      </Grid>

      <IconButton // collapse button
        aria-label="add"
        onClick={this.toggleDrawer("bottom", false)}
        style={{
          color: "#ffffff",
          backgroundColor: "#0D0F21",
          border: "1px solid #7e86bd22",
          width: "100px",
          borderRadius: "24px",
          position: "absolute",
          top: "3px",
          left: "45%",
        }}
      >
        <ExpandMoreRounded />
      </IconButton>
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
            {this.list("bottom")}
          </Drawer>
        </React.Fragment>
      </div>
    );
  }
}

import * as React from "react";
import "./BottomBar.css";
import "highlight.js/styles/atom-one-dark.css";
import { C } from "../../managers/Core";
import LocationTypeSetting from "./LocationTypeSetting";
import SourceCodeInterface from "./SourceCodeInterface";
import LandscapeSetting from "./LandscapeSetting";

//MUI elements
import Box from "@mui/material/Box";
import Drawer from "@mui/material/Drawer";
import Button from "@mui/material/Button";
import LoadingButton from '@mui/lab/LoadingButton';
import Fab from "@mui/material/Fab";
import Grid from "@mui/material/Grid2";
import Alert from "@mui/material/Alert";
import IconButton from '@mui/material/IconButton';
import Collapse from "@mui/material/Collapse";
import { ThemeProvider } from "@mui/material";
import { createTheme } from "@mui/material/styles";


//Icon imports
import TerminalIcon from "@mui/icons-material/TerminalRounded";
import TerminalTwoToneIcon from '@mui/icons-material/TerminalTwoTone';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreRounded from "@mui/icons-material/ExpandMoreRounded";
import PlayCircleIcon from "@mui/icons-material/PlayCircleOutline";
import CloseIcon from "@mui/icons-material/CloseRounded";
import FormatListBulletedIcon from '@mui/icons-material/FormatListBulleted';
import ListAltOutlinedIcon from '@mui/icons-material/ListAltOutlined';
import MapIcon from '@mui/icons-material/Map';
import PolylineIcon from '@mui/icons-material/Polyline';
import PsychologyIcon from '@mui/icons-material/Psychology';
import CalendarViewMonthIcon from '@mui/icons-material/CalendarViewMonth';
import CalendarViewMonthTwoToneIcon from '@mui/icons-material/CalendarViewMonthTwoTone';


const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
});

const defaultSourceCode = `% UAV properties
initial_charge ~ normal(90, 5).
charge_cost ~ normal(-0.1, 0.2).
weight ~ normal(0.2, 0.1).

% Weather conditions
1/10::fog; 9/10::clear.

% Visual line of sight
0.8::vlos(X) :- 
    fog, distance(X, operator) < 50;
    clear, distance(X, operator) < 100;
    clear, over(X, bay), distance(X, operator) < 400.

% Sufficient charge to return to operator
can_return(X) :-
    B is initial_charge, O is charge_cost,
    D is distance(X, operator), 0 < B + (2 * O * D).

% Permits related to local features
permits(X) :- 
    distance(X, service) < 15; 
    distance(X, primary) < 15;
    distance(X, secondary) < 10; 
    distance(X, tertiary) < 5;
    distance(X, rail) < 5; 
    distance(X, crossing) < 5; 
    over(X, park).

% Definition of a valid mission
landscape(X) :- 
    vlos(X), weight < 25, can_return(X); 
    permits(X), can_return(X).
`;


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
        interpolation: "linear"
      },
      runningParamsToggled: false,
      locationTypeToggled: false,
      sourceCodeToggled: true,
      runningState: 0,
      sourceCode: defaultSourceCode
    };
  }

  highlightOriginElement = false;
  highlightSourceElement = false;

  inputSize = 100;

  // function to update the UI
  updateUI = () => {
    this.setState({ update: this.state.update + 1 });
    // check origin
    const markers = C().mapMan.listOriginMarkers();
    const markersName = markers.map((marker) => marker.feature.properties["name"]);
    if (markersName.indexOf(this.state.landscapeSetting.origin) === -1) {
      this.setState({
        landscapeSetting: {
          ...this.state.landscapeSetting,
          origin: ""
        }
      })
    }
    //console.log("updateUI()! " + this.state.update);
  };

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
      this.setState({ runningParamsToggled: false, locationTypeToggled: false, sourceCodeToggled: false });
    }else {
      // set source code to be toggled by default
      this.setState({ runningParamsToggled: false, locationTypeToggled: false, sourceCodeToggled: true });
    }
  };

  // Toggle the running state of the source code
  toggleRun = async () => {
    // check if source code is available
    if (this.state.sourceCode === "") {
      // toggle source code and hide running params and location type
      this.setState({ sourceCodeToggled: true, runningParamsToggled: false, locationTypeToggled: false });
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
      this.setState({ runningParamsToggled: true, locationTypeToggled: false, sourceCodeToggled: false });

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
      sourceCode: this.state.sourceCode,
      dimensions: this.state.landscapeSetting.dimensions,
      resolutions: this.state.landscapeSetting.resolutions,
      supportResolutions: this.state.landscapeSetting.supportResolutions,
      sampleSize: this.state.landscapeSetting.sampleSize,
      interpolation: this.state.landscapeSetting.interpolation
    };
    
    // call the backend to run the source code
    try {
      const mapHashData = await C().sourceMan.intermediateCalls(runParam, "loadmapdata");
      const mapHashValue = Number(mapHashData);
      this.setState({ runningState: 2 });
      const starmapHashData = await C().sourceMan.intermediateCalls(runParam, "starmap", mapHashValue);
      const starmapHashValue = Number(starmapHashData);
      this.setState({ runningState: 3 });
      await C().sourceMan.intermediateCalls(runParam, "inference", starmapHashValue);
      this.setState({ runningState: 0 });
    }
    catch (error) {
      console.error(error.message);
    }


    // only for testing purposes
    //this.setState({ runningState: (this.state.runningState + 1) % 4 });
  };

  toggleRunningParams = () => {
    // if the location type setting is toggled, close it
    if (this.state.locationTypeToggled) {
      this.setState({ locationTypeToggled: false });
    }
    // if the source code is toggled, close it
    if (this.state.sourceCodeToggled) {
      this.setState({ sourceCodeToggled: false });
    }
    // toggle the running parameters
    this.setState({ runningParamsToggled: !this.state.runningParamsToggled });
  }

  toggleLocationType = () => {
    // if the running parameters is toggled, close it
    if (this.state.runningParamsToggled) {
      this.setState({ runningParamsToggled: false });
    }
    // if the source code is toggled, close it
    if (this.state.sourceCodeToggled) {
      this.setState({ sourceCodeToggled: false });
    }
    // toggle the location type setting
    this.setState({ locationTypeToggled: !this.state.locationTypeToggled });
  }

  toggleSourceCode = () => {
    // if the location type setting is toggled, close it
    if (this.state.locationTypeToggled) {
      this.setState({ locationTypeToggled: false });
    }
    // if the running parameters is toggled, close it
    if (this.state.runningParamsToggled) {
      this.setState({ runningParamsToggled: false });
    }
    // toggle the source code
    this.setState({ sourceCodeToggled: !this.state.sourceCodeToggled });
  }

  

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
  }

  getRunningLabels = (state) => {
    if (state > 3 || state < 0) {
      throw new Error("Invalid state");
    }
    const labels = ["Run", "Loading Map Data", "Calculating StarMap", "Inference"];
    return labels[state];
  }

  landscapeEdit = (landscapeSetting) => {
    this.setState({landscapeSetting: {
      ...landscapeSetting
    }});
  }

  runningParams = () => (
    <ThemeProvider theme={darkTheme}>
      <LandscapeSetting 
        {...this.state.landscapeSetting}
        highlightOriginElement={this.highlightOriginElement}
        onEdit={this.landscapeEdit}
      />
    </ThemeProvider>
  )


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
        <Grid
          size={12}
        >
          <Button // collapse button
            aria-label="add"
            onClick={this.toggleDrawer("bottom", false)}
            style={{
              color: "#ffffff",
              backgroundColor: "#0D0F21",
              border: "1px solid #7e86bd22",
              width: "100px",
              borderRadius: "24px",
              marginTop: "6px",
            }}
          >
            <ExpandMoreRounded />
          </Button>
        </Grid>

        <Grid // contains menu buttons for source, landscape settings, location type and run interface
          container
          spacing={0}
          direction="row"
          alignItems="center"
          justifyContent="start"
          m={0}
          style={{ 
            marginLeft: "32px",
            marginRight: "32px",
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
            size={6}
          >
            <Grid
              size={1}
            >
              <IconButton // source editor expand button
                onClick={() => {
                  this.toggleSourceCode();
                }}
                style={{ color: "#eeeeee", fontSize: 12}}
                aria-label="Open source editor menu"
              >
                {this.state.sourceCodeToggled ? (
                  <TerminalTwoToneIcon />
                ) : (
                  <TerminalIcon />
                )}
              </IconButton>
            </Grid>
            
            <Grid
              size={1}
            >
              <IconButton // landscape setting expand button
                onClick={() => {
                  this.toggleRunningParams();
                }}
                style={{ color: "#eeeeee", fontSize: 12}}
                aria-label="Open landscape setting menu"
              >
                {this.state.runningParamsToggled ? (
                  <CalendarViewMonthTwoToneIcon  />
                ) : (
                  <CalendarViewMonthIcon />
                )}
              </IconButton>
            </Grid>

            <Grid size={1}> 
              <IconButton // location type menu expand button
                onClick={() => {
                  this.toggleLocationType();
                }}
                style={{ color: "#eeeeee", fontSize: 12 }}
                aria-label="Open location type menu"
              >
                {this.state.locationTypeToggled ? (
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
            size={5}
            style={{ 
             }}
          >
            <Collapse in={!C().sourceMan.closed}
              collapsedSize={0}
              orientation="horizontal"  
            >
              <Alert 
                severity={C().sourceMan.success ? "success" : "error"}
                style={{
                  minWidth: "80px",
                  marginLeft: "30px",
                }}
                sx={{
                  padding: "3px 10px 3px 10px",
                }}
                variant='filled'
                action={
                  <IconButton
                    aria-label="close"
                    color="inherit"
                    size="small"
                    onClick={() => {
                      C().sourceMan.closeAlert()
                      if (!C().sourceMan.success){
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
              <LoadingButton
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
          // logic to display location type settings
          this.state.locationTypeToggled ?
            <Grid
              container
              spacing={0}
              direction="row"
              alignItems="center"
              justifyContent="start"
              m={0}
              sx={{ 
                width: "100%",
                display: "flex",
                paddingLeft: "32px",
                paddingRight: "32px",
               }}
            >
              <ThemeProvider theme={darkTheme}>
                <LocationTypeSetting 
                  initialRows={C().sourceMan.locationTypes}
                />
              </ThemeProvider>
            </Grid> : null
        }

        {
          // logic to display source editor menu
          this.state.sourceCodeToggled ?
        
          <SourceCodeInterface 
            sourceCode={this.state.sourceCode}
            onEdit={(value) => this.setState({sourceCode: value})}
            highlightSourceElement={this.highlightSourceElement}
          />
          : null
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
                width: "60%",
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

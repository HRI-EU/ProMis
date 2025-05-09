import * as React from "react";
import "./BottomBar.css";
import hljs from "highlight.js";
import "highlight.js/styles/atom-one-dark.css";
import { C } from "../managers/Core";
import LocationTypeSetting from "./LocationTypeSetting";

//MUI elements
import Box from "@mui/material/Box";
import Drawer from "@mui/material/Drawer";
import Button from "@mui/material/Button";
import LoadingButton from '@mui/lab/LoadingButton';
import Fab from "@mui/material/Fab";
import Grid from "@mui/material/Grid2";
import Chip from "@mui/material/Chip";
import Alert from "@mui/material/Alert";
import IconButton from '@mui/material/IconButton';
import Collapse from "@mui/material/Collapse";
import { FormControl, InputLabel, MenuItem, ThemeProvider } from "@mui/material";
import { createTheme } from "@mui/material/styles";
import TextField from "@mui/material/TextField";
import EditIcon from '@mui/icons-material/Edit';
import DoneIcon from '@mui/icons-material/Done';

//Icon imports
import TerminalIcon from "@mui/icons-material/TerminalRounded";
import TerminalTwoToneIcon from '@mui/icons-material/TerminalTwoTone';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreRounded from "@mui/icons-material/ExpandMoreRounded";
import PlayCircleIcon from "@mui/icons-material/PlayCircleOutline";
import FileUploadIcon from "@mui/icons-material/FileUploadOutlined";
import CloseIcon from "@mui/icons-material/CloseRounded";
import FormatListBulletedIcon from '@mui/icons-material/FormatListBulleted';
import ListAltOutlinedIcon from '@mui/icons-material/ListAltOutlined';
import MapIcon from '@mui/icons-material/Map';
import PolylineIcon from '@mui/icons-material/Polyline';
import PsychologyIcon from '@mui/icons-material/Psychology';
import CalendarViewMonthIcon from '@mui/icons-material/CalendarViewMonth';
import CalendarViewMonthTwoToneIcon from '@mui/icons-material/CalendarViewMonthTwoTone';
import { Select } from "@mui/material";

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
});


export default class BottomBar extends React.Component {
  constructor() {
    super();
    this.state = {
      top: false,
      left: false,
      bottom: false,
      right: false,
      update: 0,
      dimensionWidth: 1024,
      dimensionHeight: 1024,
      resolutionWidth: 100,
      resolutionHeight: 100,
      runningParamsToggled: false,
      locationTypeToggled: false,
      sourceCodeToggled: true,
      supportResolutionWidth: 25,
      supportResolutionHeight: 25,
      sampleSize: 25,
      runningState: 0,
    };
  }

  highlightOriginElement = false;
  highlightSourceElement = false;

  inputSize = 100;

  // Create a reference to the code element
  codeRef = React.createRef(null);

  // Create a reference to the hidden file input element
  hiddenFileInput = React.createRef(null);


  // to handle the user-selected file
  handleChange = (event) => {
    if (event.target.files.length === 0) {
      return;
    }
    const file = event.target.files[0];
    const fileReader = new FileReader(file);
    fileReader.onloadend = () => {
      C().sourceMan.importSource(fileReader.result);
    };
    fileReader.readAsText(file);
  };

  // reset the file input to allow the same file to be uploaded again
  componentDidMount() {
    if (this.hiddenFileInput.current) {
      this.hiddenFileInput.current.setAttribute("onclick", "this.value=null;");
    }
  }

  // Highlight the code when the component updates
  componentDidUpdate() {
    if (this.codeRef.current === null) {
      return;
    }
    
    this.codeRef.current.removeAttribute("data-highlighted");
    hljs.highlightAll(this.codeRef.current);
    //console.log("highlighted");
  }

  // function to update the UI
  updateUI = () => {
    this.setState({ update: this.state.update + 1 });
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
    if (!C().sourceMan.hasSource) {
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
    if (C().sourceMan.origin === "") {
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
      dimensionWidth: this.state.dimensionWidth,
      dimensionHeight: this.state.dimensionHeight,
      resolutionWidth: this.state.resolutionWidth,
      resolutionHeight: this.state.resolutionHeight,
      supportResolutionWidth: this.state.supportResolutionWidth,
      supportResolutionHeight: this.state.supportResolutionHeight,
      sampleSize: this.state.sampleSize,
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

  // Toggle the file input
  toggleFile = () => {
    if (C().sourceMan.hasSource) {
      C().sourceMan.removeSource();
      return;
    }
    this.hiddenFileInput.current.click();
  };

  updateEditor = (e) => {
    // update the source code
    C().sourceMan.importSource(e.target.value);
  }

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


  editorValue = () => {
    if (!C().sourceMan.hasSource) {
      return "No Model";
    }
    if (C().sourceMan.source.slice(-2) == "\n ") {
      return C().sourceMan.source.slice(0, -1);
    }
    return C().sourceMan.source;
  }

  checkTab = (element, event) => {
    let code = element.value;
    if(event.key == "Tab") {
      /* Tab key pressed */
      event.preventDefault(); // stop normal
      let before_tab = code.slice(0, element.selectionStart); // text before tab
      let after_tab = code.slice(element.selectionEnd, element.value.length); // text after tab
      let cursor_pos = element.selectionStart + 1; // where cursor moves after tab - moving forward by 1 char to after tab
      element.value = before_tab + "\t" + after_tab; // add tab char
      // move cursor
      element.selectionStart = cursor_pos;
      element.selectionEnd = cursor_pos;
      C().sourceMan.importSource(element.value); // Update text to include indent
    }
  }

  createSelectItems = () => {
    let items = [];
    const markers = C().mapMan.listOriginMarkers();
    for (let i = 0; i < markers.length; i++) {
      items.push(
        <MenuItem key={i + 1} value={markers[i].feature.properties["name"]}>
          {markers[i].feature.properties["name"]}
        </MenuItem>
      );
    }
    return items;
  }
  createInterpolationItems = () => {
    let items = ["linear", "nearest", "gaussian_process"];
    return items.map((item, index) => {
      return <MenuItem key={index} value={item}>{item}</MenuItem>
    });
  };

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

  handleOriginChange = (event) => {
    C().sourceMan.updateOrigin(event.target.value);
    // get marker with this origin name
    const latLon = C().mapMan.latlonFromMarkerName(event.target.value);
    // recenter map
    C().mapMan.recenterMap(latLon);
  }

  handleInterpolationChange = (event) => {
    C().sourceMan.updateInterpolation(event.target.value);
  }

  runningParams = () => (
    <ThemeProvider theme={darkTheme}>
    <Grid
      container
      spacing={2}
      direction="column"
      alignItems="start"
      justifyContent="center"
      m={1}
      style={{ marginLeft: "38px", width: "90%" }}
    >
      <Grid
        container
        item
        size={12}
        direction="row"
        justifyContent="start"
        alignItems="center"
        spacing={2}
      >
        
        <Grid
          container
          item
          size={4}
        >
          <FormControl sx={{minWidth: 125}} size="small" error={this.highlightOriginElement}>
            <InputLabel
              style={{ color: "#ffffff" }}
            >Origin</InputLabel>
            <Select
              label="Origin"
              variant="outlined"
              value={C().sourceMan.origin}
              onChange={this.handleOriginChange}
            >
              {this.createSelectItems()}
            </Select>
          </FormControl>
        </Grid>
        
        <Grid
          container
          item
          direction="row"
          justifyContent="start"
          alignItems="center"
          spacing={0}
          size={4}
        >
          <Grid
            item
          >
          <TextField type="number" size="small" label="Width" variant="outlined" 
            value={this.state.dimensionWidth}
            onFocus={() => {
              C().mapMan.highlightBoundaryAlter(C().sourceMan.origin, this.state.dimensionWidth, this.state.dimensionHeight,
                                          this.state.resolutionWidth, this.state.resolutionHeight,
                                          this.state.supportResolutionWidth, this.state.supportResolutionHeight);
            }}
            onChange={(e) => {
              this.setState({ dimensionWidth: e.target.value })
              C().mapMan.highlightBoundaryAlter(C().sourceMan.origin, e.target.value, this.state.dimensionHeight
                                          , this.state.resolutionWidth, this.state.resolutionHeight,
                                          this.state.supportResolutionWidth, this.state.supportResolutionHeight);
            }}
            onBlur={() => {
              C().mapMan.unhighlightBoundaryAlter();
            }}
            sx={{
              width: this.inputSize
            }}
          />
          </Grid>
          <div
            style={{
              marginLeft: "2px",
              color: "#ffffff",
            }}
          >x</div>
          <Grid
            item
          >
          <TextField type="number" size="small" label="Height" variant="outlined"
            value={this.state.dimensionHeight}
            onFocus={() => {
              C().mapMan.highlightBoundaryAlter(C().sourceMan.origin, this.state.dimensionWidth, this.state.dimensionHeight
                                          , this.state.resolutionWidth, this.state.resolutionHeight,
                                          this.state.supportResolutionWidth, this.state.supportResolutionHeight);
            }}
            onChange={(e) => {
              this.setState({ dimensionHeight: e.target.value })
              C().mapMan.highlightBoundaryAlter(C().sourceMan.origin, this.state.dimensionWidth, e.target.value
                                          , this.state.resolutionWidth, this.state.resolutionHeight,
                                          this.state.supportResolutionWidth, this.state.supportResolutionHeight);
            }}
            onBlur={() => {
              C().mapMan.unhighlightBoundaryAlter();
            }}
            sx={{
              width: this.inputSize
            }}
          />
          </Grid>
          
          <Grid
            item
          >
            <div
              style={{
                color: "#ffffff",
              }}
            >m</div>
          </Grid>
          
        </Grid>
        
        
        <Grid
          item
          size={4}
          container
        >
          <TextField type="number" size="small" variant="outlined" label="Sampled Maps"
            value={this.state.sampleSize}
            onChange={(e) => this.setState({ sampleSize: e.target.value })}
            sx={{
              width: 125
            }}
          />
        </Grid>
        
      </Grid>
      <Grid
        container
        item
        size={12}
        direction="row"
        justifyContent="start"
        justifyItems="start"
        alignItems="center"
        spacing={2}
      >
        
        <Grid
          item
          alignItems={"center"}
          size={4}
          sx={{ display: "flex" }}
        >
          <TextField type="number" size="small" variant="outlined" label="Inference"
            value={this.state.resolutionWidth}
            onFocus={() => {
              C().mapMan.highlightBoundaryAlter(C().sourceMan.origin, this.state.dimensionWidth, this.state.dimensionHeight
                                          , this.state.resolutionWidth, this.state.resolutionHeight,
                                          this.state.supportResolutionWidth, this.state.supportResolutionHeight);
            }}
            onChange={(e) => {
              this.setState({ resolutionWidth: e.target.value })
              C().mapMan.highlightBoundaryAlter(C().sourceMan.origin, this.state.dimensionWidth, this.state.dimensionHeight
                                          , e.target.value, this.state.resolutionHeight,
                                          this.state.supportResolutionWidth, this.state.supportResolutionHeight);
            }}
            onBlur={() => {
              C().mapMan.unhighlightBoundaryAlter();
            }}
            sx={{
              width: this.inputSize
            }}
          />
          <div
            style={{
              marginLeft: "2px",
              color: "#ffffff",
            }}
          >x</div>
          <TextField type="number" size="small" variant="outlined" label="Grid"
            value={this.state.resolutionHeight}
            onFocus={() => {
              C().mapMan.highlightBoundaryAlter(C().sourceMan.origin, this.state.dimensionWidth, this.state.dimensionHeight
                                          , this.state.resolutionWidth, this.state.resolutionHeight,
                                          this.state.supportResolutionWidth, this.state.supportResolutionHeight);
            }}
            onChange={(e) => {
              this.setState({ resolutionHeight: e.target.value })
              C().mapMan.highlightBoundaryAlter(C().sourceMan.origin, this.state.dimensionWidth, this.state.dimensionHeight
                                          , this.state.resolutionWidth, e.target.value,
                                          this.state.supportResolutionWidth, this.state.supportResolutionHeight);
            }}
            onBlur={() => {
              C().mapMan.unhighlightBoundaryAlter();
            }}
            sx={{
              width: this.inputSize
            }}
          />
          
        </Grid>
        
        
        <Grid
          item
          alignItems="center"
          size={4}
          sx={{ display: "flex" }}
        >
          <TextField type="number" size="small" variant="outlined" label="Interpolation"
            value={this.state.supportResolutionWidth}
            onFocus={() => {
              C().mapMan.highlightBoundaryAlter(C().sourceMan.origin, this.state.dimensionWidth, this.state.dimensionHeight,
                                          this.state.resolutionWidth, this.state.resolutionHeight,
                                          this.state.supportResolutionWidth, this.state.supportResolutionHeight);
            }}
            onChange={(e) => {
              this.setState({ supportResolutionWidth: e.target.value })
              C().mapMan.highlightBoundaryAlter(C().sourceMan.origin, this.state.dimensionWidth, this.state.dimensionHeight
                                          , this.state.resolutionWidth, this.state.resolutionHeight,
                                          e.target.value, this.state.supportResolutionHeight);
            }}
            onBlur={() => {
              C().mapMan.unhighlightBoundaryAlter();
            }}
            sx={{
              width: this.inputSize
            }}
          />
          <div
            style={{
              marginLeft: "2px",
              color: "#ffffff",
            }}
          >x</div>
          <TextField type="number" size="small" variant="outlined" label="Grid"
            value={this.state.supportResolutionHeight}
            onFocus={() => {
              C().mapMan.highlightBoundaryAlter(C().sourceMan.origin, this.state.dimensionWidth, this.state.dimensionHeight,
                                          this.state.resolutionWidth, this.state.resolutionHeight,
                                          this.state.supportResolutionWidth, this.state.supportResolutionHeight);
            }}
            onChange={(e) => {
              this.setState({ supportResolutionHeight: e.target.value })
              C().mapMan.highlightBoundaryAlter(C().sourceMan.origin, this.state.dimensionWidth, this.state.dimensionHeight
                                          , this.state.resolutionWidth, this.state.resolutionHeight,
                                          this.state.supportResolutionWidth, e.target.value);
            }}
            onBlur={() => {
              C().mapMan.unhighlightBoundaryAlter();
            }}
            sx={{
              width: this.inputSize
            }}
          />
          
        </Grid>
    
        
        
        <Grid
          item
          size={4}
          container
        >
          <FormControl sx={{minWidth: 125}} size="small">
            <InputLabel
              style={{ color: "rgba(255, 255, 255, 0.7)" }}
            >Interpolation</InputLabel>
            <Select
              label="Interpolation"
              variant="outlined"
              value={C().sourceMan.interpolation}
              onChange={this.handleInterpolationChange}
            >
              {this.createInterpolationItems()}
            </Select>
          </FormControl>
        </Grid>
        
      </Grid>
    </Grid>
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
          <Button
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

        <Grid
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
              <IconButton
                onClick={() => {
                  this.toggleSourceCode();
                }}
                style={{ color: "#eeeeee", fontSize: 12}}
                aria-label="Open location type menu"
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
              <IconButton
                onClick={() => {
                  this.toggleRunningParams();
                }}
                style={{ color: "#eeeeee", fontSize: 12}}
                aria-label="Open running param menu"
              >
                {this.state.runningParamsToggled ? (
                  <CalendarViewMonthTwoToneIcon  />
                ) : (
                  <CalendarViewMonthIcon />
                )}
              </IconButton>
            </Grid>

            <Grid size={1}> 
              <IconButton
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
          
          
          <Grid
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
        
        {this.state.runningParamsToggled ? this.runningParams() : null}
        
        {
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

        {this.state.sourceCodeToggled ?
        <Grid
          style={{
            width: "100%"
          }}
        >
          
          <Grid
            container
            spacing={0}
            direction="row"
            alignItems="center"
            justifyContent="start"
            m={0}
            style={{ 
              marginLeft: "32px" ,
              marginTop: "10px",
            }}
            sx={{ display: "flex" }}
          >
            <Chip
              icon={
                C().sourceMan.hasSource ? (
                  <CloseIcon style={{ color: "#ffffff" }} />
                ) : (
                  <FileUploadIcon style={{ color: "#ffffff" }} />
                )
              }
              onClick={this.toggleFile}
              label={C().sourceMan.hasSource ? "Remove source" : "Import source"}
              variant="outlined"
              style={{
                color: "#ffffff",
                borderColor: "#7e86bd22",
                minWidth: "150px",
              }}
            />
            <input
              type="file"
              accept=".pl"
              onChange={this.handleChange}
              ref={this.hiddenFileInput}
              style={{ display: "none" }} // Make the file input element invisible
            />

            
            
            <Chip
              icon={
                C().sourceMan.edit ? (
                  <DoneIcon style={{ color: "#ffffff" }} />
                ) : (
                  <EditIcon style={{ color: "#ffffff" }} />
                )
              }
              onClick={() => C().sourceMan.toggleEdit()}
              label={C().sourceMan.edit ? "Done" : "Edit"}
              variant="outlined"
              style={{
                color: "#ffffff",
                borderColor: "#7e86bd22",
                minWidth: "80px",
                marginLeft: "8px",
              }}
            />
            
          </Grid>

          <Grid
            container
            spacing={0}
            direction="column"
            alignItems="center"
            justifyContent="start"
            m={0}
            sx={{ 
              display: "flex",
              marginTop: "12px",
              paddingLeft: "32px",
              paddingRight: "32px",
            }}
          >
            {C().sourceMan.edit ? 
              <textarea id="editing"
                className={this.highlightSourceElement ? "errorSignal": ""}
                value={this.editorValue()}
                onChange={(e) => this.updateEditor(e)}
                onKeyDown={(e) => this.checkTab(e.target, e)}
                style={{
                  height: "200px",
                  color: "#ffffff",
                  paddingLeft: "16px",
                }}
              >
              </textarea>
              :
              <pre
                className={this.highlightSourceElement ? "errorSignal": ""}
                id="highlighting"
              >
                <code 
                  id="codeBlock"
                  ref={this.codeRef}
                  className={C().sourceMan.hasSource ? "prolog" : ""}
                >
                  {this.editorValue()}
                </code>
              </pre>
            }
          </Grid>
        </Grid>

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

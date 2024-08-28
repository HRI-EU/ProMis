import * as React from "react";
import "./BottomBar.css";
import hljs from "highlight.js";
import "highlight.js/styles/atom-one-dark.css";
import { C } from "../managers/Core";

//MUI elements
import Box from "@mui/material/Box";
import Drawer from "@mui/material/Drawer";
import Button from "@mui/material/Button";
import Fab from "@mui/material/Fab";
import Grid from "@mui/material/Grid";
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
import ExpandMoreRounded from "@mui/icons-material/ExpandMoreRounded";
import PlayCircleIcon from "@mui/icons-material/PlayCircleOutline";
import StopCircleIcon from "@mui/icons-material/StopCircleOutlined";
import FileUploadIcon from "@mui/icons-material/FileUploadOutlined";
import CloseIcon from "@mui/icons-material/CloseRounded";
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
    };
  }

  inputSize = 80;

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
  };

  // Toggle the running state of the source code
  toggleRun = () => {
    C().sourceMan.toggleRun(this.state.dimensionWidth, this.state.dimensionHeight, this.state.resolutionWidth, this.state.resolutionHeight);
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
    // sync scrolling
    //this.snycScroll();
  }
  
  snycScroll = () => {
    const editing = document.getElementById("editing");
    const highlighting = document.getElementById("highlighting");
    const codeBlock = document.getElementById("codeBlock");
    highlighting.scrollTop = editing.scrollTop;
    codeBlock.scrollLeft = editing.scrollLeft;
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
    items.push(
      <MenuItem key={0} value={""}>
        None
      </MenuItem>
    );
    const markers = C().mapMan.listDroneMarkers();
    for (let i = 0; i < markers.length; i++) {
      items.push(
        <MenuItem key={i + 1} value={markers[i].feature.properties["name"]}>
          {markers[i].feature.properties["name"]}
        </MenuItem>
      );
    }
    return items;
  }

  handleOriginChange = (event) => {
    C().sourceMan.updateOrigin(event.target.value);
    // get marker with this origin name
    const latLon = C().mapMan.latlonDroneFromMarkerName(event.target.value);
    // recenter map
    C().mapMan.recenterMap(latLon);
  }
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
          container
          spacing={0}
          direction="column"
          alignItems="center"
          justifyContent="start"
          m={0}
          sx={{ display: "flex" }}
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
          style={{ marginLeft: "32px" }}
          sx={{ display: "flex" }}
        >
          <ThemeProvider theme={darkTheme}>
            <FormControl sx={{ m: 1, minWidth: 120}} size="small">
              <InputLabel id="demo-simple-select-helper-label"
                style={{ color: "#ffffff" }}
              >Origin</InputLabel>
              <Select
                labelId="demo-simple-select-helper-label"
                id="demo-simple-select-helper"
                label="Origin"
                variant="outlined"
                value={C().sourceMan.origin}
                onChange={this.handleOriginChange}
              >
                {this.createSelectItems()}
              </Select>
            </FormControl>
          </ThemeProvider>
          <ThemeProvider theme={darkTheme}>
            <FormControl sx={{ m: 1, minWidth: 120}} size="small">
              <InputLabel id="demo-simple-select-helper-label"
                style={{ color: "#ffffff" }}
              >Start</InputLabel>
              <Select
                labelId="demo-simple-select-helper-label"
                id="demo-simple-select-helper"
                label="Origin"
                variant="outlined"
                value={C().sourceMan.start}
                onChange={(e) => C().sourceMan.updateStart(e.target.value)}
              >
                {this.createSelectItems()}
              </Select>
            </FormControl>
          </ThemeProvider>
          <ThemeProvider theme={darkTheme}>
            <Grid
              spacing={0}
              direction="row"
              alignItems="center"
              justifyContent="start"
              m={0}
              sx={{ display: "flex",
                marginLeft: "20px",
              }}
            >
              <div
                style={{
                  marginRight: "10px",
                  color: "#ffffff",
                }}
              >Dimensions:</div>
              <TextField type="number" size="small" label="width" variant="outlined" 
                value={this.state.dimensionWidth}
                onChange={(e) => this.setState({ dimensionWidth: e.target.value })}
                sx={{
                  width: this.inputSize
                }}
              />
              <TextField type="number" size="small" label="height" variant="outlined"
                value={this.state.dimensionHeight}
                onChange={(e) => this.setState({ dimensionHeight: e.target.value })}
                sx={{
                  width: this.inputSize
                }}
              />
              <div
                style={{
                  marginLeft: "2px",
                  color: "#ffffff",
                }}
              >m²</div>
            </Grid>
          </ThemeProvider>
          <ThemeProvider theme={darkTheme}>
            <Grid
              spacing={0}
              direction="row"
              alignItems="center"
              justifyContent="start"
              m={0}
              sx={{ display: "flex" ,
                marginLeft: "20px",
              }}
            >
              <div
                style={{
                  marginRight: "10px",
                  color: "#ffffff",
                }}
              >Resolutions:</div>
              <TextField type="number" size="small" variant="outlined" 
                value={this.state.resolutionWidth}
                onChange={(e) => this.setState({ resolutionWidth: e.target.value })}
                sx={{
                  width: this.inputSize
                }}
              />
              <TextField type="number" size="small" variant="outlined"
                value={this.state.resolutionHeight}
                onChange={(e) => this.setState({ resolutionHeight: e.target.value })}
                sx={{
                  width: this.inputSize
                }}
              />
              <div
                style={{
                  marginLeft: "2px",
                  color: "#ffffff",
                }}
              >px</div>
            </Grid>
          </ThemeProvider>
        </Grid>


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
              C().sourceMan.running ? (
                <StopCircleIcon style={{ color: "#ffffff" }} />
              ) : (
                <PlayCircleIcon style={{ color: "#ffffff" }} />
              )
            }
            onClick={this.toggleRun}
            label={C().sourceMan.running ? "Running" : "Run"}
            variant="outlined"
            style={{
              color: "#ffffff",
              borderColor: "#7e86bd22",
              minWidth: "80px",
              marginLeft: "8px",
            }}
          />
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
                  onClick={() => C().sourceMan.closeAlert()}
                >
                  <CloseIcon fontSize="inherit" />
                </IconButton>
              }
            >
              {C().sourceMan.success ? "Success" : "Error"}
            </Alert>
          </Collapse>
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
          }}
        >
          {C().sourceMan.edit ? 
            <textarea id="editing"
              value={this.editorValue()}
              onChange={(e) => this.updateEditor(e)}
              onKeyDown={(e) => this.checkTab(e.target, e)}
              style={{
                height: "300px",
                color: "#ffffff",
                padding: "16px",
              }}
            >
            </textarea>
            :
            <pre
              id="highlighting"
            >
              <code 
                id="codeBlock"
                ref={this.codeRef}
                className={C().sourceMan.hasSource ? "prolog" : ""}
              >
                {C().sourceMan.hasSource
                  ? C().sourceMan.source
                  : "No Model"}
              </code>
            </pre>
          }
        </Grid>

        
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
          <TerminalIcon />
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

import * as React from "react";
import PropTypes from "prop-types";
import CSVFileReader from "./CSVFileReader.js";
import { styled } from "@mui/material/styles";
import { C } from "../managers/Core.js";
import { RenderMode } from "../managers/MapManager.js";
import { updateLayerConfig } from "../utils/Utility.js";

//Local
import "./SidebarRight.css";
import ColorHelper from "../utils/ColorHelper.js";

//MUI elements
import Box from "@mui/material/Box";
import Drawer from "@mui/material/Drawer";
import Button from "@mui/material/Button";
import Fab from "@mui/material/Fab";
import Grid from "@mui/material/Grid";
import ListItemText from "@mui/material/ListItemText";
import IconButton from "@mui/material/IconButton";
import Slider from "@mui/material/Slider";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import FormControl from "@mui/material/FormControl";
import Select from "@mui/material/Select";
import TextField from "@mui/material/TextField";

//Icons
import TuneIcon from "@mui/icons-material/TuneRounded";
import VisibilityRounded from "@mui/icons-material/VisibilityRounded";
import VisibilityOffRounded from "@mui/icons-material/VisibilityOffRounded";
import RemoveCircleOutline from "@mui/icons-material/RemoveCircleOutline";
import ChevronRightIcon from "@mui/icons-material/ChevronRightRounded";
import FileDownloadIcon from "@mui/icons-material/FileDownload";
import ArrowUpIcon from "@mui/icons-material/ArrowUpwardRounded";
import ArrowDownIcon from "@mui/icons-material/ArrowDownwardRounded";
import MyLocationIcon from "@mui/icons-material/MyLocationRounded";
import PaletteFilledIcon from "@mui/icons-material/Palette";
import PaletteOutlinedIcon from "@mui/icons-material/PaletteOutlined";
import SettingsFilledIcon from "@mui/icons-material/Settings";
import SettingsOutlinedIcon from "@mui/icons-material/SettingsOutlined";
import AddIcon from "@mui/icons-material/AddRounded";
import EditIcon from "@mui/icons-material/Edit";
import DoneIcon from "@mui/icons-material/Done";

const VisuallyHiddenInput = styled("input")({
  clip: "rect(0 0 0 0)",
  clipPath: "inset(50%)",
  height: 1,
  overflow: "hidden",
  position: "absolute",
  bottom: 0,
  left: 0,
  whiteSpace: "nowrap",
  width: 1,
});

export default class SidebarRight extends React.Component {
  //const [value, setValue] = React.useState(30);

  constructor() {
    super();
    this.state = {
      top: false,
      left: false,
      bottom: false,
      right: false,
      update: 0,
    };
  }

  updateUI = () => {
    this.setState({ update: this.state.update + 1 });
    console.log(this.state);
  };

  // return the eye symbol if the layer is visible, otherwise return the crossed eye symbol
  getEyeSymbol(isVisible) {
    return isVisible ? <VisibilityRounded /> : <VisibilityOffRounded />;
  }

  toggleDrawer = (anchor, open) => (event) => {
    if (
      event.type === "keydown" &&
      (event.key === "Tab" || event.key === "Shift")
    ) {
      return;
    }
    this.setState({ ...this.state, [anchor]: open });
  };

  // toggle the visibility of all layers
  toggleHideAllLayers = () => {
    C().layerMan.toggleAllLayers();
  };

  list = (anchor) => (
    <Box
      sx={{ width: anchor === "top" || anchor === "bottom" ? "auto" : 300 }}
      role="presentation"
      style={{
        backgroundColor: "#0D0F21",
        borderRadius: "24px 0px 0px 24px",
        overflowY: "scroll",
        overflowX: "hidden",
        scrollbarWidth: "none",
        msOverflowStyle: "none",
      }}
    >
      <div>
        <Grid
          container
          spacing={0}
          direction="column"
          alignItems="center"
          justifyContent="start"
          m={0}
          style={{ maxWidth: "300", display: "flex", height: "100%" }}
        >
          <Fab
            aria-label="add"
            onClick={this.toggleDrawer("right", false)}
            style={{
              color: "#ffffff",
              backgroundColor: "#0D0F21",
              position: "absolute",
              top: "8px",
              right: "236px",
              border: "1px solid #7e86bd22",
            }}
          >
            <ChevronRightIcon />
          </Fab>

          <div
            style={{
              marginTop: "64px",
              marginBottom: "0px",
              marginLeft: "0px",
              marginRight: "0px",
              color: "#ffffff",
              width: "100%",
              paddingLeft: "0px",
            }}
          >
            <Grid
              container
              spacing={0}
              direction="row"
              alignItems="center"
              justifyContent="start"
              m={0}
              style={{ marginLeft: "24px" }}
            >
              <h4>Collections</h4>

              <IconButton
                onClick={() => {
                  this.toggleHideAllLayers();
                }}
                style={{ color: "#ffffff" }}
                aria-label="Toggle all layers"
              >
                {this.getEyeSymbol(!C().layerMan.hideAllLayers)}
              </IconButton>
            </Grid>
          </div>

          {C().layerMan.layers.map((layer, index) => {
            const layerId = layer.id;
            return (
              <SidebarRightItem index={index} key={layerId} layer={layer} />
            );
          })}

          <Button
            style={{
              marginTop: "32px",
              marginBottom: "800px",
              marginRight: "0px",
              marginLeft: "0px",
              color: "#ffffff",
              borderColor: "#ffffff",
              borderRadius: "32px",
              fontSize: 12,
            }}
            variant="outlined"
            startIcon={<AddIcon />}
          >
            <VisuallyHiddenInput type="file" />
            <CSVFileReader
              onFileLoaded={(data, fileInfo) =>
                C().layerMan.importLayer(data, fileInfo)
              }
            />
          </Button>
        </Grid>
      </div>
    </Box>
  );

  render() {
    //Update reference
    C().addRefSidebarRight(this.updateUI);
    C().addToggleDrawerRight(() => {
      this.setState({ right: true });
    });

    return (
      <div
        style={{
          position: "absolute",
          top: 12,
          right: 12,
        }}
      >
        <Fab
          id="sidebar-right-fab"
          aria-label="add"
          onClick={this.toggleDrawer("right", true)}
          style={{
            color: "#ffffff",
            backgroundColor: "#0D0F21",
          }}
        >
          <TuneIcon />
        </Fab>

        <React.Fragment key={"right"}>
          <Drawer
            variant="persistent"
            anchor={"right"}
            open={this.state["right"]}
            onClose={this.toggleDrawer("right", false)}
            color="primary"
            PaperProps={{
              elevation: 0,
              style: { backgroundColor: "transparent" },
            }}
            fx={{
              backgroundColor: "#ff0000",
              variant: "solid",
              borderRadius: "24px 0px 0px 24px",
            }}
            style={{
              borderRadius: "24px 0px 0px 24px",
            }}
          >
            {this.list("right")}
          </Drawer>
        </React.Fragment>
      </div>
    );
  }
}

class SidebarRightItem extends React.Component {
  constructor(props) {
    super(props);
    this.layer = props.layer;

    this.state = {
      textfieldRadiusStr: this.layer.radius + "",
      textfieldRadiusVal: this.layer.radius,
      textfieldRangeVal: this.layer.valueRange,
      textfieldRangeMinStr: this.layer.valueRange[0] + "",
      textfieldRangeMaxStr: this.layer.valueRange[1] + "",
      layerName: this.layer.name,
      currentHue: this.layer.hue,
      currentOpacity: this.layer.opacity,
    };
    this.index = props.index;
  }

  // change the hue of the layer when the hue slider is changed
  hueSliderChanged = (layer, hue) => {
    // skip if render mode is *image
    if (
      layer.renderMode === RenderMode.PNGImage ||
      layer.renderMode === RenderMode.SVGImage
    ) {
      layer.hue = hue;
      this.setState({ currentHue: hue });
      return;
    }
    C().layerMan.changeLayerColor(layer, hue);
  };

  // change the hue of the layer when the hue slider is changed
  commitHueSliderChanged = (layer, hue) => {
    C().layerMan.changeLayerColor(layer, hue);
    updateLayerConfig(layer);
  };

  // change the opacity of the layer when the opacity slider is changed
  opacitySliderChanged = (layer, opacityRange, commited) => {
    // skip if render mode is *image and is not committed
    if (
      layer.renderMode === RenderMode.PNGImage ||
      layer.renderMode === RenderMode.SVGImage
    ) {
      if (!commited) {
        this.layer.opacity = opacityRange;
        this.setState({
          currentOpacity: opacityRange,
        });
        return;
      }
    }

    C().layerMan.changeLayerOpacity(layer, opacityRange, commited);
  };

  // change the radius of the layer when the radius slider is changed
  radiusChanged = (selectedLayerId, radius) => {
    C().layerMan.changeLayerRadius(selectedLayerId, radius);
    this.setState({
      textfieldRadiusStr: radius + "",
      textfieldRadiusVal: radius,
    });
  };

  // change the value range of the layer when the value range slider is changed
  valueRangeChanged = (selectedLayerId, valueRange) => {
    C().layerMan.changeLayerValueRange(selectedLayerId, valueRange);
    this.setState({
      textfieldRangeVal: valueRange,
      textfieldRangeMinStr: valueRange[0],
      textfieldRangeMaxStr: valueRange[1],
    });
  };

  // toggle the edit name of the layer
  toggleEditName = (layer, layerName = "") => {
    if (layerName === "") {
      layerName = this.state.layerName;
    }
    C().layerMan.toggleEditName(layer.id, layerName);
  };

  // toggle the visibility of the layer
  toggleVisibility = (layer) => {
    C().layerMan.changeLayerVisibility(layer.id, !layer.visible);
  };

  // toggle the settings menu of the layer
  toggleSettingsMenu = (layer) => {
    C().layerMan.changeLayerSettingsExpanded(
      layer.id,
      !layer.settingsMenuExpanded,
    );
  };

  // toggle the color menu of the layer
  toggleColorMenu = (layer) => {
    C().layerMan.changeLayerColorsExpanded(layer.id, !layer.colorMenuExpanded);
  };

  // change the render mode of the layer
  renderModeChanged = (layerId, renderMode) => {
    C().layerMan.changeLayerRenderMode(layerId, renderMode);
  };

  // return the name of the render mode
  getRenderModeName(renderMode) {
    switch (renderMode) {
      case RenderMode.HeatmapRect:
        return "Heatmap (Squares)";
      case RenderMode.HeatmapCircle:
        return "Heatmap (Circles)";
      case RenderMode.Voronoi:
        return "Voronoi";
      case RenderMode.SVGImage:
        return "SVG Image";
      case RenderMode.PNGImage:
        return "PNG Image";
    }
  }

  // delete the layer
  onDeleteLayer = (layerId) => {
    C().layerMan.deleteLayer(layerId);
  };

  /**
   * Create a GeoJSON file from the layer and download it
   * Called when export json for a specific layer is clicked
   * @param {number} layerId
   */
  onExportGeoJSON = (layerId) => {
    const geojson = C().layerMan.exportGeoJSON(layerId);
    const layerName = C().layerMan.getLayerById(layerId).name;
    // remove .csv from layer name
    const layerNameWithoutCSV = layerName.replace(".csv", "");

    // prepare data and set up download geojson
    var dataStr =
      "data:text/json;charset=utf-8," +
      encodeURIComponent(JSON.stringify(geojson, null, 2));
    var downloadAnchorNode = document.createElement("a");
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute(
      "download",
      layerNameWithoutCSV + ".geojson",
    );
    document.body.appendChild(downloadAnchorNode); // required for firefox
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  };

  render() {
    //Load layer data from LayerManager
    var layer = C().layerMan.getLayerById(this.layer.id);

    return (
      <div
        id={"layer-" + this.index}
        key={layer.id}
        style={{
          //borderColor: '#000fff',
          marginTop: "12px",
          marginBottom: "0px",
          marginRight: "0px",
          marginLeft: "0px",
        }}
      >
        <Grid
          container
          spacing={0}
          direction="column"
          alignItems="start"
          justifyContent="start"
          m={0}
        >
          <Grid
            container
            spacing={0}
            direction="row"
            alignItems="center"
            justifyContent="start"
            width="250px"
            m={0}
          >
            <IconButton
              onClick={() => {
                this.toggleVisibility(layer);
              }}
              style={{ color: "#ffffff", fontSize: 12 }}
              aria-label="Toggle all layers"
            >
              <Box
                style={{
                  //borderColor: '#000fff',
                  marginTop: "0px",
                  marginBottom: "0px",
                  marginRight: "0px",
                  marginLeft: "0px",
                  opacity: layer.visible ? "1" : "0.3",
                }}
                sx={{
                  width: "24px",
                  height: "24px",
                  m: 1,
                  borderRadius: "24px",
                  bgcolor: ColorHelper.calcHexByHue(layer.hue),
                  border: "1px",
                  borderColor: "#ffffffaa",
                }}
              ></Box>
            </IconButton>

            <div
              style={{
                marginTop: "0px",
                marginBottom: "0px",
                marginRight: "0px",
                marginLeft: "8px",
                width: "190px",
              }}
            >
              {layer.editName ? (
                <TextField
                  id="outlined-basic"
                  borderColor="white"
                  label=""
                  value={this.state.layerName}
                  variant="outlined"
                  size="small"
                  onChange={(event) => {
                    var str = event.target.value;
                    this.setState({ layerName: str });
                  }}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      this.toggleEditName(layer);
                    } else if (event.key === "Escape") {
                      this.setState({ layerName: layer.name });
                      this.toggleEditName(layer, layer.name);
                    }
                  }}
                  InputProps={{
                    inputProps: {
                      min: 0,
                      style: { textAlign: "left" },
                    },
                    style: {
                      color: "#ffffff",
                      borderRadius: "8px",
                    },
                  }}
                  style={{
                    width: "180px",
                    marginTop: "0px",
                  }}
                  sx={{
                    color: "white",
                    ".MuiOutlinedInput-notchedOutline": {
                      borderColor: "rgba(228, 219, 233, 0.25)",
                    },
                    "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                      borderColor: "rgba(228, 219, 233, 0.25)",
                    },
                    "&:hover .MuiOutlinedInput-notchedOutline": {
                      borderColor: "rgba(228, 219, 233, 0.25)",
                    },
                    ".MuiSvgIcon-root ": {
                      fill: "white !important",
                    },
                  }}
                />
              ) : (
                <ListItemText
                  primary={layer.name === "" ? "Untitled" : layer.name}
                  style={{
                    textAlign: "left",
                    marginTop: "0px",
                    marginBottom: "0px",
                    marginRight: "0px",
                    marginLeft: "0px",
                    width: "190px",
                    overflow: "hidden",
                    color: layer.visible ? "#ffffff" : "#ffffff88",
                  }}
                />
              )}
            </div>
          </Grid>

          <Grid
            container
            spacing={0}
            direction="row"
            alignItems="center"
            justifyContent="start"
            m={0}
            style={{ marginLeft: "0px" }}
          >
            <IconButton
              onClick={() => {
                C().layerMan.moveLayerUp(layer.id);
              }}
              style={{ color: "#eeeeee", fontSize: 12 }}
              aria-label="Move layer up"
            >
              <ArrowUpIcon />
            </IconButton>

            <IconButton
              onClick={() => {
                C().layerMan.moveLayerDown(layer.id);
              }}
              style={{ color: "#eeeeee", fontSize: 12 }}
              aria-label="Move layer down"
            >
              <ArrowDownIcon />
            </IconButton>

            <IconButton
              onClick={() => {
                C().layerMan.moveToLayerCenter(layer.id);
              }}
              style={{ color: "#eeeeee", fontSize: 12 }}
              aria-label="Move map to center"
            >
              <MyLocationIcon />
            </IconButton>

            <IconButton
              onClick={() => {
                this.toggleEditName(layer);
              }}
              style={{ color: "#eeeeee", fontSize: 12, marginLeft: "10px" }}
              aria-label="Edit layer name"
            >
              {layer.editName ? <DoneIcon /> : <EditIcon />}
            </IconButton>

            <IconButton
              onClick={() => {
                this.toggleColorMenu(layer);
              }}
              style={{ color: "#eeeeee", fontSize: 12 }}
              aria-label="Open color menu"
            >
              {layer.colorMenuExpanded ? (
                <PaletteFilledIcon />
              ) : (
                <PaletteOutlinedIcon />
              )}
            </IconButton>

            <IconButton
              onClick={() => {
                this.toggleSettingsMenu(layer);
              }}
              style={{ color: "#eeeeee", fontSize: 12 }}
              aria-label="Open settings menu"
            >
              {layer.settingsMenuExpanded ? (
                <SettingsFilledIcon />
              ) : (
                <SettingsOutlinedIcon />
              )}
            </IconButton>
          </Grid>
        </Grid>

        {layer.colorMenuExpanded ? (
          <Grid
            container
            spacing={0}
            direction="column"
            alignItems="center"
            justifyContent="start"
            style={{ marginTop: "8px" }}
          >
            <Grid
              container
              spacing={0}
              direction="row"
              alignItems="start"
              justifyContent="center"
            >
              <IconButton
                onClick={() => {
                  this.commitHueSliderChanged(layer, 0);
                }}
                style={{ color: "#ffffff", fontSize: 12 }}
                aria-label="Toggle all layers"
              >
                <Box
                  style={{
                    marginRight: "2px",
                    marginLeft: "2px",
                  }}
                  sx={{
                    width: "24px",
                    height: "24px",
                    m: 1,
                    borderRadius: "24px",
                    bgcolor: "#ef9a9a",
                    border: "1px",
                    borderColor: "#ffffffaa",
                  }}
                ></Box>
              </IconButton>

              <IconButton
                onClick={() => {
                  this.commitHueSliderChanged(layer, 72);
                }}
                style={{ color: "#ffffff", fontSize: 12 }}
                aria-label="Toggle all layers"
              >
                <Box
                  style={{
                    //borderColor: '#000fff',
                    marginRight: "2px",
                    marginLeft: "2px",
                  }}
                  sx={{
                    width: "24px",
                    height: "24px",
                    m: 1,
                    borderRadius: "24px",
                    bgcolor: "#deef9a",
                    border: "1px",
                    borderColor: "#ffffffaa",
                  }}
                ></Box>
              </IconButton>

              <IconButton
                onClick={() => {
                  this.commitHueSliderChanged(layer, 144);
                }}
                style={{ color: "#ffffff", fontSize: 12 }}
                aria-label="Toggle all layers"
              >
                <Box
                  style={{
                    marginRight: "2px",
                    marginLeft: "2px",
                  }}
                  sx={{
                    width: "24px",
                    height: "24px",
                    m: 1,
                    borderRadius: "24px",
                    bgcolor: "#9aefbc",
                    border: "1px",
                    borderColor: "#ffffffaa",
                  }}
                ></Box>
              </IconButton>

              <IconButton
                onClick={() => {
                  this.commitHueSliderChanged(layer, 216);
                }}
                style={{ color: "#ffffff", fontSize: 12 }}
                aria-label="Toggle all layers"
              >
                <Box
                  style={{
                    //borderColor: '#000fff',
                    marginRight: "2px",
                    marginLeft: "2px",
                  }}
                  sx={{
                    width: "24px",
                    height: "24px",
                    m: 1,
                    borderRadius: "24px",
                    bgcolor: "#9abcef",
                    border: "1px",
                    borderColor: "#ffffffaa",
                  }}
                ></Box>
              </IconButton>

              <IconButton
                onClick={() => {
                  this.commitHueSliderChanged(layer, 288);
                }}
                style={{ color: "#ffffff", fontSize: 12 }}
                aria-label="Toggle all layers"
              >
                <Box
                  style={{
                    marginRight: "2px",
                    marginLeft: "2px",
                  }}
                  sx={{
                    width: "24px",
                    height: "24px",
                    m: 1,
                    borderRadius: "24px",
                    bgcolor: "#de9aef",
                    border: "1px",
                    borderColor: "#ffffffaa",
                  }}
                ></Box>
              </IconButton>
            </Grid>

            <div
              style={{
                width: "180px",
                marginBottom: "0px",
                marginLeft: "0px",
                marginRight: "0px",
              }}
            >
              <Slider
                min={0}
                max={359}
                value={layer.hue}
                onChange={(event, newValue) => {
                  this.hueSliderChanged(layer, newValue);
                }}
                onChangeCommitted={(event, newValue) => {
                  this.commitHueSliderChanged(layer, newValue);
                }}
                valueLabelDisplay="auto"
                style={{
                  color: "#ffffff",
                  marginTop: "0px",
                  width: "14px !important",
                }}
              />

              <div
                style={{
                  marginTop: "12px",
                  marginBottom: "0px",
                  marginLeft: "0px",
                  marginRight: "0px",
                  color: "#ffffff",
                }}
              >
                Opacity
              </div>

              <Slider
                value={layer.opacity}
                min={0}
                max={100}
                onChange={(event, newValue) => {
                  this.opacitySliderChanged(layer, newValue, false);
                }}
                onChangeCommitted={(event, newValue) => {
                  this.opacitySliderChanged(layer, newValue, true);
                }}
                valueLabelDisplay="auto"
                style={{
                  color: "#ffffff",
                }}
              />
            </div>
          </Grid>
        ) : null}

        {layer.settingsMenuExpanded ? (
          <div
            style={{
              marginTop: "0px",
              marginBottom: "0px",
              marginLeft: "0px",
              marginRight: "0px",
            }}
          >
            <Grid
              container
              spacing={0}
              direction="column"
              alignItems="center"
              justifyContent="start"
              style={{ marginTop: "16px" }}
            >
              <FormControl sx={{ m: 1, minWidth: 200 }}>
                <InputLabel
                  id="demo-simple-select-helper-label"
                  style={{ color: "#fff" }}
                >
                  Render Mode
                </InputLabel>
                <Select
                  labelId="demo-simple-select-helper-label"
                  id="demo-simple-select-helper"
                  value={layer.renderMode}
                  label="Render mode"
                  onChange={(event) =>
                    this.renderModeChanged(layer.id, event.target.value)
                  }
                  inputProps={{
                    MenuProps: {
                      MenuListProps: {
                        sx: {
                          color: "#ffffff",
                          backgroundColor: "#0f1124",
                        },
                      },
                    },
                  }}
                  sx={{
                    color: "white",
                    ".MuiOutlinedInput-notchedOutline": {
                      borderColor: "rgba(228, 219, 233, 0.25)",
                    },
                    "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                      borderColor: "rgba(228, 219, 233, 0.25)",
                    },
                    "&:hover .MuiOutlinedInput-notchedOutline": {
                      borderColor: "rgba(228, 219, 233, 0.25)",
                    },
                    ".MuiSvgIcon-root ": {
                      fill: "white !important",
                    },
                  }}
                  style={{
                    color: "#ffffff",
                    textColor: "#ffffff",
                    borderRadius: "16px",
                    textAlign: "left",
                  }}
                >
                  <MenuItem value={RenderMode.HeatmapRect}>
                    Heatmap (Squares)
                  </MenuItem>
                  <MenuItem value={RenderMode.HeatmapCircle}>
                    Heatmap (Circles)
                  </MenuItem>
                  <MenuItem value={RenderMode.Voronoi}>Voronoi</MenuItem>
                  <MenuItem value={RenderMode.SVGImage}>SVG Image</MenuItem>
                  <MenuItem value={RenderMode.PNGImage}>PNG Image</MenuItem>
                </Select>
              </FormControl>

              {layer.renderMode !== RenderMode.Voronoi &&
              layer.renderMode !== RenderMode.SVGImage &&
              layer.renderMode !== RenderMode.PNGImage ? (
                <Grid
                  container
                  spacing={0}
                  direction="column"
                  alignItems="center"
                  justifyContent="start"
                >
                  <div
                    style={{
                      marginTop: "16px",
                      marginBottom: "0px",
                      marginLeft: "0px",
                      marginRight: "0px",
                      color: "#ffffff",
                    }}
                  >
                    Radius
                  </div>

                  <Slider
                    value={this.state.textfieldRadiusVal}
                    min={0.1}
                    max={
                      parseFloat(this.state.textfieldRadiusStr) <= 10
                        ? 10
                        : parseFloat(this.state.textfieldRadiusStr)
                    }
                    step={0.1}
                    onChange={(event, newValue) => {
                      this.setState({ textfieldRadiusVal: newValue });
                    }}
                    onChangeCommitted={(event, newValue) => {
                      this.radiusChanged(layer.id, newValue);
                    }}
                    valueLabelDisplay="auto"
                    style={{
                      width: "180px",
                      color: "#ffffff",
                    }}
                  />

                  <TextField
                    id="outlined-basic"
                    label=""
                    value={this.state.textfieldRadiusStr}
                    variant="outlined"
                    size="small"
                    onChange={(event) => {
                      var str = event.target.value;
                      //Dont rerender if last char is digit sign
                      console.log("changed to string " + str);
                      this.setState({ textfieldRadiusStr: str });
                      if (str.slice(-1) !== ".") {
                        this.radiusChanged(
                          layer.id,
                          str !== "" ? parseFloat(str) : 0,
                        );
                      }
                    }}
                    InputProps={{
                      inputProps: {
                        min: 0,
                        style: { textAlign: "center" },
                        pattern: "[+-]?([0-9]*[.])?[0-9]+",
                      },
                      style: {
                        color: "#ffffff",
                        borderRadius: "16px",
                      },
                    }}
                    style={{
                      width: "80px",
                      marginTop: "8px",
                    }}
                    sx={{
                      color: "white",
                      ".MuiOutlinedInput-notchedOutline": {
                        borderColor: "rgba(228, 219, 233, 0.25)",
                      },
                      "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                        borderColor: "rgba(228, 219, 233, 0.25)",
                      },
                      "&:hover .MuiOutlinedInput-notchedOutline": {
                        borderColor: "rgba(228, 219, 233, 0.25)",
                      },
                      "& .MuiOutlinedInput-root.Mui-focused .MuiOutlinedInput-notchedOutline":
                        {
                          borderColor: "rgba(228, 219, 233, 0.25)",
                        },
                      ".MuiSvgIcon-root ": {
                        fill: "white !important",
                      },
                    }}
                  />
                </Grid>
              ) : null}

              <div
                style={{
                  marginTop: "20px",
                  marginBottom: "0px",
                  marginLeft: "0px",
                  marginRight: "0px",
                  color: "#ffffff",
                }}
              >
                Value Filter
              </div>

              <Slider
                value={this.state.textfieldRangeVal}
                min={layer.markersValMinMax[0]}
                max={layer.markersValMinMax[1]}
                step={0.01}
                onChange={(event, newValue) => {
                  this.setState({ textfieldRangeVal: newValue });
                }}
                onChangeCommitted={(event, newValue) => {
                  this.valueRangeChanged(layer.id, newValue);
                }}
                valueLabelDisplay="auto"
                style={{
                  width: "180px",
                  color: "#ffffff",
                }}
              />

              <Grid
                container
                spacing={0}
                direction="row"
                alignItems="center"
                justifyContent="center"
                style={{ marginTop: "8px" }}
              >
                <TextField
                  id="outlined-basic"
                  label=""
                  value={this.state.textfieldRangeVal[0]}
                  variant="outlined"
                  size="small"
                  onChange={(event) => {
                    var str = event.target.value;
                    this.setState({ textfieldRangeMinStr: str });
                    if (str.slice(-1) !== ".") {
                      this.valueRangeChanged(layer.id, [
                        str !== "" ? parseFloat(str) : 0,
                        layer.valueRange[1],
                      ]);
                    }
                  }}
                  InputProps={{
                    inputProps: {
                      min: 0,
                      style: { textAlign: "center" },
                      pattern: "[+-]?([0-9]*[.])?[0-9]+",
                    },
                    style: {
                      color: "#ffffff",
                      borderRadius: "16px",
                    },
                  }}
                  style={{
                    width: "80px",
                    marginRight: "64px",
                  }}
                  sx={{
                    color: "white",
                    ".MuiOutlinedInput-notchedOutline": {
                      borderColor: "rgba(228, 219, 233, 0.25)",
                    },
                    "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                      borderColor: "rgba(228, 219, 233, 0.25)",
                    },
                    "&:hover .MuiOutlinedInput-notchedOutline": {
                      borderColor: "rgba(228, 219, 233, 0.25)",
                    },
                    "& .MuiOutlinedInput-root.Mui-focused .MuiOutlinedInput-notchedOutline":
                      {
                        borderColor: "rgba(228, 219, 233, 0.25)",
                      },
                    ".MuiSvgIcon-root ": {
                      fill: "white !important",
                    },
                  }}
                />

                <TextField
                  id="outlined-basic"
                  label=""
                  value={this.state.textfieldRangeVal[1]}
                  variant="outlined"
                  size="small"
                  onChange={(event) => {
                    var str = event.target.value;
                    this.setState({ textfieldRangeMaxStr: str });
                    if (str.slice(-1) !== ".") {
                      this.valueRangeChanged(layer.id, [
                        layer.valueRange[0],
                        str !== "" ? parseFloat(str) : 0,
                      ]);
                    }
                  }}
                  InputProps={{
                    inputProps: {
                      min: 0,
                      style: { textAlign: "center" },
                      pattern: "[+-]?([0-9]*[.])?[0-9]+",
                    },
                    style: {
                      color: "#ffffff",
                      borderRadius: "16px",
                    },
                  }}
                  style={{
                    width: "80px",
                  }}
                  sx={{
                    color: "white",
                    ".MuiOutlinedInput-notchedOutline": {
                      borderColor: "rgba(228, 219, 233, 0.25)",
                    },
                    "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
                      borderColor: "rgba(228, 219, 233, 0.25)",
                    },
                    "&:hover .MuiOutlinedInput-notchedOutline": {
                      borderColor: "rgba(228, 219, 233, 0.25)",
                    },
                    "& .MuiOutlinedInput-root.Mui-focused .MuiOutlinedInput-notchedOutline":
                      {
                        borderColor: "rgba(228, 219, 233, 0.25)",
                      },
                    ".MuiSvgIcon-root ": {
                      fill: "white !important",
                    },
                  }}
                />
              </Grid>

              <Button
                onClick={() => {
                  this.onDeleteLayer(layer.id);
                }}
                style={{
                  marginTop: "20px",
                  marginBottom: "0px",
                  marginRight: "0px",
                  marginLeft: "0px",
                  color: "#ffffff",
                  borderColor: "#ffffff",
                  borderRadius: "32px",
                  fontSize: 12,
                }}
                variant="outlined"
                startIcon={<RemoveCircleOutline />}
              >
                Delete layer
                <VisuallyHiddenInput type="file" />
              </Button>
              <Button
                onClick={() => {
                  this.onExportGeoJSON(layer.id);
                }}
                style={{
                  marginTop: "20px",
                  marginBottom: "0px",
                  marginRight: "0px",
                  marginLeft: "0px",
                  color: "#ffffff",
                  borderColor: "#ffffff",
                  borderRadius: "32px",
                  fontSize: 12,
                }}
                variant="outlined"
                startIcon={<FileDownloadIcon />}
              >
                export GeoJSON
              </Button>
            </Grid>
          </div>
        ) : null}

        <div
          style={{
            width: "100%",
            height: "2px",
            marginTop:
              layer.settingsMenuExpanded || layer.colorMenuExpanded
                ? "24px"
                : "4px",
            marginBottom: "0px",
            marginLeft: "0px",
            marginRight: "0px",
            backgroundColor: "#7e86bd22",
          }}
        ></div>
      </div>
    );
  }
}

SidebarRightItem.propTypes = {
  layer: PropTypes.object.isRequired,
  index: PropTypes.number.isRequired,
};

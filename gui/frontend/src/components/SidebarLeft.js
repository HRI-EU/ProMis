import * as React from "react";
import { C } from "../managers/Core";

//MUI elements
import Box from "@mui/material/Box";
import Drawer from "@mui/material/Drawer";
import Button from "@mui/material/Button";
import Fab from "@mui/material/Fab";
import Grid from "@mui/material/Grid";
import { Modal } from "@mui/material";
import Typography from "@mui/material/Typography";
import { ThemeProvider, createTheme } from "@mui/material/styles";

//Icon imports
import MenuIcon from "@mui/icons-material/MenuRounded";
import FileUploadIcon from "@mui/icons-material/FileUploadRounded";
import FileDownloadIcon from "@mui/icons-material/FileDownloadRounded";
import ClearIcon from "@mui/icons-material/ClearRounded";
import InfoIcon from "@mui/icons-material/InfoOutlined";
import SimCardDownloadIcon from "@mui/icons-material/SimCardDownload";
import { styled } from "@mui/material/styles";

// style for the modal
const style = {
  position: "absolute",
  top: "50%",
  left: "50%",
  transform: "translate(-50%, -50%)",
  width: 400,
  bgcolor: "background.paper",
  border: "2px solid #000",
  boxShadow: 24,
  p: 4,
  color: "text.primary",
};

// create a dark theme for the modal
const darkTheme = createTheme({
  palette: {
    mode: "dark",
  },
});

export default function SidebarLeft() {
  const [state, setState] = React.useState({
    top: false,
    left: false,
    bottom: false,
    right: false,
  });

  // state for the modal of the about section
  const [open, setOpen] = React.useState(false);
  const handleOpen = () => setOpen(true);
  const handleClose = () => setOpen(false);

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

  /**
   * Import all layers from exported json file
   * @param {*} event
   * @returns
   */
  async function importFile(event) {
    if (event.target.files.length === 0) return;
    var file = event.target.files[0];
    async function parseJsonFile(file) {
      return new Promise((resolve, reject) => {
        const fileReader = new FileReader();
        fileReader.onload = (event) => resolve(JSON.parse(event.target.result));
        fileReader.onerror = (error) => reject(error);
        fileReader.readAsText(file);
      });
    }

    const object = await parseJsonFile(file);
    console.log(object);
    C().layerMan.importAllLayers(object);
  }

  /**
   * export all layers to a json file
   */
  const saveFile = async () => {
    const obj = C().layerMan.layers;
    const markerLayers = C().layerMan.layers.map((layer) => {
      return layer.markerLayer;
    });
    const leafletOverlays = C().layerMan.layers.map((layer) => {
      return layer.leafletOverlays;
    });
    obj.forEach((layer) => {
      layer.markerLayer = null;
      layer.leafletOverlays = [];
    });
    const blob = new Blob([JSON.stringify(obj, null, 2)], {
      type: "application/json",
    });
    // add markerLayer back to layers
    obj.forEach((layer, index) => {
      layer.markerLayer = markerLayers[index];
      layer.leafletOverlays = leafletOverlays[index];
    });

    const a = document.createElement("a");
    a.download = "layer-file.json";
    a.href = URL.createObjectURL(blob);
    a.addEventListener("click", () => {
      setTimeout(() => URL.revokeObjectURL(a.href), 30 * 1000);
    });
    a.click();
  };

  /**
   * Delete all previously added layers from the map and from the SidebarLeft
   */
  function clearAllLayers() {
    C().layerMan.deleteAllLayers();
  }

  /**
   * Export all layers to GeoJSON including markers
   * Create a download link for the GeoJSON file
   */
  function exportGeoJSON() {
    const geojson = C().layerMan.exportAllGeoJSON();
    const fileName = "session";
    var dataStr =
      "data:text/json;charset=utf-8," +
      encodeURIComponent(JSON.stringify(geojson, null, 2));
    var downloadAnchorNode = document.createElement("a");
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", fileName + ".geojson");
    document.body.appendChild(downloadAnchorNode); // required for firefox
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  }

  const toggleDrawer = (anchor, open) => (event) => {
    if (
      event.type === "keydown" &&
      (event.key === "Tab" || event.key === "Shift")
    ) {
      return;
    }

    setState({ ...state, [anchor]: open });
  };

  const list = (anchor) => (
    <Box
      sx={{ width: anchor === "top" || anchor === "bottom" ? "auto" : 260 }}
      role="presentation"
      style={{
        backgroundColor: "#0D0F21",
        height: "100%",
        borderRadius: "0px 24px 24px 0px",
        overflow: "hidden",
      }}
    >
      <Grid
        container
        spacing={0}
        direction="column"
        alignItems="left"
        justifyContent="start"
        m={0}
        sx={{ minHeight: "100vh" }}
      >
        <div
          style={{
            marginTop: "48px",
            marginBottom: "0px",
            marginLeft: "0px",
            marginRight: "0px",
            color: "#ffffff",
            width: "100%",
            paddingLeft: "24px",
          }}
        >
          <h5>Project</h5>
        </div>

        <Button
          component="label"
          style={{
            width: "200px",
            marginTop: "12px",
            marginBottom: "0px",
            marginRight: "0px",
            marginLeft: "24px",
            color: "#ffffff",
            borderColor: "#ffffff",
            borderRadius: "32px",
            fontSize: 12,
          }}
          variant="outlined"
          startIcon={<FileUploadIcon />}
        >
          <div
            style={{ width: "140px", marginLeft: "12px", textAlign: "start" }}
          >
            Import project
            <VisuallyHiddenInput type="file" onChange={importFile} />
          </div>
        </Button>

        <Button
          onClick={() => saveFile()}
          style={{
            width: "200px",
            marginTop: "12px",
            marginBottom: "0px",
            marginRight: "0px",
            marginLeft: "24px",
            color: "#ffffff",
            borderColor: "#ffffff",
            borderRadius: "32px",
            fontSize: 12,
          }}
          variant="outlined"
          startIcon={<FileDownloadIcon />}
        >
          <div
            style={{ width: "140px", marginLeft: "12px", textAlign: "start" }}
          >
            Export project
          </div>
        </Button>

        <Button
          onClick={exportGeoJSON}
          style={{
            width: "200px",
            marginTop: "12px",
            marginBottom: "0px",
            marginRight: "0px",
            marginLeft: "24px",
            color: "#ffffff",
            borderColor: "#ffffff",
            borderRadius: "32px",
            fontSize: 12,
          }}
          variant="outlined"
          startIcon={<SimCardDownloadIcon />}
        >
          <div
            style={{ width: "140px", marginLeft: "12px", textAlign: "start" }}
          >
            Export GEOJSON
          </div>
        </Button>

        <Button
          onClick={() => clearAllLayers()}
          style={{
            width: "200px",
            marginTop: "12px",
            marginBottom: "0px",
            marginRight: "0px",
            marginLeft: "24px",
            color: "#ffffff",
            borderColor: "#ffffff",
            borderRadius: "32px",
            fontSize: 12,
          }}
          variant="outlined"
          startIcon={<ClearIcon />}
        >
          <div
            style={{ width: "140px", marginLeft: "12px", textAlign: "start" }}
          >
            Clear all layers
          </div>
        </Button>

        <div
          style={{
            marginTop: "48px",
            marginBottom: "0px",
            marginLeft: "0px",
            marginRight: "0px",
            color: "#ffffff",
            width: "100%",
            paddingLeft: "24px",
          }}
        >
          <h5>About</h5>
        </div>

        <Button
          onClick={handleOpen}
          style={{
            width: "200px",
            marginTop: "12px",
            marginBottom: "0px",
            marginRight: "0px",
            marginLeft: "24px",
            color: "#ffffff",
            borderColor: "#ffffff",
            borderRadius: "32px",
            fontSize: 12,
          }}
          variant="outlined"
          startIcon={<InfoIcon />}
        >
          <div
            style={{ width: "140px", marginLeft: "12px", textAlign: "start" }}
          >
            Details
          </div>
        </Button>
      </Grid>
      <ThemeProvider theme={darkTheme}>
        <Modal
          open={open}
          onClose={handleClose}
          aria-labelledby="about"
          aria-describedby="description"
        >
          <Box sx={style}>
            <Typography id="about" variant="h6" component="h2">
              About
            </Typography>
            <Typography id="description" sx={{ mt: 2 }}>
              Project:{" "}
              <b>
                Geographic information interface for probabilistic mission
                design
              </b>
              <br />
              Developed by:{" "}
              <b>
                Van Duc Hoang, Duc Bach Lai, Trung Hieu Tran, Timo Krusch, Junyi
                Chen
              </b>
              <br />
              Drone icon made by{" "}
              <a href="https://commons.wikimedia.org/wiki/File:Drone.svg">
                Jacek Rużyczka
              </a>
              ,{" "}
              <a href="https://creativecommons.org/licenses/by-sa/4.0">
                CC BY-SA 4.0
              </a>
              , via Wikimedia Commons
            </Typography>
          </Box>
        </Modal>
      </ThemeProvider>
    </Box>
  );

  return (
    <div
      style={{
        position: "absolute",
        top: 20,
        left: 12,
      }}
    >
      <Fab
        aria-label="add"
        onClick={toggleDrawer("left", true)}
        style={{
          color: "#ffffff",
          backgroundColor: "#0D0F21",
        }}
        size="small"
      >
        <MenuIcon />
      </Fab>

      <React.Fragment key={"left"}>
        <Drawer
          anchor={"left"}
          open={state["left"]}
          onClose={toggleDrawer("left", false)}
          color="primary"
          PaperProps={{
            elevation: 0,
            style: { backgroundColor: "transparent" },
          }}
          fx={{
            backgroundColor: "#ff0000",
            variant: "solid",
            borderRadius: "0px 24px 24px 0px",
          }}
          style={{
            borderRadius: "0px 24px 24px 0px",
          }}
        >
          {list("left")}
        </Drawer>
      </React.Fragment>
    </div>
  );
}

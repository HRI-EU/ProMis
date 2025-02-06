import { C } from "../managers/Core.js";

import React from "react";

import { IconButton } from "@mui/material";
import LightbulbIcon from '@mui/icons-material/Lightbulb';
import LightbulbOutlinedIcon from '@mui/icons-material/LightbulbOutlined';

export default function DynamicLayerInteractive() {
    const [dynamicOnTop, setDynamicOnTop] = React.useState(false);

    const onDynamicClick = () => {
      setDynamicOnTop(!dynamicOnTop);
      C().mapMan.toggleDynamicOnTop(dynamicOnTop);
    }

    return (
      <div 
        className="leaflet-control"
        style={{ 
          position: "absolute", 
          top: "320px", 
          left: "10px",
          zIndex: 1001,
          border: "2px solid rgba(0,0,0,0.2)",
        }}
      >
        <IconButton aria-label="highlight" 
          className="leaflet-buttons-control-button"
          style={{
            backgroundColor: "white",
            color: "#495057",
            borderRadius: 0,
            width: "30px",
            height: "30px",
          }}
          onClick={onDynamicClick}
        >
          {dynamicOnTop ? <LightbulbIcon /> : <LightbulbOutlinedIcon />}
        </IconButton>
      </div>
    )
}



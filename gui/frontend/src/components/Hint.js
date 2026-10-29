import * as React from "react";
import PropTypes from "prop-types";

import Tooltip from "@mui/material/Tooltip";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";

/**
 * A small info pin that explains an element of the GUI when hovered,
 * to keep explanations out of the way until they are needed.
 * @param {*} props
 * props.title - The explanation, a string or JSX.
 * props.sx - Additional styles of the icon.
 * @returns JSX.Element
 */
export default function Hint({ title, sx }) {
  return (
    <Tooltip title={title}>
      <InfoOutlinedIcon
        aria-label={typeof title === "string" ? title : "Help"}
        sx={{
          fontSize: 16,
          marginLeft: "4px",
          opacity: 0.6,
          cursor: "help",
          verticalAlign: "middle",
          "&:hover": { opacity: 1 },
          ...sx,
        }}
      />
    </Tooltip>
  );
}

Hint.propTypes = {
  title: PropTypes.node.isRequired,
  sx: PropTypes.object,
};

import * as React from "react";
import PropTypes from "prop-types";
import { C } from "../../managers/Core";

import "./SourceCodeInterface.css";
require("petrel/css/dark.css");

import { CodeEditor } from "petrel";
import hljs from "highlight.js";

import Chip from "@mui/material/Chip";
import Grid from "@mui/material/Grid2";

import FileUploadIcon from "@mui/icons-material/FileUploadOutlined";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";

import Hint from "../Hint";

// cheat sheet for the Resin syntax of the rules, shown as a hint
const RULES_HELP = (
  <span style={{ fontSize: 12, lineHeight: 1.6 }}>
    <b>Sources</b> bring relations of map features into the rules:
    <br />
    <code>
      distance(primary) &lt;- source(&quot;/star_map/distance/primary&quot;,
      Density).
    </code>
    <br />
    <code>
      over(park) &lt;- source(&quot;/star_map/over/park&quot;, Probability).
    </code>
    <br />
    <b>Rules</b> combine them with <code>if</code>, <code>and</code>,{" "}
    <code>not</code> and comparisons:
    <br />
    <code>permits if distance(primary) &lt; 15.0.</code>
    <br />
    <b>Target</b>: the landscape is computed from one atom:
    <br />
    <code>permits -&gt; target(&quot;/landscape&quot;).</code>
  </span>
);

/*
  SourceCodeInterface Component
  - Display the source code editor using Petrel
  - Allow importing source code from a .pl file
  - Allow expanding/collapsing the editor view
  - Allow syntax highlighting for Prolog code
 */
export default function SourceCodeInterface({ showErrors }) {
  const [isExpanded, setIsExpanded] = React.useState(true);
  // whether the editor is empty, to outline it when a run is started without rules
  const [isEmpty, setIsEmpty] = React.useState(
    C().sourceMan.getSource().trim() === "",
  );
  const hiddenFileInput = React.useRef(null);
  let codeEditor = null;
  let isInit = false;

  // reset the file input to allow the same file to be uploaded again
  React.useEffect(() => {
    if (!isInit) {
      if (hiddenFileInput.current) {
        hiddenFileInput.current.setAttribute("onclick", "this.value=null;");
      }
      codeEditor = new CodeEditor(document.getElementById("editor"));
      codeEditor.setHighlighter((code) => hljs.highlight("prolog", code).value);
      codeEditor.setAutoCompleteHandler(C().autoComplete);
      codeEditor.create();
      const source = C().sourceMan.getSource();
      codeEditor.setValue(source);
      C().initCodeEditor(codeEditor);
    }
    isInit = true;

    return () => {
      C().sourceMan.setSource(codeEditor.getValue());
    };
  }, []);

  // Toggle the file input
  function toggleFile() {
    hiddenFileInput.current.click();
  }

  // to handle the user-selected file
  function handleChange(event) {
    if (event.target.files.length === 0) {
      return;
    }
    const file = event.target.files[0];
    const fileReader = new FileReader(file);
    fileReader.onloadend = () => {
      var source = fileReader.result;
      if (source.slice(-1) == "\n") {
        source += " ";
      }
      const codeEditor = C().getCodeEditor();
      if (codeEditor != null) {
        codeEditor.setValue(source);
        updateEmpty();
      }
    };
    fileReader.readAsText(file);
  }

  // track whether the editor is empty, and refresh the bottom bar when this changes
  function updateEmpty() {
    const codeEditor = C().getCodeEditor();
    const empty = codeEditor !== null && codeEditor.getValue().trim() === "";
    if (empty !== isEmpty) {
      setIsEmpty(empty);
      C().updateBottomBar();
    }
  }

  function reSize() {
    setIsExpanded(!isExpanded);
  }

  return (
    <Grid
      style={{
        width: "100%",
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
          marginLeft: "32px",
          marginTop: "2px",
        }}
      >
        {/* Import Source Button */}
        <Chip
          icon={<FileUploadIcon style={{ color: "#ffffff" }} />}
          onClick={toggleFile}
          label="Import source"
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
          onChange={handleChange}
          ref={hiddenFileInput}
          style={{ display: "none" }} // Make the file input element invisible
        />
        {/* Expand/Collapse Button */}
        <Chip
          icon={
            isExpanded ? (
              <ExpandMoreIcon style={{ color: "#ffffff" }} />
            ) : (
              <ExpandLessIcon style={{ color: "#ffffff" }} />
            )
          }
          onClick={reSize}
          label={isExpanded ? "Collapse" : "Expand"}
          variant="outlined"
          style={{
            color: "#ffffff",
            borderColor: "#7e86bd22",
            minWidth: "80px",
            marginLeft: "8px",
          }}
        />
        <Hint
          title={RULES_HELP}
          sx={{ color: "#ffffff", marginLeft: "12px" }}
        />
      </Grid>
      {/* Source Code Editor */}
      <div
        id="editorWrapper"
        className={showErrors && isEmpty ? "errorOutline" : ""}
        onInput={updateEmpty}
        onKeyUp={updateEmpty}
        style={{
          border: "1px solid #282C34",
          marginLeft: "32px",
          marginTop: "4px",
          width: "90%",
          borderRadius: "10px",
        }}
      >
        <div
          id="editor"
          style={{
            width: "100%",
            minHeight: isExpanded ? 400 : 80,
            maxHeight: isExpanded ? 400 : 80,
            textAlign: "start",
          }}
        >
          {" "}
        </div>
      </div>
    </Grid>
  );
}

SourceCodeInterface.propTypes = {
  showErrors: PropTypes.bool.isRequired,
};

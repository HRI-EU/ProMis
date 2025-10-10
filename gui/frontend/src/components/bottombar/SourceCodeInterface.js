import * as React from 'react';
import PropTypes from "prop-types";
import { C } from "../../managers/Core";

import "./SourceCodeInterface.css";
require('petrel/css/dark.css')

import { CodeEditor } from "petrel"
import hljs from "highlight.js";

import Chip from "@mui/material/Chip";
import Grid from "@mui/material/Grid2";

import FileUploadIcon from "@mui/icons-material/FileUploadOutlined";
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';


export default function SourceCodeInterface({highlightSourceElement}){
    const [isExpanded, setIsExpanded] = React.useState(false);
    const hiddenFileInput = React.useRef(null);
    let codeEditor = null
    let isInit = false

    // reset the file input to allow the same file to be uploaded again
    React.useEffect(() => {
        if (!isInit){
            if (hiddenFileInput.current) {
                hiddenFileInput.current.setAttribute("onclick", "this.value=null;");
            }
            codeEditor = new CodeEditor(document.getElementById("editor"));
            codeEditor.setHighlighter(code => hljs.highlight("prolog", code).value);
            codeEditor.setAutoCompleteHandler(C().autoComplete);
            codeEditor.create();
            const source = C().sourceMan.getSource();
            codeEditor.setValue(source);
            C().initCodeEditor(codeEditor);
        }
        isInit = true

        return () => {
            C().sourceMan.setSource(codeEditor.getValue());
        }
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
            }
        };
        fileReader.readAsText(file);
    }

    function reSize() {
        setIsExpanded(!isExpanded);
    }


    return (
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
                marginTop: "2px",
            }}
            >
                <Chip
                    icon={ <FileUploadIcon style={{ color: "#ffffff" }} /> }
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
                <Chip
                    icon={ 
                    isExpanded ? <ExpandMoreIcon style={{ color: "#ffffff" }} /> : <ExpandLessIcon style={{ color: "#ffffff" }} />
                    }
                    onClick={reSize}
                    label={isExpanded ? "Collapse" : "Expand"}
                    variant="outlined"
                    style={{
                        color: "#ffffff",
                        borderColor: "#7e86bd22",
                        minWidth: "80px",
                        marginLeft: "8px"
                    }}
                />
            
            </Grid>
            <div
                id="editorWrapper"
                className={highlightSourceElement ? "errorSignal": ""}
                style={{
                    border: "1px solid #282C34",
                    marginLeft: "32px",
                    marginTop: "4px",
                    width: "90%",
                    borderRadius: "10px"
                }}
            >
                <div 
                    id="editor"
                    style={{
                        width: "100%",
                        minHeight: isExpanded ? 400 : 80,
                        maxHeight: isExpanded ? 400 : 80,
                        textAlign: "start"
                    }}
                > </div>
            </div>
            
        </Grid>);
}

SourceCodeInterface.propTypes = {
    highlightSourceElement: PropTypes.bool.isRequired
}

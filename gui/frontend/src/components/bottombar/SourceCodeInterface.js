import * as React from 'react';
import PropTypes from "prop-types";

import "./SourceCodeInterface.css";

import hljs from "highlight.js";

import Chip from "@mui/material/Chip";
import Grid from "@mui/material/Grid2";

import FileUploadIcon from "@mui/icons-material/FileUploadOutlined";
import EditIcon from '@mui/icons-material/Edit';
import DoneIcon from '@mui/icons-material/Done';
import CloseIcon from "@mui/icons-material/CloseRounded";

export default function SourceCodeInterface({sourceCode, onEdit, highlightSourceElement}){
    const [inEdit, setInEdit] = React.useState(false);
    const codeRef = React.useRef(null);
    const hiddenFileInput = React.useRef(null);

    function hasSource(sourceCode) {
        return sourceCode !== "";
    }

    // reset the file input to allow the same file to be uploaded again
    React.useEffect(() => {
        if (hiddenFileInput.current) {
            hiddenFileInput.current.setAttribute("onclick", "this.value=null;");
        }
    }, []);

    React.useEffect(() => {
        if (codeRef.current === null){
            return;
        }
        codeRef.current.removeAttribute("data-highlighted");
        hljs.highlightAll(codeRef.current)
    });



    // Toggle the file input
    function toggleFile() {
        if (hasSource(sourceCode)) {
            onEdit("");
            return;
        }
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
            onEdit(source);
        };
        fileReader.readAsText(file);
    }

    function checkTab(element, event) {
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
            onEdit(element.value); // Update text to include indent
        }
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
                    icon={
                    hasSource(sourceCode) ? (
                        <CloseIcon style={{ color: "#ffffff" }} />
                    ) : (
                        <FileUploadIcon style={{ color: "#ffffff" }} />
                    )
                    }
                    onClick={toggleFile}
                    label={hasSource(sourceCode) ? "Remove source" : "Import source"}
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
                    inEdit ? (
                        <DoneIcon style={{ color: "#ffffff" }} />
                    ) : (
                        <EditIcon style={{ color: "#ffffff" }} />
                    )
                    }
                    onClick={() => {
                        setInEdit(!inEdit);
                    }}
                    label={inEdit ? "Done" : "Edit"}
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
                {inEdit ? 
                    <textarea id="editing"
                    className={highlightSourceElement ? "errorSignal": ""}
                    value={sourceCode}
                    onChange={(e) => onEdit(e.target.value)}
                    onKeyDown={(e) => checkTab(e.target, e)}
                    style={{
                        height: "200px",
                        color: "#ffffff",
                        paddingLeft: "16px",
                    }}
                    >
                    </textarea>
                    :
                    <pre
                    className={highlightSourceElement ? "errorSignal": ""}
                    id="highlighting"
                    >
                    <code 
                        id="codeBlock"
                        ref={codeRef}
                        className={hasSource(sourceCode) ? "prolog" : ""}
                    >
                        {sourceCode}
                    </code>
                    </pre>
                }
            </Grid>
        </Grid>);
}

SourceCodeInterface.propTypes = {
    sourceCode: PropTypes.string.isRequired,
    onEdit: PropTypes.func,
    highlightSourceElement: PropTypes.bool.isRequired
}

import * as React from 'react';
import PropTypes from "prop-types";
import { C } from "../../managers/Core";

import "./SourceCodeInterface.css";
require('petrel/css/dark.css')

import { CodeEditor } from "petrel"

import Chip from "@mui/material/Chip";
import Grid from "@mui/material/Grid2";

import FileUploadIcon from "@mui/icons-material/FileUploadOutlined";
import EditIcon from '@mui/icons-material/Edit';
import DoneIcon from '@mui/icons-material/Done';
import CloseIcon from "@mui/icons-material/CloseRounded";

export default function SourceCodeInterface({sourceCode, onEdit, highlightSourceElement}){
    const [inEdit, setInEdit] = React.useState(false);
    const hiddenFileInput = React.useRef(null);
    let codeEditor = null
    let isInit = false

    function hasSource(sourceCode) {
        return sourceCode !== "";
    }

    // reset the file input to allow the same file to be uploaded again
    React.useEffect(() => {
        if (!isInit){
            if (hiddenFileInput.current) {
                hiddenFileInput.current.setAttribute("onclick", "this.value=null;");
            }
            console.log(highlightSourceElement)
            codeEditor = new CodeEditor(document.getElementById("editor"))
            codeEditor.setAutoCompleteHandler(C().autoComplete) 
            codeEditor.create()
        }
        isInit = true
    }, []);

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

            <div 
                id="editor"
                style={{
                    width: "100%",
                    height: 200
                }}
            > </div>
        </Grid>);
}

SourceCodeInterface.propTypes = {
    sourceCode: PropTypes.string.isRequired,
    onEdit: PropTypes.func,
    highlightSourceElement: PropTypes.bool.isRequired
}

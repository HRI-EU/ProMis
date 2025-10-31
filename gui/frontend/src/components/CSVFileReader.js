// CSVFileReader.js
import React, { useEffect } from "react";
import CSVReader from "react-csv-reader";
import "./CSVFileReader.css"; // Import the CSS file for styling
import PropTypes from "prop-types";
import { useRef } from "react";


/*
  This is a helper component to handle CSV File Reader on sidebar right.
  @props: onFileLoaded(data: number[][], fileinfo)
*/
const CSVFileReader = ({ onFileLoaded }) => {
  const componentRef = useRef(null);
  const handleFileLoaded = (data, fileInfo) => {
    // Ensure the file is selected before processing
    if (fileInfo && fileInfo.name) {
      // Generate a unique id using the current timestamp

      onFileLoaded(data, { ...fileInfo });
    } else {
      console.error("Invalid file or file not selected.");
      // You can add additional error handling or display a message to the user
    }
  };

  // allow the user to select the same file again
  useEffect(() => {
    if (componentRef.current) {
      componentRef.current.setAttribute("onclick", "this.value=null;");
    }
  }, [componentRef]);

  CSVFileReader.propTypes = {
    onFileLoaded: PropTypes.func.isRequired,
  };

  return (
    <CSVReader
      cssClass="csv-reader-input" // Add a CSS class for styling
      label="Add layer" // Set the label text
      onFileLoaded={handleFileLoaded}
      inputId="csv-reader-input" // Set a unique input ID
      aria-controls="csv-reader-input"
      ref={componentRef}
    />
  );
};

export default CSVFileReader;

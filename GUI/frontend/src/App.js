// App.js
import React from "react";
import MapComponent from "./components/MapComponent";
import "./App.css";
import { BrowserRouter as Router } from "react-router-dom";

function App() {
  return (
    <Router>
      <div className="App">
        <MapComponent />
      </div>
    </Router>
  );
}

export default App;

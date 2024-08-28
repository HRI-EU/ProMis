# GUI for PMD

This is a software project designed for visualizing ProMis output and CSV data of the probability distribution of drones.

The project is based on React.js and Leaflet.

## Installation and Deployment

### Requirements

- [Node.js](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) is required for using the npm package manager.
- [Python > 3.9](https://www.python.org/downloads/) is required for the backend. We recommend using [virtual environments](https://docs.python.org/3/library/venv.html) to install the dependancies.
    - [ProMis](https://github.com/HRI-EU/ProMis) for Probabilistic Mission Design.
    - [FastAPI](https://fastapi.tiangolo.com/) for the backend server.

You can then start the backend server with:

### `fastapi run ./backend/main.py`

In the frontend project directory, you can run:

### `npm start`

Runs the app in the development mode.\
Open [http://localhost:3000](http://localhost:3000) to view it in your browser.

The page will reload when you make changes.\
You may also see any lint errors in the console.

### Install with docker

You can also install the program with docker by running:

### `docker compose up`

## First Steps

### Import CSV file as a new layer

To instantiate a new layer of points and the corresponding probability values, simply expand the right sidebar by clicking on the top-right button and select "new layer".

The CSV file should be in the following format:

```csv
latitude,longitude,value
49.8821815378995,8.647164642182332,7.211102772335674
49.87696708632973,8.658434392066596,0.528400372434818
49.87759650141061,8.65231293292399,57.450293181169556
```

### Modify Layer Visualization

Once you've imported a layer, there will be five buttons:

* Move upwards in the layer hierarchy.
* Move downwards in the layer hierarchy.
* Center it on the map.
* Open palette menu: you can pick one pre-defined hue, or use the hue slider. You can also change the opacity. The saturation depends on the value of the point.
* Settings: Select render mode(Heatmap/Voronoi), radius, filter value range, and delete layer.

## Import and Export

To save your project with multiple layers, simply expand the left sidebar and click on "export project". This will export your project as a Json file. Later you can import it again via the button below.

### Export Geojson

Geojson can be exported in the left sidebar for all the layers. You can also choose to export selected layer in the setting of right sidebar.

### run a model

dc-problog models can be imported in the bottom bar. This will display the code and highlight it. You can configure your run by selecting an origin, height and width of the mission. The resolution can also be configure to have better precision.

## Add and Remove Markers

To mark the positions of drones and landing strips, simply use the buttons on the lefttop corner.

You can move and delete them by the arrow and eraser buttons as well.

## Weather information

Click on the bottom left button to see the temperature, precipitation and atmospheric pressure at the center of the position. Note: Data outside Germany is unavailable.

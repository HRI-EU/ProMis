# Example Usage

## Import CSV file as a new layer

To instantiate a new layer of points and the corresponding probability values, simply expand the right sidebar by clicking on the top-right button and select "new layer".
ProMis provides easy access to its data in the form of CSV files.
The GUI can import and visualize such data 

If you would like to import data from other applications, the CSV file should be in the following format:

```csv
latitude,longitude,value
49.8821815378995,8.647164642182332,7.211102772335674
49.87696708632973,8.658434392066596,0.528400372434818
49.87759650141061,8.65231293292399,57.450293181169556
```

## Modify Layer Visualization

Once you've imported a layer, there will be five buttons:

* Move upwards in the layer hierarchy.
* Move downwards in the layer hierarchy.
* Center it on the map.
* Open palette menu: you can pick one pre-defined hue, or use the hue slider. You can also change the opacity. The saturation depends on the value of the point.
* Settings: Select render mode(Heatmap/Voronoi), radius, filter value range, and delete layer.

## Import and Export

To save your project with multiple layers, simply expand the left sidebar and click on "export project". 
This will export your project as a Json file. Later you can import it again via the button below.

Geojson can be exported in the left sidebar for all the layers. 
You can also choose to export selected layer in the setting of right sidebar.

## Add and Remove Markers

To mark the positions of drones and landing strips, simply use the buttons on the lefttop corner.
You can move and delete them by the arrow and eraser buttons as well.

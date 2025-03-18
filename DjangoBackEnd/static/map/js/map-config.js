// map-config.js - Basic map setup and initialization
const map = new maplibregl.Map({
    container: 'map',
    style: 'https://victor2.tftservice.no/styles/osm-bright/style.json', // Use predefined style from Victor's server
    center: [18.9553, 69.6496], // Tromsø
    zoom: 10
});

// Initialize Mapbox Draw control
const draw = new MapboxDraw({
    displayControlsDefault: false,
    styles: [
        { "id": "gl-draw-point", "type": "circle", "filter": ["==", "$type", "Point"] },
        { "id": "gl-draw-line", "type": "line", "filter": ["==", "$type", "LineString"], "paint": { "line-color": "#FF0000", "line-width": 3, "line-dasharray": [0.2, 2] } },
        { "id": "gl-draw-polygon-fill", "type": "fill", "filter": ["==", "$type", "Polygon"], "paint": { "fill-color": "#FF0000", "fill-opacity": 0.3 } },
        { "id": "gl-draw-polygon-stroke", "type": "line", "filter": ["==", "$type", "Polygon"], "paint": { "line-color": "#FF0000", "line-width": 2 } }
    ]
});

// Add the drawing control to the map
map.addControl(draw);

// Global variables
let geojsonData = null;
const API_BASE_URL = "http://127.0.0.1:8000/api/locations/";
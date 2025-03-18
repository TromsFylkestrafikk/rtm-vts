// map-layers.js - Layer definitions and functions

// Add custom vector tile source
map.on('load', () => {
    // Define vector tile source - the same source as in map-config.js
    map.addSource('custom-tiles', {
        type: 'vector',
        tiles: ['https://victor2.tftservice.no/data/norway-vector/{z}/{x}/{y}.pbf'],
        minzoom: 0,
        maxzoom: 14
    });

    // Layers to add
    const layers = [
        { id: "roads-layer", type: "line", sourceLayer: "transportation", paint: { "line-color": "#B0BEC5", "line-width": 3 } },
        { id: "forest-layer", type: "fill", sourceLayer: "landcover", paint: { "fill-color": "#6aeb86", "fill-opacity": 0.5 } },
        { id: "water", type: "fill", sourceLayer: "water", paint: { "fill-color": "#64B5F6", "fill-opacity": 0.5 } },
        { id: "landuse", type: "fill", sourceLayer: "landuse", paint: { "fill-color": "#FFD54F", "fill-opacity": 0.5 } },
        { id: "landcover", type: "fill", sourceLayer: "landcover", paint: { "fill-color": "#e0ddb8", "fill-opacity": 0.5 } },
        { id: "building", type: "fill", sourceLayer: "building", paint: { "fill-color": "#A1887F", "fill-opacity": 0.5 } },
        { id: "boundary", type: "line", sourceLayer: "boundary", paint: { "line-color": "#b84600", "line-width": 0.5 } }
    ];

    // Add layers to map
    layers.forEach(layer => {
        map.addLayer({
            id: layer.id,
            type: layer.type,
            source: "custom-tiles", // Reference the correct source
            "source-layer": layer.sourceLayer, // The layer from the vector tile
            paint: layer.paint
        });
    });

    // Add text layers (Place names, transportation names, etc.)
    const textLayers = [
        { id: "place", sourceLayer: "place" },
        { id: "transportation_name", sourceLayer: "transportation_name" }
    ];

    textLayers.forEach(layer => {
        map.addLayer({
            id: layer.id,
            type: "symbol",
            source: "custom-tiles",
            "source-layer": layer.sourceLayer,
            layout: {
                "text-field": ["get", "name"],
                "text-font": ['Roboto Regular'],
                "text-size": 12,
                "text-allow-overlap": false,
                "text-max-width": 8,
                "symbol-spacing": 500
            },
            paint: {
                "text-color": "#000000",
                "text-halo-color": "#FFFFFF",
                "text-halo-width": 2,
                "text-opacity": 1
            }
        });
    });
});

// Function to update a map layer with new data
function updateLayer(id, type, data, paint) {
    // Remove existing layer and source if they exist
    if (map.getSource(id)) {
        map.removeLayer(id);
        map.removeSource(id);
    }

    // Add new source with filtered GeoJSON data
    map.addSource(id, {
        "type": "geojson",
        "data": {
            "type": "FeatureCollection",
            "features": data
        }
    });

    // Add new layer with the specified type and styles
    map.addLayer({
        "id": id,
        "type": type,
        "source": id,
        "paint": paint,
        "layout": { "visibility": data.length > 0 ? "visible" : "none" }
    });
}

// Function to add all data layers to the map
function addAllLayers(data) {
    const points = data.features.filter(f => f.geometry.type === "Point");
    const lines = data.features.filter(f => f.geometry.type === "LineString");

    updateLayer("locations-layer", "circle", points, { 
        "circle-radius": 6, 
        "circle-color": ['match', ['get', 'severity'], 
            'none', '#7e4da3', 
            'low', '#FFFF00', 
            'high', '#FFA500', 
            'highest', '#FF0000', 
            'unknown', '#808080', 
            '#0000FF'
        ] 
    });
    
    updateLayer("line-layer", "line", lines, { 
        "line-color": ['match', ['get', 'severity'], 
            'none', '#7e4da3', 
            'low', '#FFFF00', 
            'high', '#FFA500', 
            'highest', '#FF0000', 
            'unknown', '#808080', 
            '#0000FF'
        ], 
        "line-width": 4 
    });

    // Add click handlers for popups
    map.on('click', 'locations-layer', function (e) {
        const { name, description = "No description", comment, severity, situation_type } = e.features[0].properties;
        new maplibregl.Popup()
            .setLngLat(e.features[0].geometry.coordinates)
            .setHTML(`<h3>${name}</h3>
                    <p>${description}</p>
                    <hr>
                    <p><strong>Comments:</strong> ${comment}</p>
                    <p><strong>Situation Type:</strong> ${situation_type}</p>
                    <p><strong>Severity:</strong> ${severity}</p>`)
            .addTo(map);
    });
}

// Function to toggle visibility of the points layer
function togglePointVisibility(isVisible) {
    map.setLayoutProperty('locations-layer', 'visibility', isVisible ? 'visible' : 'none');
}

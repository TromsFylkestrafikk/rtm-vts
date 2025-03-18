// Reference to the HTML element that displays coordinates
const coordinates = document.createElement('div');
coordinates.id = 'coordinates';
document.body.appendChild(coordinates);


// Event listener for drawing completion
map.on('draw.create', (e) => {
    const feature = e.features[0];
    if (!feature) return;

    // Extract coordinates from the drawn feature
    const coords = feature.geometry.type === 'Polygon' ? 
        feature.geometry.coordinates[0] : 
        feature.geometry.coordinates;

    // Display coordinates in the HTML element
    coordinates.innerHTML = `Coordinates:<br />${coords.map(coord => 
        `Lng: ${coord[0].toFixed(5)}, Lat: ${coord[1].toFixed(5)}`).join('<br />')}`;

    // Show coordinates in a popup on the map
    new maplibregl.Popup()
        .setLngLat(coords[0])
        .setHTML(`<strong>Coordinates:</strong><br>Lng: ${coords[0][0].toFixed(5)}<br>Lat: ${coords[0][1].toFixed(5)}`)
        .addTo(map);
});
async function populateDropdowns() {
    try {
        const response = await fetch('/api/filter-options/');
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Populate county dropdown
        const countyDropdown = document.getElementById("county-dropdown");
        data.counties.forEach(county => {
            const option = document.createElement("option");
            option.value = county;
            option.textContent = county;
            countyDropdown.appendChild(option);
        });
        
        // Populate situation dropdown
        const situationDropdown = document.getElementById("situation-dropdown");
        data.situation_types.forEach(type => {
            const option = document.createElement("option");
            option.value = type;
            option.textContent = type;
            situationDropdown.appendChild(option);
        });

        // Corrected: use data.severities (plural)
        const severityDropdown = document.getElementById("severity-dropdown");
        data.severities.forEach(severity => {
            const option = document.createElement("option");
            option.value = severity;
            option.textContent = severity.charAt(0).toUpperCase() + severity.slice(1);
            severityDropdown.appendChild(option);
        });
    } catch (error) {
        console.error("❌ Error populating dropdowns:", error);
    }
}
// Initial data load
document.addEventListener('DOMContentLoaded', async function () {
    try {
        const response = await fetch(API_BASE_URL);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        geojsonData = await response.json();

        // Validate fetched data
        if (!geojsonData?.features) {
            throw new Error("❌ Invalid GeoJSON data format!");
        }

        console.log("📡 API Data Fetched:", geojsonData);
        
        // Populate dropdowns
        populateDropdowns();
        
        // Add map layers
        addAllLayers(geojsonData);
        
        // Populate transit list with buttons
        populateTransitList(geojsonData);
        
        // Add debug information
        console.log("🚏 Transit list populated with:", 
                    geojsonData.features.filter(f => f.geometry.type === "Point").length,
                    "point features");
    } catch (error) {
        console.error("❌ Error fetching locations:", error);
    }
});

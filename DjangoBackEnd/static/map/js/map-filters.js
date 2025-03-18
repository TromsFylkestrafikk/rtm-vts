// Reference to the HTML element that displays coordinates
const coordinates = document.createElement('div');
coordinates.id = 'coordinates';
document.body.appendChild(coordinates);

// Populates the transit list with checkboxes for each point feature
function populateTransitList(data) {
    const transitList = document.getElementById("transit-list");
    if (!transitList) return console.error("❌ 'transit-list' element not found!");
    
    transitList.innerHTML = "";
    
    data.features
        .filter(f => f.geometry.type === "Point")
        .forEach(item => {
            const listItem = document.createElement("li");
            
            const label = document.createElement("label");
            label.textContent = item.properties.name || "Unnamed Location";
            
            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.checked = true;
            checkbox.dataset.id = item.properties.id;
            
            checkbox.addEventListener("change", () => {
                // Toggle visibility of this specific point if possible
                // As a fallback, toggle all points
                togglePointVisibility(checkbox.checked);
            });
            
            listItem.appendChild(label);
            listItem.appendChild(checkbox);
            transitList.appendChild(listItem);
        });
}

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
        populateDropdowns();
        populateCountyDropdown(geojsonData);
        populateSituationDropdown(geojsonData);
        addAllLayers(geojsonData);
        populateTransitList(geojsonData);
    } catch (error) {
        console.error("❌ Error fetching locations:", error);
    }
});

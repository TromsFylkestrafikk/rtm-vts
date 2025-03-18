// Populate the county dropdown with unique county names
function populateCountyDropdown(data) {
    const counties = new Set(data.features.map(f => f.properties?.county).filter(Boolean));
    const countyDropdown = document.getElementById("county-dropdown");
    countyDropdown.innerHTML = '<option value="">Select County</option>';
    counties.forEach(county => countyDropdown.appendChild(new Option(county, county)));
    console.log("✅ County dropdown populated.");
}

// Populate the situation type dropdown
function populateSituationDropdown(data) {
    const situations = new Set(data.features.map(f => f.properties?.situation_type).filter(Boolean));
    const situationDropdown = document.getElementById("situation-dropdown");
    situationDropdown.innerHTML = '<option value="">All Situation Types</option>';
    situations.forEach(situation => situationDropdown.appendChild(new Option(situation, situation)));
    console.log("✅ Situation dropdown populated.");
}

// Update the map with filtered data
function updateMapWithFilteredData(filteredFeatures) {
    updateLayer("locations-layer", "circle", 
        filteredFeatures.filter(f => f.geometry.type === "Point"), 
        {
            "circle-radius": 6, 
            "circle-color": ['match', ['get', 'severity'], 
                'none', '#7e4da3', 
                'low', '#FFFF00', 
                'high', '#FFA500', 
                'highest', '#FF0000', 
                'unknown', '#808080', 
                '#0000FF'
            ]
        }
    );

    updateLayer("line-layer", "line", 
        filteredFeatures.filter(f => f.geometry.type === "LineString"), 
        {
            "line-color": ['match', ['get', 'severity'], 
                'none', '#7e4da3', 
                'low', '#FFFF00', 
                'high', '#FFA500', 
                'highest', '#FF0000', 
                'unknown', '#808080', 
                '#0000FF'
            ],
            "line-width": 4
        }
    );
}

// Combined filter function for both county and situation type
function updateFilters() {
    if (!geojsonData) return;
    
    const selectedCounty = document.getElementById("county-dropdown").value.trim().toLowerCase();
    const selectedSituation = document.getElementById("situation-dropdown").value.trim().toLowerCase();
    
    const filteredFeatures = geojsonData.features.filter(f => {
        const countyMatch = !selectedCounty || 
            f.properties?.county?.trim().toLowerCase() === selectedCounty;
        const situationMatch = !selectedSituation || 
            f.properties?.situation_type?.trim().toLowerCase() === selectedSituation;
        return countyMatch && situationMatch;
    });
    
    updateMapWithFilteredData(filteredFeatures);
}

// Function to fetch data with filters from the API

async function fetchFilteredData() {
    const countyValue = document.getElementById("county-dropdown").value;
    const situationValue = document.getElementById("situation-dropdown").value;
    
    let url = API_BASE_URL;
    const params = new URLSearchParams();
    
    if (countyValue) params.append('county', countyValue);
    if (situationValue) params.append('situation_type', situationValue);
    
    if (params.toString()) {
        url += "?" + params.toString();
    }
    
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        geojsonData = await response.json();
        
        // Update the map with the filtered data
        addAllLayers(geojsonData);
        populateTransitList(geojsonData);
    } catch (error) {
        console.error("❌ Error fetching filtered data:", error);
    }
}

// Event listeners for dropdowns
document.getElementById("county-dropdown").addEventListener("change", fetchFilteredData);
document.getElementById("situation-dropdown").addEventListener("change", fetchFilteredData);
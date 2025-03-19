console.log("Trip search script loaded");
document.addEventListener('DOMContentLoaded', function() {
    const tripSearchForm = document.getElementById('trip-search-form');
    console.log("trip-search");
    if (tripSearchForm) {
        console.log("Trip search form found!");
    } else {
        console.error("Trip search form NOT found!");
    }

    tripSearchForm.addEventListener('submit', function(e) {
        e.preventDefault();

        const fromLocation = document.getElementById('from').value;
        const toLocation = document.getElementById('to').value;

        console.log("Submitting trip search:", fromLocation, toLocation);

        fetch("{% url 'trip' %}", {
            method: 'POST',
            headers: {
                'X-CSRFToken': '{{ csrf_token }}',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: new URLSearchParams({
                'from': fromLocation,
                'to': toLocation
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log("Trip response:", data);
            if (data.geojson) {
                renderTripMap(data.geojson);
            } else {
                alert("Could not find a route");
            }
        })
        .catch(error => {
            console.error("Error fetching trip:", error);
            alert("An error occurred while fetching the trip.");
        });
    });

    function renderTripMap(geojsonData) {
        console.log("Rendering map with:", geojsonData);
    }
});

document.addEventListener("DOMContentLoaded", function() {
    const startDateInput = document.getElementById("start-date");
    const endDateInput = document.getElementById("end-date");
    const fetchDataButton = document.getElementById("fetch-data");
    const chartsContainer = document.getElementById("charts-container");

    fetchDataButton.addEventListener("click", function() {
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;

        if (!startDate || !endDate) {
            alert("Please select both start and end dates.");
            return;
        }

        fetchData(startDate, endDate);
    });

    function fetchData(startDate, endDate) {
        const nasaDataUrl = `/nasa_data?start=${startDate}&end=${endDate}`;
        const historyDataUrl = `/history?start=${startDate}&end=${endDate}`;

        Promise.all([
            fetch(nasaDataUrl).then(response => response.json()),
            fetch(historyDataUrl).then(response => response.json())
        ])
        .then(data => {
            const nasaData = data[0];
            const historyData = data[1];

            updateCharts(nasaData.data, historyData);
        })
        .catch(error => {
            console.error("Error fetching data:", error);
        });
    }

    function updateCharts(nasaData, historyData) {
        // Clear existing charts
        chartsContainer.innerHTML = "";

        // Render new charts with the fetched data
        renderNasaChart(nasaData);
        renderHistoryChart(historyData);
    }

    function renderNasaChart(data) {
        // Implementation for rendering NASA data chart
    }

    function renderHistoryChart(data) {
        // Implementation for rendering history data chart
    }
});
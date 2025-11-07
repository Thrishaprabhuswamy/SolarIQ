const ctxSolar = document.getElementById('solarChart').getContext('2d');
const ctxLoad = document.getElementById('loadChart').getContext('2d');
const ctxCombined = document.getElementById('combinedChart').getContext('2d');

let solarChart, loadChart, combinedChart;

function fetchData(startDate, endDate) {
    const url = `/nasa_data?start=${startDate}&end=${endDate}`;
    return fetch(url)
        .then(response => response.json())
        .then(data => {
            return data.data; // Assuming data.data contains the relevant data
        });
}

function fetchLoadData(startDate, endDate) {
    const url = `/history?start=${startDate}&end=${endDate}`;
    return fetch(url)
        .then(response => response.json())
        .then(data => {
            return data; // Assuming data contains the relevant load data
        });
}

function updateCharts(solarData, loadData) {
    const solarLabels = solarData.map(entry => entry.date);
    const solarValues = solarData.map(entry => entry.solar);
    const loadValues = loadData.map(entry => entry.load);

    if (solarChart) {
        solarChart.destroy();
    }
    if (loadChart) {
        loadChart.destroy();
    }
    if (combinedChart) {
        combinedChart.destroy();
    }

    solarChart = new Chart(ctxSolar, {
        type: 'line',
        data: {
            labels: solarLabels,
            datasets: [{
                label: 'Solar Generation',
                data: solarValues,
                borderColor: 'rgba(255, 206, 86, 1)',
                fill: false
            }]
        }
    });

    loadChart = new Chart(ctxLoad, {
        type: 'line',
        data: {
            labels: solarLabels,
            datasets: [{
                label: 'Load',
                data: loadValues,
                borderColor: 'rgba(54, 162, 235, 1)',
                fill: false
            }]
        }
    });

    combinedChart = new Chart(ctxCombined, {
        type: 'line',
        data: {
            labels: solarLabels,
            datasets: [{
                label: 'Solar Generation',
                data: solarValues,
                borderColor: 'rgba(255, 206, 86, 1)',
                fill: false
            }, {
                label: 'Load',
                data: loadValues,
                borderColor: 'rgba(54, 162, 235, 1)',
                fill: false
            }]
        }
    });
}

document.getElementById('dateRangeForm').addEventListener('submit', function(event) {
    event.preventDefault();
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;

    Promise.all([fetchData(startDate, endDate), fetchLoadData(startDate, endDate)])
        .then(([solarData, loadData]) => {
            updateCharts(solarData, loadData);
        })
        .catch(error => {
            console.error('Error fetching data:', error);
        });
});
// Visualization.js - Handles data visualization for the scraped content

document.addEventListener('DOMContentLoaded', function() {
    // Initialize visualizations if we're on the visualization page
    const chartContainer = document.getElementById('chart_container');
    if (chartContainer) {
        initializeCharts();
    }
    
    // Handle view toggle buttons
    const viewButtons = document.querySelectorAll('.view-toggle-btn');
    viewButtons.forEach(button => {
        button.addEventListener('click', function() {
            const viewType = this.getAttribute('data-view');
            toggleView(viewType);
        });
    });
    
    // Load preferred view on page load
    loadPreferredView();
    
    // Initialize filter functionality
    const filterInput = document.getElementById('filter_content');
    if (filterInput) {
        filterInput.addEventListener('input', function() {
            filterItems(this.value);
        });
    }
});

// Initialize charts using Chart.js
function initializeCharts() {
    const sessionId = document.getElementById('session_id').value;
    
    // Fetch data for charts
    fetch(`/api/data/${sessionId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            createElementTypeChart(data);
            createContentLengthChart(data);
        })
        .catch(error => {
            console.error('Error fetching data for charts:', error);
            document.getElementById('chart_container').innerHTML = 
                '<div class="alert alert-danger">Error loading charts. Please try again later.</div>';
        });
}

// Create chart showing distribution of element types
function createElementTypeChart(data) {
    const elementTypes = {};
    
    // Count element types
    data.items.forEach(item => {
        const type = item.element_type || 'unknown';
        elementTypes[type] = (elementTypes[type] || 0) + 1;
    });
    
    // Prepare data for chart
    const labels = Object.keys(elementTypes);
    const counts = Object.values(elementTypes);
    
    // Define colors for chart
    const backgroundColors = [
        'rgba(54, 162, 235, 0.6)',
        'rgba(255, 99, 132, 0.6)',
        'rgba(255, 206, 86, 0.6)',
        'rgba(75, 192, 192, 0.6)',
        'rgba(153, 102, 255, 0.6)',
        'rgba(255, 159, 64, 0.6)',
        'rgba(199, 199, 199, 0.6)'
    ];
    
    // Repeat colors if we have more element types than colors
    const chartColors = labels.map((_, i) => backgroundColors[i % backgroundColors.length]);
    
    // Create the chart
    const ctx = document.getElementById('element_type_chart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: counts,
                backgroundColor: chartColors,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                },
                title: {
                    display: true,
                    text: 'Element Types Distribution',
                    color: '#f8f9fa'
                }
            }
        }
    });
}

// Create chart showing content length distribution
function createContentLengthChart(data) {
    // Group content by length ranges
    const lengthRanges = {
        'Empty': 0,
        '1-10 chars': 0,
        '11-50 chars': 0,
        '51-100 chars': 0,
        '101-500 chars': 0,
        '500+ chars': 0
    };
    
    // Count items in each range
    data.items.forEach(item => {
        const length = item.content ? item.content.length : 0;
        
        if (length === 0) {
            lengthRanges['Empty']++;
        } else if (length <= 10) {
            lengthRanges['1-10 chars']++;
        } else if (length <= 50) {
            lengthRanges['11-50 chars']++;
        } else if (length <= 100) {
            lengthRanges['51-100 chars']++;
        } else if (length <= 500) {
            lengthRanges['101-500 chars']++;
        } else {
            lengthRanges['500+ chars']++;
        }
    });
    
    // Prepare data for chart
    const labels = Object.keys(lengthRanges);
    const counts = Object.values(lengthRanges);
    
    // Create the chart
    const ctx = document.getElementById('content_length_chart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Number of Elements',
                data: counts,
                backgroundColor: 'rgba(75, 192, 192, 0.6)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#f8f9fa'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                x: {
                    ticks: {
                        color: '#f8f9fa'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Content Length Distribution',
                    color: '#f8f9fa'
                }
            }
        }
    });
}

// Filter items based on search input
function filterItems(searchTerm) {
    searchTerm = searchTerm.toLowerCase();
    const items = document.querySelectorAll('.data-item');
    let matchCount = 0;
    
    items.forEach(item => {
        const content = item.querySelector('.item-content').textContent.toLowerCase();
        if (content.includes(searchTerm)) {
            item.style.display = '';
            matchCount++;
        } else {
            item.style.display = 'none';
        }
    });
    
    // Update the filter info
    const filterInfo = document.getElementById('filter_info');
    if (filterInfo) {
        if (searchTerm) {
            filterInfo.textContent = `Showing ${matchCount} matching items`;
            filterInfo.style.display = 'block';
        } else {
            filterInfo.style.display = 'none';
        }
    }
}

// Export functionality
function exportData(format) {
    const sessionId = document.getElementById('session_id').value;
    window.location.href = `/export/${format}/${sessionId}`;
}

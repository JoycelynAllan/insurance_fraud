/**
 * Dashboard functionality for AI Fraud Detection System
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Set up date range picker if element exists
    if (document.getElementById('dashboard-daterange')) {
        setupDateRangePicker();
    }

    // Set up refresh button if it exists
    const refreshBtn = document.getElementById('refresh-dashboard');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            refreshDashboardData();
        });
    }

    // Set up the time interval selector
    const timeIntervalSelect = document.getElementById('time-interval');
    if (timeIntervalSelect) {
        timeIntervalSelect.addEventListener('change', function() {
            fetchTimeSeriesData(this.value);
        });
    }

    // Load initial data
    fetchDashboardStats();
});

/**
 * Set up date range picker
 */
function setupDateRangePicker() {
    // This is a placeholder for date range picker implementation
    // In a real implementation, you'd initialize a date range picker library
    
    const dateRangeSelect = document.getElementById('dashboard-date-preset');
    if (dateRangeSelect) {
        dateRangeSelect.addEventListener('change', function() {
            // Calculate date range based on selection
            const range = this.value;
            let startDate, endDate;
            const today = new Date();
            endDate = formatDate(today);
            
            if (range === 'today') {
                startDate = endDate;
            } else if (range === 'week') {
                const lastWeek = new Date(today);
                lastWeek.setDate(today.getDate() - 7);
                startDate = formatDate(lastWeek);
            } else if (range === 'month') {
                const lastMonth = new Date(today);
                lastMonth.setMonth(today.getMonth() - 1);
                startDate = formatDate(lastMonth);
            } else if (range === 'year') {
                const lastYear = new Date(today);
                lastYear.setFullYear(today.getFullYear() - 1);
                startDate = formatDate(lastYear);
            } else {
                // Default to last 30 days
                const thirtyDaysAgo = new Date(today);
                thirtyDaysAgo.setDate(today.getDate() - 30);
                startDate = formatDate(thirtyDaysAgo);
            }
            
            // Update any date range displays
            document.getElementById('date-range-display').textContent = `${startDate} to ${endDate}`;
            
            // Fetch new data with date range
            fetchDashboardData(startDate, endDate);
        });
    }
}

/**
 * Format date as YYYY-MM-DD
 */
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * Fetch dashboard stats from API
 */
function fetchDashboardStats(period = 'month') {
    // If the API route exists, fetch from there
    fetch(`/api/stats?period=${period}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updateDashboardStats(data);
        })
        .catch(error => {
            console.error('Error fetching dashboard stats:', error);
        });
}

/**
 * Fetch time series data from API
 */
function fetchTimeSeriesData(interval = 'day') {
    fetch(`/api/timeseries?interval=${interval}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            updateTimeSeriesChart(data);
        })
        .catch(error => {
            console.error('Error fetching time series data:', error);
        });
}

/**
 * Update dashboard stats with fetched data
 */
function updateDashboardStats(data) {
    // Update total transactions
    const totalTransactionsElement = document.getElementById('total-transactions');
    if (totalTransactionsElement) {
        totalTransactionsElement.textContent = data.total_transactions;
    }
    
    // Update fraud transactions
    const fraudTransactionsElement = document.getElementById('fraud-transactions');
    if (fraudTransactionsElement) {
        fraudTransactionsElement.textContent = data.fraud_transactions;
    }
    
    // Update fraud amount
    const fraudAmountElement = document.getElementById('fraud-amount');
    if (fraudAmountElement) {
        fraudAmountElement.textContent = `$${data.fraud_amount.toFixed(2)}`;
    }
    
    // Update fraud percentage
    const fraudPercentageElement = document.getElementById('fraud-percentage');
    if (fraudPercentageElement) {
        fraudPercentageElement.textContent = `${data.fraud_percentage.toFixed(2)}%`;
    }
    
    // Update category data if chart exists
    updateCategoryChart(data.merchant_categories);
}

/**
 * Update time series chart with new data
 */
function updateTimeSeriesChart(data) {
    const chartElement = document.getElementById('transactionsChart');
    if (!chartElement) return;
    
    const ctx = chartElement.getContext('2d');
    
    // Check if chart already exists and destroy it
    if (window.transactionsChart) {
        window.transactionsChart.destroy();
    }
    
    // Create new chart
    window.transactionsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [
                {
                    label: 'All Transactions',
                    data: data.total_counts,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3
                },
                {
                    label: 'Fraudulent Transactions',
                    data: data.fraud_counts,
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Transactions'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            }
        }
    });
}

/**
 * Update category chart with new data
 */
function updateCategoryChart(categoryData) {
    const chartElement = document.getElementById('categoryChart');
    if (!chartElement || !categoryData) return;
    
    const ctx = chartElement.getContext('2d');
    
    // Process category data
    const categories = Object.keys(categoryData).slice(0, 5);
    const fraudRates = categories.map(cat => categoryData[cat].fraud_rate);
    
    // Check if chart already exists and destroy it
    if (window.categoryChart) {
        window.categoryChart.destroy();
    }
    
    // Create new chart
    window.categoryChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categories,
            datasets: [{
                label: 'Fraud Rate (%)',
                data: fraudRates,
                backgroundColor: 'rgba(255, 159, 64, 0.7)',
                borderColor: 'rgba(255, 159, 64, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Fraud Rate (%)'
                    },
                    max: 100
                },
                x: {
                    title: {
                        display: true,
                        text: 'Merchant Category'
                    }
                }
            }
        }
    });
}

/**
 * Refresh all dashboard data
 */
function refreshDashboardData() {
    // Show loading indicator
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.classList.remove('d-none');
    }
    
    // Fetch fresh data
    Promise.all([
        fetchDashboardStats('month'),
        fetchTimeSeriesData('day')
    ])
    .then(() => {
        // Hide loading indicator
        if (loadingOverlay) {
            loadingOverlay.classList.add('d-none');
        }
        
        // Show success message
        const alertContainer = document.getElementById('alert-container');
        if (alertContainer) {
            const alertElement = document.createElement('div');
            alertElement.className = 'alert alert-success alert-dismissible fade show';
            alertElement.innerHTML = `
                <strong>Success!</strong> Dashboard data refreshed.
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            alertContainer.appendChild(alertElement);
            
            // Auto-remove the alert after 3 seconds
            setTimeout(() => {
                alertElement.classList.remove('show');
                setTimeout(() => alertElement.remove(), 150);
            }, 3000);
        }
    })
    .catch(error => {
        console.error('Error refreshing dashboard data:', error);
        
        // Hide loading indicator
        if (loadingOverlay) {
            loadingOverlay.classList.add('d-none');
        }
        
        // Show error message
        const alertContainer = document.getElementById('alert-container');
        if (alertContainer) {
            const alertElement = document.createElement('div');
            alertElement.className = 'alert alert-danger alert-dismissible fade show';
            alertElement.innerHTML = `
                <strong>Error!</strong> Failed to refresh dashboard data.
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            alertContainer.appendChild(alertElement);
        }
    });
}

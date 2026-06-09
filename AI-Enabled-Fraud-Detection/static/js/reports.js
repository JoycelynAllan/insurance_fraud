/**
 * Reports functionality for AI Fraud Detection System
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Set up delete buttons
    initDeleteButtons();
    
    // Set up download buttons
    initDownloadButtons();
});

/**
 * Initialize delete report buttons
 */
function initDeleteButtons() {
    const deleteButtons = document.querySelectorAll('button.btn-outline-danger[title="Delete"]');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Get the report ID from the closest <tr> or parent element
            const row = this.closest('tr');
            const reportTitle = row ? row.querySelector('td:first-child').textContent : 'this report';
            
            // Confirm deletion
            if (confirm(`Are you sure you want to delete "${reportTitle}"?`)) {
                // In a real implementation, this would send a delete request to the server
                // For now, we'll just remove the row to simulate deletion
                
                // Show a success message
                showMessage('success', `Report "${reportTitle}" deleted successfully.`);
                
                // Remove the row from the table
                if (row) {
                    row.classList.add('fade');
                    setTimeout(() => row.remove(), 300);
                }
            }
        });
    });
}

/**
 * Initialize PDF download buttons
 */
function initDownloadButtons() {
    const downloadButtons = document.querySelectorAll('button.btn-outline-secondary[title="Download PDF"]');
    
    downloadButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Get the report title
            const row = this.closest('tr');
            const reportTitle = row ? row.querySelector('td:first-child').textContent : 'Report';
            
            // In a real implementation, this would trigger a PDF download
            // For now, we'll just show a message
            showMessage('info', `Preparing PDF download for "${reportTitle}". This feature will be available soon.`);
        });
    });
    
    // Also handle the export buttons on the report view page
    const exportBtn = document.getElementById('exportTransactions');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            showMessage('info', 'Preparing export. This feature will be available soon.');
        });
    }
}

/**
 * Show a message to the user
 */
function showMessage(type, message) {
    // Create the alert element
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type} alert-dismissible fade show`;
    alertElement.role = 'alert';
    alertElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Find a container for the alert, or create one
    let alertContainer = document.getElementById('alert-container');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'alert-container';
        alertContainer.className = 'container mt-3';
        
        // Insert after the nav
        const nav = document.querySelector('nav');
        if (nav && nav.nextSibling) {
            nav.parentNode.insertBefore(alertContainer, nav.nextSibling);
        } else {
            // Fallback to prepending to body
            document.body.prepend(alertContainer);
        }
    }
    
    // Add the alert to the container
    alertContainer.appendChild(alertElement);
    
    // Auto-remove the alert after 5 seconds
    setTimeout(() => {
        alertElement.classList.remove('show');
        setTimeout(() => alertElement.remove(), 150);
    }, 5000);
}

/**
 * Filter reports by date range
 */
function filterReportsByDate(startDate, endDate) {
    // Get all report rows
    const rows = document.querySelectorAll('table tbody tr');
    
    // Convert input dates to Date objects
    const start = startDate ? new Date(startDate) : null;
    const end = endDate ? new Date(endDate) : null;
    
    // Filter each row
    rows.forEach(row => {
        // Get the date from the row (assuming date is in the 2nd column)
        const dateCell = row.querySelector('td:nth-child(2)');
        if (!dateCell) return;
        
        // Parse the date range
        const dateRange = dateCell.textContent.split('to');
        if (dateRange.length !== 2) return;
        
        // Get report end date (we'll filter based on this)
        const reportEndDate = new Date(dateRange[1].trim());
        
        // Check if the report falls within the filter range
        let showRow = true;
        
        if (start && reportEndDate < start) {
            showRow = false;
        }
        
        if (end && reportEndDate > end) {
            showRow = false;
        }
        
        // Show or hide the row
        row.style.display = showRow ? '' : 'none';
    });
}

/**
 * Generate a CSV export of report data
 */
function exportReportToCSV(reportData) {
    // Format the data as CSV
    let csvContent = 'data:text/csv;charset=utf-8,';
    
    // Add headers
    const headers = [
        'Transaction ID', 
        'Date', 
        'Merchant', 
        'Amount', 
        'Is Fraud',
        'Fraud Probability'
    ];
    csvContent += headers.join(',') + '\n';
    
    // Add data rows
    reportData.transactions.forEach(transaction => {
        const row = [
            transaction.transaction_id,
            transaction.timestamp,
            transaction.merchant,
            transaction.amount,
            transaction.is_fraud ? 'Yes' : 'No',
            (transaction.fraud_probability * 100).toFixed(2) + '%'
        ];
        csvContent += row.join(',') + '\n';
    });
    
    // Create download link
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', 'report_export.csv');
    document.body.appendChild(link);
    
    // Trigger download
    link.click();
    
    // Clean up
    document.body.removeChild(link);
}

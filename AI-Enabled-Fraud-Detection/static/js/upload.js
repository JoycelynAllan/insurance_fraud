/**
 * Upload functionality for AI Fraud Detection (fileName && fileSize && fileInfo) {
            fileName.textContent = file.name;
            fileSize.textContent = formatFileSize(file.size);
            fileInfo.style.display = 'block';
            dropArea.style.display = 'none';
        }
    }
    
    // Reset file selection
    function resetFileSelection() {
        fileInput.value = '';
        if (fileInfo && dropArea) {
            fileInfo.style.display = 'none';
            dropArea.style.display = 'block';
        }
    }
    
    // Validate the file
    function validateFile(file) {
        // Check if the file is a CSV
        if (!file.name.toLowerCase().endsWith('.csv')) {
            showError('Please select a CSV file.');
            return false;
        }
        
        // Check file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            showError('File size exceeds the maximum limit of 10MB.');
            return false;
        }
        
        return true;
    }
    
    // Show error message
    function showError(message) {
        // Create and show an alert
        const alertContainer = document.createElement('div');
        alertContainer.className = 'alert alert-danger alert-dismissible fade show mt-3';
        alertContainer.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Insert the alert before the drop area
        dropArea.parentNode.insertBefore(alertContainer, dropArea);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alertContainer.classList.remove('show');
            setTimeout(() => alertContainer.remove(), 150);
        }, 5000);
    }
    
    // Event: Browse button click
    browseBtn.addEventListener('click', function() {
        fileInput.click();
    });
    
    // Event: File input change
    fileInput.addEventListener('change', function() {
        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            if (validateFile(file)) {
                showFileInfo(file);
            } else {
                resetFileSelection();
            }
        }
    });
    
    // Event: Remove file button click
    if (removeFile) {
        removeFile.addEventListener('click', function() {
            resetFileSelection();
        });
    }
    
    // Event: Drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, function(e) {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, function() {
            dropArea.classList.add('highlight');
        }, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, function() {
            dropArea.classList.remove('highlight');
        }, false);
    });
    
    dropArea.addEventListener('drop', function(e) {
        const file = e.dataTransfer.files[0];
        
        if (file) {
            if (validateFile(file)) {
                fileInput.files = e.dataTransfer.files;
                showFileInfo(file);
            }
        }
    }, false);
    
    // Event: Form submit
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            if (fileInput.files.length === 0) {
                e.preventDefault();
                showError('Please select a file to upload!');
            } else {
                // Show loading state
                const submitBtn = uploadForm.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Uploading...';
                }
            }
        });
    }
}

/**
 * Initialize sample download functionality
 */
function initSampleDownload() {
    const sampleDownloadBtn = document.querySelector('a[href="#"][class*="btn-outline-primary"]');
    
    if (sampleDownloadBtn) {
        sampleDownloadBtn.addEventListener('click', function(e) {
            e.preventDefault();
            downloadSampleCSV();
        });
    }
}

/**
 * Generate and download a sample CSV file
 */
function downloadSampleCSV() {
    // Create sample data
    const sampleData = [
        ['transaction_id', 'amount', 'timestamp', 'merchant', 'merchant_category', 'description', 'location', 'ip_address', 'device_id'],
        ['tx_12345', '125.50', '2023-06-15 14:30:25', 'SuperMart', 'Retail', 'Weekly groceries', 'New York, NY', '192.168.1.1', 'device_abc123'],
        ['tx_12346', '75.20', '2023-06-15 16:42:10', 'EasyDine', 'Restaurant', 'Dinner with colleagues', 'New York, NY', '192.168.1.2', 'device_abc123'],
        ['tx_12347', '35.99', '2023-06-16 09:15:45', 'MorningCafe', 'Food', 'Breakfast meeting', 'Boston, MA', '192.168.1.3', 'device_abc123'],
        ['tx_12348', '99.99', '2023-06-16 13:20:30', 'TechStore', 'Electronics', 'USB-C charger', 'Boston, MA', '192.168.1.4', 'device_abc123'],
        ['tx_12349', '1250.00', '2023-06-17 11:05:15', 'LuxuryShop', 'Retail', 'Designer handbag', 'Los Angeles, CA', '192.168.1.5', 'device_def456'],
    ];
    
    // Convert to CSV format
    let csvContent = sampleData.map(row => row.join(',')).join('\n');
    
    // Create a blob and download link
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    
    // Create download link
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'sample_transactions.csv');
    link.style.display = 'none';
    
    // Add to DOM, trigger download, and clean up
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setTimeout(() => URL.revokeObjectURL(url), 100);
}

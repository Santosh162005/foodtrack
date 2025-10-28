// Main JavaScript for Food Expiry Tracker

// Upload Area Functionality
document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const imagePreview = document.getElementById('imagePreview');
    const previewImg = document.getElementById('previewImg');
    const ocrStatus = document.getElementById('ocrStatus');
    const foodNameInput = document.getElementById('foodName');
    const expiryDateInput = document.getElementById('expiryDate');
    const imagePathInput = document.getElementById('imagePath');

    // Set today's date as default for purchase date
    const today = new Date().toISOString().split('T')[0];
    const purchaseDateInput = document.getElementById('purchaseDate');
    if (purchaseDateInput) {
        purchaseDateInput.value = today;
    }

    // Click to upload
    if (uploadArea) {
        uploadArea.addEventListener('click', function() {
            fileInput.click();
        });
    }

    // Drag and drop
    if (uploadArea) {
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileUpload(files[0]);
            }
        });
    }

    // File input change
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                handleFileUpload(e.target.files[0]);
            }
        });
    }

    // Handle file upload
    function handleFileUpload(file) {
        // Validate file type
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp'];
        if (!allowedTypes.includes(file.type)) {
            showOCRStatus('error', 'Invalid file type. Please upload an image file.');
            return;
        }

        // Validate file size (16MB)
        if (file.size > 16 * 1024 * 1024) {
            showOCRStatus('error', 'File size too large. Maximum size is 16MB.');
            return;
        }

        // Show preview
        const reader = new FileReader();
        reader.onload = function(e) {
            previewImg.src = e.target.result;
            imagePreview.classList.remove('d-none');
        };
        reader.readAsDataURL(file);

        // Upload file
        uploadFile(file);
    }

    // Upload file to server
    function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        showOCRStatus('info', '<i class="spinner-border spinner-border-sm"></i> Processing image with AI OCR...');

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Auto-fill form
                if (data.food_name) {
                    foodNameInput.value = data.food_name;
                }
                if (data.expiry_date) {
                    expiryDateInput.value = data.expiry_date;
                }
                if (data.image_path) {
                    imagePathInput.value = data.image_path;
                }
                
                showOCRStatus('success', '✓ ' + data.message);
            } else {
                if (data.image_path) {
                    imagePathInput.value = data.image_path;
                }
                if (data.food_name) {
                    foodNameInput.value = data.food_name;
                }
                showOCRStatus('warning', '⚠ ' + data.message);
            }
        })
        .catch(error => {
            showOCRStatus('error', '✗ Error processing image: ' + error);
        });
    }

    // Show OCR status
    function showOCRStatus(type, message) {
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        };

        ocrStatus.innerHTML = `
            <div class="alert ${alertClass[type]} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
    }

    // Check for notifications on page load
    checkNotifications();
});

// Delete food item
function deleteFood(foodId) {
    if (confirm('Are you sure you want to delete this item?')) {
        fetch(`/delete_food/${foodId}`, {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error deleting item: ' + data.message);
            }
        })
        .catch(error => {
            alert('Error: ' + error);
        });
    }
}

// Handle delete button clicks using event delegation
document.addEventListener('DOMContentLoaded', function() {
    document.body.addEventListener('click', function(e) {
        if (e.target.closest('.delete-btn')) {
            const button = e.target.closest('.delete-btn');
            const foodId = button.getAttribute('data-food-id');
            if (foodId) {
                deleteFood(foodId);
            }
        }
    });
});

// Filter food items by status
const filterButtons = {
    'filterAll': null,
    'filterFresh': 'Fresh',
    'filterNearExpiry': 'Near Expiry',
    'filterExpired': 'Expired'
};

Object.keys(filterButtons).forEach(buttonId => {
    const button = document.getElementById(buttonId);
    if (button) {
        button.addEventListener('click', function() {
            filterTable(filterButtons[buttonId]);
        });
    }
});

function filterTable(status) {
    const table = document.getElementById('foodTable');
    if (!table) return;
    
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        if (status === null) {
            row.style.display = '';
        } else {
            const rowStatus = row.getAttribute('data-status');
            row.style.display = rowStatus === status ? '' : 'none';
        }
    });
}

// Check notifications
function checkNotifications() {
    fetch('/api/check_notifications')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.notifications && data.notifications.length > 0) {
                showNotifications(data.notifications);
            }
        })
        .catch(error => {
            console.error('Notification check error:', error);
        });
}

// Show notifications
function showNotifications(notifications) {
    const notificationHTML = notifications.map(msg => `<li>${msg}</li>`).join('');
    
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-warning alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.maxWidth = '500px';
    alertDiv.innerHTML = `
        <strong><i class="fas fa-bell"></i> Expiry Alerts!</strong>
        <ul class="mb-0 mt-2">
            ${notificationHTML}
        </ul>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-dismiss after 10 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 10000);
}

// Search functionality (optional enhancement)
function searchTable() {
    const input = document.getElementById('searchInput');
    if (!input) return;
    
    const filter = input.value.toLowerCase();
    const table = document.getElementById('foodTable');
    const rows = table.querySelectorAll('tbody tr');
    
    rows.forEach(row => {
        const foodName = row.cells[0].textContent.toLowerCase();
        const category = row.cells[1].textContent.toLowerCase();
        
        if (foodName.includes(filter) || category.includes(filter)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Export to CSV (optional feature)
function exportToCSV() {
    const table = document.getElementById('foodTable');
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(row => {
        const cols = row.querySelectorAll('td, th');
        const rowData = [];
        cols.forEach(col => {
            rowData.push(col.textContent.trim());
        });
        csv.push(rowData.join(','));
    });
    
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'food_items_' + new Date().toISOString().split('T')[0] + '.csv';
    a.click();
    window.URL.revokeObjectURL(url);
}

// Dark mode toggle (optional)
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    localStorage.setItem('darkMode', document.body.classList.contains('dark-mode'));
}

// Load dark mode preference
if (localStorage.getItem('darkMode') === 'true') {
    document.body.classList.add('dark-mode');
}

// Auto-refresh status every 5 minutes
setInterval(() => {
    if (window.location.pathname === '/index') {
        location.reload();
    }
}, 5 * 60 * 1000);

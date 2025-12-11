// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.querySelector('.menu-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
        });
    }
    
    // Close menu when clicking outside
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.nav-container')) {
            navMenu.classList.remove('active');
        }
    });
    
    // Image preview for scan page
    const imageInput = document.getElementById('waste-image');
    const imagePreview = document.getElementById('image-preview');
    
    if (imageInput && imagePreview) {
        imageInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                
                reader.addEventListener('load', function() {
                    imagePreview.src = this.result;
                    imagePreview.style.display = 'block';
                });
                
                reader.readAsDataURL(file);
            }
        });
    }
    
    // Auto-calculate points based on weight
    const weightInput = document.getElementById('weight');
    const pointsDisplay = document.getElementById('points-display');
    
    if (weightInput && pointsDisplay) {
        weightInput.addEventListener('input', function() {
            const weight = parseFloat(this.value) || 0;
            const points = Math.floor(weight * 10);
            pointsDisplay.textContent = points;
        });
    }
    
    // Update pickup status
    document.querySelectorAll('.update-status-btn').forEach(button => {
        button.addEventListener('click', function() {
            const pickupId = this.dataset.id;
            const currentStatus = this.dataset.status;
            
            // Show status update modal/interface
            const newStatus = prompt('Update status to (pending/confirmed/en_route/completed/cancelled):', currentStatus);
            
            if (newStatus && newStatus !== currentStatus) {
                fetch(`/update-pickup-status/${pickupId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `status=${newStatus}`
                })
                .then(response => {
                    if (response.ok) {
                        location.reload();
                    }
                });
            }
        });
    });
    
    // Fetch and display user stats
    if (document.querySelector('.user-stats')) {
        fetch('/api/user-stats')
            .then(response => response.json())
            .then(data => {
                if (!data.error) {
                    document.querySelectorAll('[data-stat="total_waste"]').forEach(el => {
                        el.textContent = `${data.total_waste}kg`;
                    });
                    document.querySelectorAll('[data-stat="total_points"]').forEach(el => {
                        el.textContent = data.total_points;
                    });
                    document.querySelectorAll('[data-stat="items_recycled"]').forEach(el => {
                        el.textContent = data.items_recycled;
                    });
                }
            });
    }
    
    // Load recycling companies for schedule form
    const companySelect = document.getElementById('company-select');
    if (companySelect) {
        fetch('/api/companies')
            .then(response => response.json())
            .then(companies => {
                companySelect.innerHTML = '<option value="">Select a recycling company</option>';
                companies.forEach(company => {
                    const option = document.createElement('option');
                    option.value = company.id;
                    option.textContent = `${company.name} - ${company.address}`;
                    companySelect.appendChild(option);
                });
            });
    }
});

// Geolocation for address autofill
function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(showPosition, showError);
    }
}

function showPosition(position) {
    // Reverse geocoding would be implemented here with a geocoding API
    console.log('Latitude:', position.coords.latitude);
    console.log('Longitude:', position.coords.longitude);
}

function showError(error) {
    console.log('Geolocation error:', error);
}
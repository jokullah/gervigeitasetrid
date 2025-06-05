/* 
Save as: advertise/static/advertise/js/projectpage_clean.js
CLEAN VERSION - Minimal, no buttons, no banners
*/

document.addEventListener('DOMContentLoaded', function() {
    console.log('🎯 ProjectPage advisor enhancement loading...');
    
    // Only run on ProjectPage editing - check for our specific class
    const projectPageAdvisorFields = document.querySelectorAll('.projectpage-advisor-checkboxes');
    
    if (projectPageAdvisorFields.length === 0) {
        console.log('🔍 No ProjectPage advisor fields found - skipping enhancement');
        return;
    }
    
    console.log('✅ Found', projectPageAdvisorFields.length, 'ProjectPage advisor fields');
    
    projectPageAdvisorFields.forEach((field, index) => {
        const fieldType = field.getAttribute('data-field') || `field-${index}`;
        console.log('🔧 Setting up', fieldType);
        
        // Get all checkboxes in this field
        const checkboxes = field.querySelectorAll('input[type="checkbox"]');
        console.log('📋 Found', checkboxes.length, 'checkboxes in', fieldType);
        
        // Enhanced checkbox styling - clean version (match ProjectAd)
        checkboxes.forEach(checkbox => {
            const label = checkbox.closest('label');
            if (label) {
                // Clean hover effects
                label.addEventListener('mouseenter', function() {
                    if (!checkbox.checked) {
                        this.style.backgroundColor = '#f0f7ff';
                        this.style.borderColor = '#0079bf';
                    }
                });
                
                label.addEventListener('mouseleave', function() {
                    if (!checkbox.checked) {
                        this.style.backgroundColor = 'white';
                        this.style.borderColor = '#e1e5e9';
                    }
                });
                
                // Update styling on change
                checkbox.addEventListener('change', function() {
                    if (this.checked) {
                        label.style.backgroundColor = '#e6f3ff';
                        label.style.borderColor = '#0079bf';
                        label.style.fontWeight = '600';
                    } else {
                        label.style.backgroundColor = 'white';
                        label.style.borderColor = '#e1e5e9';
                        label.style.fontWeight = 'normal';
                    }
                });
                
                // Initialize styling for checked items
                if (checkbox.checked) {
                    label.style.backgroundColor = '#e6f3ff';
                    label.style.borderColor = '#0079bf';
                    label.style.fontWeight = '600';
                }
            }
        });
    });
    
    console.log('✅ ProjectPage advisor enhancement complete');
});

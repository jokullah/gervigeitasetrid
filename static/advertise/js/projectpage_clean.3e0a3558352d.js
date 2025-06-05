/* 
Save as: advertise/static/advertise/js/projectpage_clean.js
CLEAN VERSION - Only for ProjectPage editing
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
        
        // Add help text
        const helpDiv = document.createElement('div');
        helpDiv.className = 'projectpage-advisor-help';
        
        if (fieldType === 'requested_advisors') {
            helpDiv.innerHTML = '💡 <strong>Óskir frá fyrirtæki:</strong> Þessir starfsmenn voru óskir fyrirtækisins um leiðbeinendur. Listinn er stafrófsraðaður og skrunanlegt.';
        } else if (fieldType === 'leidbeinendur') {
            helpDiv.innerHTML = '💡 <strong>Úthlutaðir leiðbeinendur:</strong> Veljið starfsmenn sem munu vera leiðbeinendur verkefnisins. Listinn er stafrófsraðaður og skrunanlegt.';
        } else {
            helpDiv.innerHTML = '💡 <strong>Ábending:</strong> Listinn er stafrófsraðaður og skrunanlegt. Smelltu til að velja/afvelja.';
        }
        
        // Insert help text before the field
        field.parentElement.insertBefore(helpDiv, field);
        
        // Add helper controls
        const controlsDiv = document.createElement('div');
        controlsDiv.className = 'projectpage-advisor-controls';
        
        const selectAllBtn = document.createElement('button');
        selectAllBtn.type = 'button';
        selectAllBtn.className = 'projectpage-advisor-btn select-all';
        selectAllBtn.textContent = 'Velja alla';
        
        const clearAllBtn = document.createElement('button');
        clearAllBtn.type = 'button';
        clearAllBtn.className = 'projectpage-advisor-btn clear-all';
        clearAllBtn.textContent = 'Hreinsa allt';
        
        const counterDiv = document.createElement('div');
        counterDiv.className = 'projectpage-advisor-counter';
        
        controlsDiv.appendChild(selectAllBtn);
        controlsDiv.appendChild(clearAllBtn);
        controlsDiv.appendChild(counterDiv);
        
        // Insert controls before the field
        field.parentElement.insertBefore(controlsDiv, field);
        
        // Get all checkboxes in this field
        const checkboxes = field.querySelectorAll('input[type="checkbox"]');
        console.log('📋 Found', checkboxes.length, 'checkboxes in', fieldType);
        
        // Update counter
        function updateCounter() {
            const checkedCount = field.querySelectorAll('input[type="checkbox"]:checked').length;
            counterDiv.textContent = `${checkedCount} af ${checkboxes.length} valdir`;
        }
        
        // Button functionality
        selectAllBtn.addEventListener('click', function() {
            checkboxes.forEach(cb => {
                cb.checked = true;
                cb.dispatchEvent(new Event('change', { bubbles: true }));
            });
            updateCounter();
        });
        
        clearAllBtn.addEventListener('click', function() {
            checkboxes.forEach(cb => {
                cb.checked = false;
                cb.dispatchEvent(new Event('change', { bubbles: true }));
            });
            updateCounter();
        });
        
        // Listen for changes to update counter
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', updateCounter);
        });
        
        // Initialize counter
        updateCounter();
        
        // Enhanced checkbox styling (clean version)
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

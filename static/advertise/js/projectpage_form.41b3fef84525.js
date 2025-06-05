/* 
Save as: advertise/static/advertise/js/projectpage_form.js
*/

document.addEventListener('DOMContentLoaded', function() {
    console.log('🔥🔥🔥 ProjectPage form JS loaded!');
    alert('🔥 PROJECTPAGE FORM JS IS WORKING! 🔥');
    
    // Add debug message with delay to ensure it shows above the CSS banner
    setTimeout(function() {
        const debugDiv = document.createElement('div');
        debugDiv.innerHTML = '🔥 PROJECTPAGE FORM JS IS ACTIVE! 🔥';
        debugDiv.style.cssText = `
            position: fixed;
            top: 50px;
            left: 0;
            right: 0;
            background: #0000ff;
            color: white;
            padding: 20px;
            z-index: 10001;
            font-size: 24px;
            font-weight: bold;
            text-align: center;
        `;
        document.body.appendChild(debugDiv);
        
        // Hide after 5 seconds
        setTimeout(() => {
            debugDiv.style.display = 'none';
        }, 5000);
    }, 100);
    
    // Look for advisor checkbox fields
    const advisorFields = document.querySelectorAll('.advisor-checkboxes');
    console.log('🔍 Found', advisorFields.length, 'advisor checkbox fields');
    
    if (advisorFields.length > 0) {
        console.log('🎯 Setting up advisor fields...');
        
        advisorFields.forEach((field, index) => {
            console.log('✅ Processing advisor field', index);
            
            // Make field extra visible
            field.style.border = '10px solid blue';
            field.style.background = 'pink';
            
            // Add helper text
            const helpDiv = document.createElement('div');
            helpDiv.innerHTML = '💡 <strong>Tip:</strong> This list is alphabetical and scrollable. Click to select/deselect advisors.';
            helpDiv.style.cssText = `
                background: #e8f4fd;
                border-left: 4px solid #0079bf;
                padding: 8px 12px;
                margin: 8px 0;
                border-radius: 4px;
                font-size: 12px;
            `;
            
            field.parentElement.insertBefore(helpDiv, field);
            
            // Style individual checkboxes
            const checkboxes = field.querySelectorAll('input[type="checkbox"]');
            console.log('Found', checkboxes.length, 'checkboxes in field', index);
            
            checkboxes.forEach(checkbox => {
                const label = checkbox.closest('label');
                if (label) {
                    label.style.cssText = `
                        display: block !important;
                        background: lime !important;
                        border: 3px solid red !important;
                        padding: 10px !important;
                        margin: 5px 0 !important;
                        font-size: 18px !important;
                        font-weight: bold !important;
                        cursor: pointer !important;
                    `;
                    
                    // Add hover effect
                    label.addEventListener('mouseenter', function() {
                        this.style.background = 'orange';
                    });
                    
                    label.addEventListener('mouseleave', function() {
                        if (!checkbox.checked) {
                            this.style.background = 'lime';
                        }
                    });
                    
                    // Style checked state
                    checkbox.addEventListener('change', function() {
                        if (this.checked) {
                            label.style.background = 'cyan';
                            label.style.fontWeight = '900';
                        } else {
                            label.style.background = 'lime';
                            label.style.fontWeight = 'bold';
                        }
                    });
                    
                    // Initialize checked state
                    if (checkbox.checked) {
                        label.style.background = 'cyan';
                        label.style.fontWeight = '900';
                    }
                }
            });
        });
    } else {
        console.log('❌ No advisor checkbox fields found');
        
        // Debug: show all available elements
        const allCheckboxes = document.querySelectorAll('input[type="checkbox"]');
        console.log('🔍 All checkboxes on page:', allCheckboxes.length);
        
        const allFields = document.querySelectorAll('.field');
        console.log('🔍 All fields on page:', allFields.length);
        
        // Try to find advisor fields by different selectors
        const requestedField = document.querySelector('.field-requested_advisors');
        const leidbeinendurField = document.querySelector('.field-leidbeinendur');
        
        console.log('🔍 requested_advisors field:', requestedField);
        console.log('🔍 leidbeinendur field:', leidbeinendurField);
        
        if (requestedField || leidbeinendurField) {
            alert('Found advisor fields but not with .advisor-checkboxes class!');
        }
    }
});

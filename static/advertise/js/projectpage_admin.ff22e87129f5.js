/* 
Save as: advertise/static/advertise/js/projectpage_admin.js
*/

document.addEventListener('DOMContentLoaded', function() {
    console.log('🔥🔥🔥 ProjectPage custom form loaded!');
    alert('🔥 PROJECTPAGE CUSTOM FORM IS WORKING! 🔥');
    
    // Add a huge debug message to the page
    const debugMessage = document.createElement('div');
    debugMessage.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: #ff0000;
        color: white;
        padding: 20px;
        z-index: 9999;
        font-size: 24px;
        font-weight: bold;
        text-align: center;
    `;
    debugMessage.innerHTML = '🔥 PROJECTPAGE CUSTOM FORM IS ACTIVE! 🔥';
    document.body.appendChild(debugMessage);
    
    // Hide the debug message after 5 seconds
    setTimeout(() => {
        debugMessage.style.display = 'none';
    }, 5000);
    
    console.log('🎯 Setting up ProjectPage advisor fields...');
    
    // Function to setup advisor fields
    function setupAdvisorField(fieldSelector, helpTextContent) {
        const field = document.querySelector(fieldSelector);
        if (field) {
            console.log('✅ Found field:', fieldSelector);
            
            // Make the field stand out
            field.style.border = '10px solid red';
            field.style.background = 'yellow';
            field.style.padding = '20px';
            
            // Add help text
            if (!field.querySelector('.advisor-help-text')) {
                const helpText = document.createElement('div');
                helpText.className = 'help advisor-help-text';
                helpText.innerHTML = helpTextContent;
                
                const fieldContent = field.querySelector('.field-content') || field;
                if (fieldContent && fieldContent.firstChild) {
                    fieldContent.insertBefore(helpText, fieldContent.firstChild);
                    console.log('✅ Added help text to', fieldSelector);
                }
            }
            
            // Find checkboxes and style them
            const checkboxes = field.querySelectorAll('input[type="checkbox"]');
            console.log('Found', checkboxes.length, 'checkboxes in', fieldSelector);
            
            if (checkboxes.length > 0) {
                // Find common parent container
                let container = checkboxes[0].parentElement;
                while (container && container !== field) {
                    const containedCheckboxes = container.querySelectorAll('input[type="checkbox"]');
                    if (containedCheckboxes.length === checkboxes.length) {
                        console.log('✅ Found container for', fieldSelector);
                        
                        // Apply LOUD styling
                        container.style.cssText = `
                            max-height: 250px !important;
                            overflow-y: auto !important;
                            overflow-x: hidden !important;
                            border: 10px solid red !important;
                            border-radius: 6px !important;
                            padding: 15px !important;
                            background: yellow !important;
                            display: block !important;
                        `;
                        break;
                    }
                    container = container.parentElement;
                }
                
                // Style individual labels
                checkboxes.forEach(checkbox => {
                    const label = checkbox.closest('label');
                    if (label) {
                        label.style.cssText = `
                            display: block !important;
                            background: lime !important;
                            border: 2px solid red !important;
                            padding: 8px !important;
                            margin: 4px 0 !important;
                            font-size: 16px !important;
                            font-weight: bold !important;
                        `;
                    }
                });
            }
        } else {
            console.log('❌ Field not found:', fieldSelector);
        }
    }
    
    // Setup both advisor fields
    setupAdvisorField('.field-requested_advisors', 
        '💡 <strong>Óskir frá fyrirtæki:</strong> Þessir starfsmenn voru óskir fyrirtækisins um leiðbeinendur.');
    
    setupAdvisorField('.field-leidbeinendur', 
        '💡 <strong>Úthlutaðir leiðbeinendur:</strong> Veljið starfsmenn sem munu vera leiðbeinendur verkefnisins.');
});

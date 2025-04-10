// Main JavaScript functionality for the PriyaQubit Web Scraper

document.addEventListener('DOMContentLoaded', function() {
    // Initialize UI
    initializeUI();
    
    // Handle selector type change to update help text and options
    const selectorTypeSelect = document.getElementById('selector_type');
    const selectorValueSelect = document.getElementById('selector_value');
    const selectorHelp = document.getElementById('selector_help');
    
    if (selectorTypeSelect && selectorHelp) {
        updateSelectorHelp(selectorTypeSelect.value);
        
        selectorTypeSelect.addEventListener('change', function() {
            updateSelectorHelp(this.value);
            
            // Update selector values based on selected type if options are available
            if (window.selectorOptions) {
                populateSelectorOptions(this.value, window.selectorOptions);
            }
        });
    }

    // URL validation and fetch selector options
    const urlInput = document.getElementById('url');
    if (urlInput) {
        urlInput.addEventListener('change', function() {
            const isValid = validateUrl(this);
            
            if (isValid && this.value) {
                fetchSelectorOptions(this.value);
            }
        });
    }

    // Analyze URL button
    const analyzeButton = document.getElementById('analyze_url');
    if (analyzeButton) {
        analyzeButton.addEventListener('click', function() {
            const urlInput = document.getElementById('url');
            if (urlInput && validateUrl(urlInput)) {
                showLoadingIndicator(true, 'Analyzing webpage structure...');
                fetchSelectorOptions(urlInput.value);
            } else {
                showAlert('Please enter a valid URL first', 'warning');
            }
        });
    }

    // Preview selector button functionality
    const previewButton = document.getElementById('preview_selector');
    if (previewButton) {
        previewButton.addEventListener('click', function(e) {
            e.preventDefault();
            previewSelector();
        });
    }

    // Handle copy to clipboard buttons
    const copyButtons = document.querySelectorAll('.copy-content');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const contentId = this.getAttribute('data-content');
            const content = document.getElementById(contentId).textContent;
            copyToClipboard(content, this);
        });
    });

    // Search functionality
    const searchForm = document.getElementById('search_form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const searchInput = document.getElementById('search_term');
            if (!searchInput.value.trim()) {
                e.preventDefault();
                showAlert('Please enter a search term', 'warning');
            }
        });
    }

    // Handle delete confirmation
    const deleteButtons = document.querySelectorAll('.delete-session');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this session? This cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
    
    // View toggles for visualization page
    const viewToggleButtons = document.querySelectorAll('.view-toggle-btn');
    viewToggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const viewType = this.getAttribute('data-view');
            toggleView(viewType);
        });
    });
    
    // Try to load preferred view from localStorage
    if (document.getElementById('table_view') && document.getElementById('card_view')) {
        loadPreferredView();
    }
    
    // Form submission
    const scrapeForm = document.getElementById('scrape_form');
    if (scrapeForm) {
        scrapeForm.addEventListener('submit', function(e) {
            const url = document.getElementById('url').value;
            const selectorType = document.getElementById('selector_type').value;
            const selectorValue = document.getElementById('selector_value').value;
            
            if (!url || !validateUrl(document.getElementById('url'))) {
                e.preventDefault();
                showAlert('Please enter a valid URL', 'danger');
                return;
            }
            
            if (!selectorValue) {
                e.preventDefault();
                showAlert('Please select a selector value for extraction', 'warning');
                return;
            }
            
            // Show loading overlay with message
            showLoadingIndicator(true, 'Processing website data...');
        });
    }
});

// Initialize UI components
function initializeUI() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Set up page loader
    document.querySelector('.page-loader')?.classList.add('d-none');
    
    // Set up animated entrances for cards
    const animatedElements = document.querySelectorAll('.feature-card, .timeline-step');
    animatedElements.forEach((element, index) => {
        setTimeout(() => {
            element.classList.add('show');
        }, 100 * index);
    });
}

// Update the help text based on the selected selector type
function updateSelectorHelp(selectorType) {
    const selectorHelp = document.getElementById('selector_help');
    
    switch(selectorType) {
        case 'tag':
            selectorHelp.innerHTML = 'Select from recommended HTML tags found on the page (e.g., <code>div</code>, <code>a</code>, <code>p</code>).';
            break;
        case 'class':
            selectorHelp.innerHTML = 'Select from important CSS classes identified on the page (e.g., <code>container</code>, <code>nav-item</code>).';
            break;
        case 'id':
            selectorHelp.innerHTML = 'Select from page IDs found during analysis (e.g., <code>header</code>, <code>main-content</code>).';
            break;
        case 'css':
            selectorHelp.innerHTML = 'Select from pre-defined CSS selectors to target specific content patterns.';
            break;
        case 'images':
            selectorHelp.innerHTML = 'Extract all image links from the page. System will categorize by size and relevance.';
            break;
        case 'links':
            selectorHelp.innerHTML = 'Extract all hyperlinks from the page. System will categorize by type (internal, external, etc).';
            break;
        case 'robots':
            selectorHelp.innerHTML = 'Analyze the robots.txt file and crawling permissions for this website.';
            break;
        case 'meta':
            selectorHelp.innerHTML = 'Extract meta information like titles, descriptions, keywords, and Open Graph data.';
            break;
    }
}

// Validate URL format
function validateUrl(input) {
    const urlPattern = /^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$/;
    
    if (!input.value) {
        setInputValidity(input, true);
        return true;
    }
    
    const isValid = urlPattern.test(input.value);
    setInputValidity(input, isValid);
    return isValid;
}

// Set input validity visual feedback
function setInputValidity(input, isValid) {
    if (isValid) {
        input.classList.remove('is-invalid');
        input.classList.add('is-valid');
    } else {
        input.classList.remove('is-valid');
        input.classList.add('is-invalid');
    }
}

// Preview selector function - fetches a sample of elements that match the selector
function previewSelector() {
    const url = document.getElementById('url').value;
    const selectorType = document.getElementById('selector_type').value;
    const selectorValue = document.getElementById('selector_value').value;
    
    if (!validateUrl(document.getElementById('url'))) {
        showAlert('Please enter a valid URL', 'danger');
        return;
    }
    
    if (!selectorValue) {
        showAlert('Please select a selector value first', 'warning');
        return;
    }
    
    // Show loading state
    const previewButton = document.getElementById('preview_selector');
    previewButton.disabled = true;
    previewButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
    
    // Create form data for the request
    const formData = new FormData();
    formData.append('url', url);
    formData.append('selector_type', selectorType);
    formData.append('selector_value', selectorValue);
    
    // Show global loading indicator
    showLoadingIndicator(true, `Extracting data using ${selectorType}: "${selectorValue}"...`);
    
    // Show a message about initiating the scrape
    showAlert(`Initiating data extraction with ${selectorType}: "${selectorValue}"`, 'info');
    
    // Submit the form automatically after preview
    setTimeout(() => {
        document.getElementById('scrape_form').submit();
    }, 1200);
}

// Copy content to clipboard
function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(
        function() {
            // Save original button text
            const originalText = button.innerHTML;
            
            // Show copied confirmation
            button.innerHTML = '<i class="fas fa-check"></i> Copied!';
            
            // Reset after 2 seconds
            setTimeout(function() {
                button.innerHTML = originalText;
            }, 2000);
        }, 
        function(err) {
            console.error('Could not copy text: ', err);
            showAlert('Failed to copy to clipboard', 'danger');
        }
    );
}

// Show alert message
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alert_container');
    if (!alertContainer) return;
    
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type} alert-dismissible fade show`;
    alertElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    alertContainer.appendChild(alertElement);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertElement.classList.remove('show');
        setTimeout(() => {
            alertContainer.removeChild(alertElement);
        }, 150);
    }, 5000);
}

// Toggle view between table and card display
function toggleView(viewType) {
    const tableView = document.getElementById('table_view');
    const cardView = document.getElementById('card_view');
    const tableBtn = document.getElementById('table_view_btn');
    const cardBtn = document.getElementById('card_view_btn');
    
    if (viewType === 'table') {
        tableView.classList.remove('d-none');
        cardView.classList.add('d-none');
        tableBtn.classList.add('active');
        cardBtn.classList.remove('active');
    } else {
        cardView.classList.remove('d-none');
        tableView.classList.add('d-none');
        cardBtn.classList.add('active');
        tableBtn.classList.remove('active');
    }
    
    // Save preference
    localStorage.setItem('preferred_view', viewType);
}

// Load user's preferred view from localStorage
function loadPreferredView() {
    const preferredView = localStorage.getItem('preferred_view') || 'table';
    toggleView(preferredView);
}

// Fetch selector options based on the URL
function fetchSelectorOptions(url) {
    const selectorValueSelect = document.getElementById('selector_value');
    const selectorTypeSelect = document.getElementById('selector_type');
    
    if (!selectorValueSelect || !selectorTypeSelect) return;
    
    // Set loading state
    selectorValueSelect.disabled = true;
    selectorValueSelect.innerHTML = '<option value="">Analyzing page structure...</option>';
    
    // Show loading indicator
    showLoadingIndicator(true, 'Analyzing page structure and identifying important elements...');
    
    // Create form data
    const formData = new FormData();
    formData.append('url', url);
    
    // Send AJAX request to get selector options
    fetch('/api/selector-options', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.options) {
            // Store options globally for later use
            window.selectorOptions = data.options;
            
            // Populate selector based on current selected type
            populateSelectorOptions(selectorTypeSelect.value, data.options);
            
            // Enable the select
            selectorValueSelect.disabled = false;
            
            showAlert('Page analysis complete! Smart selector options loaded.', 'success');
        } else {
            // Error handling
            selectorValueSelect.innerHTML = '<option value="">Select manually or try another URL</option>';
            selectorValueSelect.disabled = false;
            
            showAlert(data.message || 'Failed to analyze page structure', 'warning');
            
            // Hide loading indicator
            showLoadingIndicator(false);
        }
    })
    .catch(error => {
        console.error('Error fetching selector options:', error);
        selectorValueSelect.innerHTML = '<option value="">Error analyzing page</option>';
        selectorValueSelect.disabled = false;
        
        showAlert('Failed to analyze page structure. Please try again.', 'danger');
        
        // Hide loading indicator
        showLoadingIndicator(false);
    });
}

// Show or hide the loading indicator
function showLoadingIndicator(show, message = 'Loading...') {
    const loadingOverlay = document.querySelector('.loading-overlay');
    
    if (!loadingOverlay) return;
    
    if (show) {
        // Set message if provided
        const messageElement = loadingOverlay.querySelector('p');
        if (messageElement) {
            messageElement.textContent = message;
        }
        
        // Show the overlay
        loadingOverlay.classList.remove('d-none');
        document.body.style.overflow = 'hidden'; // Prevent scrolling
    } else {
        // Hide the overlay
        loadingOverlay.classList.add('d-none');
        document.body.style.overflow = ''; // Allow scrolling
    }
}

// Populate selector options dropdown based on selector type
function populateSelectorOptions(selectorType, options) {
    const selectorValueSelect = document.getElementById('selector_value');
    if (!selectorValueSelect) return;
    
    // Clear current options
    selectorValueSelect.innerHTML = '';
    
    // Map selector type to the appropriate options array
    let optionsArray = [];
    let description = '';
    
    switch(selectorType) {
        case 'tag':
            optionsArray = options.tags || [];
            description = 'HTML Tags';
            break;
        case 'class':
            optionsArray = options.classes || [];
            description = 'CSS Classes';
            break;
        case 'id':
            optionsArray = options.ids || [];
            description = 'Element IDs';
            break;
        case 'css':
            optionsArray = options.css || [];
            description = 'CSS Selectors';
            break;
        case 'images':
            optionsArray = options.images || ['All Images', 'Large Images Only', 'Product Images', 'Banner Images'];
            description = 'Image Types';
            break;
        case 'links':
            optionsArray = options.links || ['All Links', 'Internal Links', 'External Links', 'Navigation Links', 'Footer Links'];
            description = 'Link Types';
            break;
        case 'robots':
            // For robots.txt, we don't need options - just set a default
            selectorValueSelect.innerHTML = '';
            selectorValueSelect.appendChild(new Option('Analyze robots.txt rules', 'analyze'));
            showLoadingIndicator(false);
            return;
        case 'meta':
            optionsArray = ['All Meta Tags', 'Title & Description', 'Keywords', 'Open Graph Data', 'Twitter Cards'];
            description = 'Meta Information';
            break;
    }
    
    // Add default empty option
    selectorValueSelect.appendChild(new Option('-- Select from recommended options --', ''));
    
    // Add options group if there are any options
    if (optionsArray.length > 0) {
        const group = document.createElement('optgroup');
        group.label = `Recommended ${description}`;
        
        optionsArray.forEach(option => {
            group.appendChild(new Option(option, option));
        });
        
        selectorValueSelect.appendChild(group);
    } else {
        // No options found for this type
        selectorValueSelect.appendChild(new Option(`No ${description.toLowerCase()} found`, ''));
    }
    
    // Hide loading indicator
    showLoadingIndicator(false);
}

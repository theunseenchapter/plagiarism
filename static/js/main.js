// Enhanced JavaScript for Smart Plagiarism Detector with Rephrasing

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize word counting
    const textInput = document.getElementById('textInput');
    const rephraseInput = document.getElementById('rephraseInput');
    
    if (textInput) {
        textInput.addEventListener('input', updateWordCount);
        updateWordCount(); // Initial count
    }
    
    if (rephraseInput) {
        rephraseInput.addEventListener('input', updateRephraseWordCount);
    }
}

// Word counting functions
function updateWordCount() {
    const textInput = document.getElementById('textInput');
    const wordCountElement = document.getElementById('wordCount');
    
    if (textInput && wordCountElement) {
        const text = textInput.value.trim();
        const wordCount = text ? text.split(/\s+/).length : 0;
        wordCountElement.textContent = `${wordCount} words`;
    }
}

function updateRephraseWordCount() {
    const rephraseInput = document.getElementById('rephraseInput');
    if (rephraseInput) {
        const text = rephraseInput.value.trim();
        const wordCount = text ? text.split(/\s+/).length : 0;
        // You can add a word count display for rephrase input if needed
    }
}

// Clear text function
function clearText() {
    const textInput = document.getElementById('textInput');
    if (textInput) {
        textInput.value = '';
        updateWordCount();
        clearResults();
    }
}

// Paste text function
async function pasteText() {
    try {
        const text = await navigator.clipboard.readText();
        const textInput = document.getElementById('textInput');
        if (textInput) {
            textInput.value = text;
            updateWordCount();
        }
    } catch (err) {
        showError('Unable to access clipboard. Please use Ctrl+V to paste manually.');
    }
}

// Analyze text function
async function analyzeText() {
    const textInput = document.getElementById('textInput');
    const text = textInput.value.trim();
    
    if (!text) {
        showError('Please enter some text to analyze.');
        return;
    }
    
    if (text.length < 50) {
        showError('Please provide at least 50 characters for meaningful analysis.');
        return;
    }
    
    showLoading('Analyzing content with advanced NLP algorithms...');
    
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayResults(data);
        } else {
            showError(data.error || 'An error occurred during analysis.');
        }
    } catch (error) {
        showError('Network error. Please check your connection and try again.');
    } finally {
        hideLoading();
    }
}

// Rephrase text function with timeout protection
async function rephraseText() {
    const rephraseInput = document.getElementById('rephraseInput');
    const style = document.getElementById('rephraseStyle').value;
    const creativity = document.getElementById('creativityLevel').value;
    const text = rephraseInput.value.trim();
    
    if (!text) {
        showError('Please enter some text to rephrase.');
        return;
    }
    
    if (text.length < 10) {
        showError('Please provide at least 10 characters for rephrasing.');
        return;
    }
    
    console.log('Starting rephrase request...'); // Debug log
    showLoading('Generating rephrased content...');
    
    // Safety timeout to force hide modal after 15 seconds
    const timeoutId = setTimeout(() => {
        console.log('Request timeout - forcing modal hide');
        forceHideModal();
        showError('Request timed out. Please try again.');
    }, 15000);
    
    try {
        console.log('Sending request to /rephrase endpoint...'); // Debug log
        const response = await fetch('/rephrase', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                text: text,
                style: style,
                creativity: creativity
            })
        });
        
        console.log('Response received:', response.status); // Debug log
        const data = await response.json();
        console.log('Response data:', data); // Debug log
        
        clearTimeout(timeoutId); // Clear the timeout
        
        if (response.ok) {
            displayRephraseResult(data.rephrased_text, data.original_text, data.changes_made, data.words_changed);
            showSuccess(`Text rephrased successfully! ${data.words_changed} words changed.`);
        } else {
            showError(data.error || 'An error occurred during rephrasing.');
        }
    } catch (error) {
        console.error('Rephrase error:', error); // Debug log
        clearTimeout(timeoutId); // Clear the timeout
        showError('Network error. Please check your connection and try again.');
    } finally {
        console.log('Hiding loading modal...'); // Debug log
        hideLoading();
        // Additional safety call
        setTimeout(forceHideModal, 500);
    }
}

// Display results function
function displayResults(data) {
    const resultsContainer = document.getElementById('results');
    
    const resultHTML = `
        <div class="result-card ${data.risk_color === 'danger' ? 'high-risk' : data.risk_color === 'warning' ? 'medium-risk' : 'low-risk'} fade-in">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h6 class="mb-0"><i class="fas fa-chart-line me-2"></i>Plagiarism Score</h6>
                <span class="badge bg-${data.risk_color} fs-6">${data.plagiarism_level}</span>
            </div>
            
            <div class="mb-3">
                <div class="progress" style="height: 20px;">
                    <div class="progress-bar bg-${data.risk_color}" 
                         role="progressbar" 
                         style="width: ${data.plagiarism_score}%" 
                         aria-valuenow="${data.plagiarism_score}" 
                         aria-valuemin="0" 
                         aria-valuemax="100">
                        ${data.plagiarism_score}%
                    </div>
                </div>
            </div>
            
            <div class="row text-center mb-3">
                <div class="col-6">
                    <strong class="text-primary">${data.text_analysis.total_words}</strong>
                    <br><small class="text-muted">Total Words</small>
                </div>
                <div class="col-6">
                    <strong class="text-success">${data.text_analysis.unique_words}</strong>
                    <br><small class="text-muted">Unique Words</small>
                </div>
            </div>
            
            ${data.issues && data.issues.length > 0 ? `
                <div class="mt-3">
                    <h6><i class="fas fa-exclamation-triangle me-2 text-warning"></i>Issues Detected:</h6>
                    <ul class="list-unstyled">
                        ${data.issues.map(issue => `<li class="mb-1"><i class="fas fa-arrow-right me-2 text-muted"></i>${issue}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            ${data.common_phrases && data.common_phrases.length > 0 ? `
                <div class="mt-3">
                    <h6><i class="fas fa-quote-right me-2 text-info"></i>Common Phrases:</h6>
                    <div class="d-flex flex-wrap gap-1">
                        ${data.common_phrases.slice(0, 5).map(phrase => `<span class="badge bg-light text-dark">${phrase}</span>`).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
    
    resultsContainer.innerHTML = resultHTML;
}

// Display rephrase result with highlighting
function displayRephraseResult(rephrasedText, originalText, changesMade, wordsChanged) {
    const rephraseResult = document.getElementById('rephraseResult');
    const rephraseActions = document.getElementById('rephraseActions');
    
    // Create highlighted version showing changes
    const highlightedText = highlightChangesAdvanced(originalText, rephrasedText, changesMade);
    
    rephraseResult.innerHTML = `
        <div class="rephrased-content p-3" style="background: white; border-radius: 8px; border: 2px solid #20c997;">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h6 class="mb-0 text-success"><i class="fas fa-magic me-2"></i>Rephrased Text</h6>
                <div>
                    <span class="badge bg-info me-2">${wordsChanged} words changed</span>
                    <button class="btn btn-sm btn-outline-secondary" onclick="toggleHighlighting()" id="highlightToggle">
                        <i class="fas fa-highlighter me-1"></i>Show Changes
                    </button>
                </div>
            </div>
            <div id="rephrasedContent">${rephrasedText}</div>
            <div id="highlightedContent" style="display: none;">${highlightedText}</div>
            <div class="mt-3 text-muted small">
                <i class="fas fa-info-circle me-1"></i>
                <span class="text-success">Green highlights</span> show rephrased parts that help reduce plagiarism.
            </div>
        </div>
    `;
    
    rephraseResult.className = 'rephrase-result has-content';
    rephraseActions.classList.remove('d-none');
    
    // Store the rephrased text for later use
    window.currentRephrasedText = rephrasedText;
    window.currentChanges = changesMade;
}

// Advanced function to highlight changes using backend data
function highlightChangesAdvanced(originalText, rephrasedText, changesMade) {
    if (!changesMade || changesMade.length === 0) {
        return rephrasedText;
    }
    
    // Create a map of original words to their replacements
    const changeMap = {};
    changesMade.forEach(change => {
        if (change.original !== 'sentence_start') {
            changeMap[change.original.toLowerCase()] = change.replacement;
        }
    });
    
    // Split rephrased text into words and highlight changed ones
    const words = rephrasedText.split(/(\s+)/); // Keep spaces
    const highlightedWords = words.map(word => {
        const cleanWord = word.toLowerCase().replace(/[.,!?;:]$/, '');
        
        // Check if this word is a replacement
        if (Object.values(changeMap).some(replacement => 
            replacement.toLowerCase() === cleanWord
        )) {
            // Find the original word that was replaced
            const originalWord = Object.keys(changeMap).find(orig => 
                changeMap[orig].toLowerCase() === cleanWord
            );
            
            return `<span class="highlight-change" 
                          style="background-color: #d4edda; padding: 2px 4px; border-radius: 3px; border: 1px solid #c3e6cb; position: relative;" 
                          title="Changed from: ${originalWord}"
                          data-bs-toggle="tooltip">${word}</span>`;
        }
        
        return word;
    });
    
    return highlightedWords.join('');
}

// Function to highlight changes between original and rephrased text
function highlightChanges(originalText, rephrasedText) {
    // Split into words for comparison
    const originalWords = originalText.toLowerCase().split(/\s+/);
    const rephrasedWords = rephrasedText.split(/\s+/);
    
    const highlightedWords = [];
    
    for (let i = 0; i < rephrasedWords.length; i++) {
        const word = rephrasedWords[i];
        const wordLower = word.toLowerCase().replace(/[.,!?;:]$/, ''); // Remove punctuation for comparison
        
        // Check if this word exists in the original text
        const isOriginal = originalWords.some(originalWord => 
            originalWord.replace(/[.,!?;:]$/, '') === wordLower
        );
        
        if (isOriginal) {
            highlightedWords.push(word);
        } else {
            // This is a rephrased/new word - highlight it
            highlightedWords.push(`<span class="highlight-change" style="background-color: #d4edda; padding: 2px 4px; border-radius: 3px; border: 1px solid #c3e6cb;">${word}</span>`);
        }
    }
    
    return highlightedWords.join(' ');
}

// Toggle between normal and highlighted view
function toggleHighlighting() {
    const rephrasedContent = document.getElementById('rephrasedContent');
    const highlightedContent = document.getElementById('highlightedContent');
    const toggleButton = document.getElementById('highlightToggle');
    
    if (rephrasedContent.style.display === 'none') {
        // Show normal version
        rephrasedContent.style.display = 'block';
        highlightedContent.style.display = 'none';
        toggleButton.innerHTML = '<i class="fas fa-highlighter me-1"></i>Show Changes';
    } else {
        // Show highlighted version
        rephrasedContent.style.display = 'none';
        highlightedContent.style.display = 'block';
        toggleButton.innerHTML = '<i class="fas fa-eye me-1"></i>Hide Changes';
        
        // Initialize tooltips for the highlighted words
        setTimeout(() => {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }, 100);
    }
}

// Copy rephrased text
function copyRephrased() {
    if (window.currentRephrasedText) {
        navigator.clipboard.writeText(window.currentRephrasedText).then(() => {
            showSuccess('Rephrased text copied to clipboard!');
        }).catch(() => {
            showError('Failed to copy text to clipboard.');
        });
    }
}

// Check rephrased text for plagiarism
function checkRephrased() {
    if (window.currentRephrasedText) {
        // Switch to detection tab
        const detectTab = document.getElementById('detect-tab');
        const textInput = document.getElementById('textInput');
        
        detectTab.click();
        textInput.value = window.currentRephrasedText;
        updateWordCount();
        
        // Auto-analyze after a short delay
        setTimeout(() => {
            analyzeText();
        }, 500);
    }
}

// Regenerate rephrase
function regenerateRephrase() {
    rephraseText();
}

// Loading functions with enhanced fallback
function showLoading(message = 'Processing...') {
    const loadingModalElement = document.getElementById('loadingModal');
    const loadingText = document.getElementById('loadingText');
    
    if (loadingText) {
        loadingText.textContent = message;
    }
    
    try {
        // Get existing instance or create new one
        let loadingModal = bootstrap.Modal.getInstance(loadingModalElement);
        if (!loadingModal) {
            loadingModal = new bootstrap.Modal(loadingModalElement);
        }
        loadingModal.show();
    } catch (error) {
        console.error('Error showing modal:', error);
        // Fallback: show modal manually
        loadingModalElement.classList.add('show');
        loadingModalElement.style.display = 'block';
        document.body.classList.add('modal-open');
    }
}

function hideLoading() {
    const loadingModalElement = document.getElementById('loadingModal');
    
    try {
        const loadingModal = bootstrap.Modal.getInstance(loadingModalElement);
        if (loadingModal) {
            loadingModal.hide();
        } else {
            throw new Error('No modal instance found');
        }
    } catch (error) {
        console.error('Error hiding modal:', error);
        // Force hide the modal with multiple methods
        forceHideModal();
    }
    
    // Additional safety timeout
    setTimeout(forceHideModal, 1000);
}

function forceHideModal() {
    const loadingModalElement = document.getElementById('loadingModal');
    
    // Remove all modal-related classes and styles
    loadingModalElement.classList.remove('show');
    loadingModalElement.style.display = 'none';
    loadingModalElement.setAttribute('aria-hidden', 'true');
    loadingModalElement.removeAttribute('aria-modal');
    
    // Remove modal-open class from body
    document.body.classList.remove('modal-open');
    
    // Remove backdrop if it exists
    const backdrops = document.querySelectorAll('.modal-backdrop');
    backdrops.forEach(backdrop => backdrop.remove());
    
    // Reset body padding and overflow
    document.body.style.paddingRight = '';
    document.body.style.overflow = '';
    
    console.log('Modal force hidden');
}

// Error handling
function showError(message) {
    // Create toast notification
    const toastContainer = getOrCreateToastContainer();
    const toast = createToast('error', 'Error', message);
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function showSuccess(message) {
    // Create toast notification
    const toastContainer = getOrCreateToastContainer();
    const toast = createToast('success', 'Success', message);
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function getOrCreateToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    return container;
}

function createToast(type, title, message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    const iconClass = type === 'error' ? 'fas fa-exclamation-circle text-danger' : 'fas fa-check-circle text-success';
    
    toast.innerHTML = `
        <div class="toast-header">
            <i class="${iconClass} me-2"></i>
            <strong class="me-auto">${title}</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    return toast;
}

function clearResults() {
    const resultsContainer = document.getElementById('results');
    if (resultsContainer) {
        resultsContainer.innerHTML = `
            <div class="text-center text-muted py-5">
                <i class="fas fa-clipboard-list fa-3x mb-3 opacity-50"></i>
                <p>Enter text and click "Analyze" to see detailed plagiarism detection results</p>
            </div>
        `;
    }
}

// These functions are called directly from the HTML's onclick, so they remain global.
function openTab(evt, tabName) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active', 'text-blue-600', 'border-blue-600');
        btn.classList.add('text-gray-500', 'border-transparent');
    });
    document.getElementById(tabName).classList.remove('hidden');
    evt.currentTarget.classList.add('active', 'text-blue-600', 'border-blue-600');
    evt.currentTarget.classList.remove('text-gray-500', 'border-transparent');
}

function showStatus(elementId, message, type = 'info') {
    const statusElement = document.getElementById(elementId);
    statusElement.innerHTML = `
        <div class="status-enter flex items-center justify-center space-x-3 p-4 rounded-xl border-2 ${
            type === 'success' ? 'bg-green-50 border-green-200 text-green-800' :
            type === 'error' ? 'bg-red-50 border-red-200 text-red-800' :
            'bg-blue-50 border-blue-200 text-blue-800'
        }">
            ${type === 'success' ? 
                '<svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>' :
                type === 'error' ?
                '<svg class="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>' :
                '<svg class="w-5 h-5 text-blue-600 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>'
            }
            <span class="font-medium">${message}</span>
        </div>
    `;
    statusElement.classList.remove('hidden');
}

/**
 * Shows a temporary message next to the bundler's "Generate" button.
 * @param {HTMLElement} buttonElement The button element to anchor the message to.
 * @param {string} message The text to display.
 * @param {'success' | 'error'} type The type of message.
 */
function showBundlerTopMessage(buttonElement, message, type) {
    const existingMessage = buttonElement.parentNode.querySelector('.bundler-top-message');
    if (existingMessage) existingMessage.remove();

    const messageDiv = document.createElement('div');
    messageDiv.className = `bundler-top-message status-enter flex items-center space-x-2 text-sm font-medium mr-4 ${
        type === 'success' ? 'text-green-700' : 'text-red-700'
    }`;
    
    const icon = type === 'success'
        ? '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>'
        : '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>';
    
    messageDiv.innerHTML = `${icon}<span>${message}</span>`;
    
    buttonElement.parentNode.insertBefore(messageDiv, buttonElement);

    setTimeout(() => {
        messageDiv.remove();
    }, 3000);
}


document.addEventListener('DOMContentLoaded', () => {
    
    document.getElementById('split-bundle').classList.remove('hidden');
    loadBundlerPaths();

    setupFileUploadUI('split-file-upload');
    setupFileUploadUI('build-file-upload');

    document.getElementById('split-form').addEventListener('submit', async (event) => {
        event.preventDefault();
        const submitBtn = event.currentTarget.querySelector('button[type="submit"]');
        const fileInput = document.getElementById('split-file-upload');
        if (fileInput.files.length === 0) {
            showStatus('status-splitter', 'Please select a file to split.', 'error');
            return;
        }
        showStatus('status-splitter', 'Splitting and updating project...', 'info');
        submitBtn.disabled = true;
        try {
            const fileContent = await fileInput.files[0].text();
            const response = await fetch('/api/split', { method: 'POST', body: fileContent });
            const result = await response.json();
            if (!result.success) throw new Error(result.message);
            
            showStatus('status-splitter', 'Project updated! Refreshing to load new APIs...', 'success');
            
            const bundlerPathContainer = document.getElementById('path-list-container');
            bundlerPathContainer.innerHTML = `
                <li class="flex items-center justify-center py-8 text-gray-500">
                    <div class="flex items-center space-x-2">
                        <svg class="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <span>Loading new endpoints...</span>
                    </div>
                </li>
            `;

            setTimeout(() => { location.reload(); }, 2500); 

        } catch (error) {
            showStatus('status-splitter', `Error: ${error.message}`, 'error');
            submitBtn.disabled = false; 
        } 
    });

    const bundleForm = document.getElementById('bundle-form');
    const filenameInput = document.getElementById('filename');

    // Clear custom validation message as the user types
    filenameInput.addEventListener('input', () => {
        filenameInput.setCustomValidity('');
    });

    bundleForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        
        // --- Custom Filename Validation ---
        if (!filenameInput.value) {
            filenameInput.setCustomValidity('Please enter an output filename.');
        } else if (!/\.(yaml|yml)$/.test(filenameInput.value)) {
            filenameInput.setCustomValidity('Filename must end with .yaml or .yml');
        } else {
            filenameInput.setCustomValidity('');
        }

        // reportValidity() will show the custom message if set, or return true if valid.
        if (!bundleForm.reportValidity()) {
            return;
        }

        const submitBtn = event.currentTarget.querySelector('button[type="submit"]');
        const statusDiv = document.getElementById('status-bundler');

        statusDiv.classList.add('hidden');
        const existingMessage = submitBtn.parentNode.querySelector('.bundler-top-message');
        if (existingMessage) existingMessage.remove();

        const selectedPaths = Array.from(document.querySelectorAll('#bundler-section input[name="paths"]:checked')).map(cb => cb.value);
        if (selectedPaths.length === 0) {
            showBundlerTopMessage(submitBtn, 'Please select at least one endpoint.', 'error');
            return;
        }

        showStatus('status-bundler', 'Bundling your selected endpoints...', 'info');
        submitBtn.disabled = true;
        const filename = filenameInput.value;

        try {
            const response = await fetch('/api/bundle', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ paths: selectedPaths, filename: filename })
            });
            if (!response.ok) {
                const errorResult = await response.json();
                throw new Error(errorResult.message || 'Unknown error');
            }
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none'; a.href = url; a.download = filename;
            document.body.appendChild(a); a.click();
            window.URL.revokeObjectURL(url); document.body.removeChild(a);
            
            showBundlerTopMessage(submitBtn, 'Bundle generated successfully!', 'success');
            statusDiv.classList.add('hidden');

        } catch (error) {
            showBundlerTopMessage(submitBtn, `Error: ${error.message}`, 'error');
            statusDiv.classList.add('hidden');
        } finally {
            submitBtn.disabled = false;
        }
    });

    document.getElementById('build-form').addEventListener('submit', async (event) => {
        event.preventDefault();
        const submitBtn = event.currentTarget.querySelector('button[type="submit"]');
        const fileInput = document.getElementById('build-file-upload');
        const filename = document.getElementById('build-filename').value;

        if (fileInput.files.length === 0) {
            showStatus('status-builder', 'Please select a bundled file to build.', 'error');
            return;
        }

        showStatus('status-builder', 'Building documentation...', 'info');
        submitBtn.disabled = true;
        
        try {
            const fileContent = await fileInput.files[0].text();
            const specContent = jsyaml.load(fileContent);

            const response = await fetch('/api/build', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ spec_content: specContent, filename: filename })
            });

            if (!response.ok) {
                const errorResult = await response.json();
                throw new Error(errorResult.message || 'Unknown build error');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none'; a.href = url; a.download = filename;
            document.body.appendChild(a); a.click();
            window.URL.revokeObjectURL(url); document.body.removeChild(a);
            showStatus('status-builder', `Successfully built ${filename}! Download started.`, 'success');

        } catch (error) {
            showStatus('status-builder', `Error: ${error.message}`, 'error');
        } finally {
            submitBtn.disabled = false;
        }
    });

    document.getElementById('search-input').addEventListener('keyup', (event) => {
        const filter = event.target.value.toLowerCase();
        document.querySelectorAll('#path-list-container .tag-group').forEach(group => {
            let groupVisible = false;
            group.querySelectorAll('.endpoint-item').forEach(endpointDiv => {
                const text = endpointDiv.textContent.toLowerCase();
                if (text.includes(filter)) {
                    endpointDiv.style.display = '';
                    groupVisible = true;
                } else {
                    endpointDiv.style.display = 'none';
                }
            });
            group.style.display = groupVisible ? '' : 'none';
        });
    });
});

function setupFileUploadUI(inputId) {
    const fileInput = document.getElementById(inputId);
    if (!fileInput) return;

    const dropZone = fileInput.closest('.file-drop-zone');
    const fileNameElement = dropZone.querySelector('.file-drop-filename');
    const defaultTextElement = dropZone.querySelector('.file-drop-text');

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            fileNameElement.textContent = `Selected file: ${fileInput.files[0].name}`;
            defaultTextElement.style.display = 'none';
        } else {
            fileNameElement.textContent = '';
            defaultTextElement.style.display = 'block';
        }
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            fileInput.dispatchEvent(new Event('change'));
        }
    });
}

async function loadBundlerPaths() {
     try {
        const response = await fetch('/api/paths');
        if (!response.ok) throw new Error((await response.json()).error || 'Network response was not ok');
        const data = await response.json();
        const container = document.getElementById('path-list-container');
        container.innerHTML = '';
        
        if (Object.keys(data.groups).length === 0) {
             container.innerHTML = `<li class="text-center text-gray-500 py-8">No endpoints found. Use the Splitter to create a project.</li>`;
             return;
        }

        for (const groupName in data.groups) {
            const groupDiv = document.createElement('div');
            groupDiv.className = 'tag-group space-y-3 mb-6';
            
            const header = document.createElement('div');
            header.className = 'sticky top-0 bg-gray-100 px-3 py-2 rounded-lg border-l-4 border-blue-500';
            header.innerHTML = `<h4 class="font-semibold text-gray-800 text-sm uppercase tracking-wide">${groupName}</h4>`;
            
            const endpointsList = document.createElement('div');
            endpointsList.className = 'space-y-2 pl-4';
            
            data.groups[groupName].forEach(endpoint => {
                const endpointDiv = document.createElement('div');
                endpointDiv.className = 'endpoint-item group hover:bg-blue-50 rounded-lg p-3 transition-colors duration-200';
                endpointDiv.innerHTML = `
                    <label class="flex items-start space-x-3 cursor-pointer">
                        <input type="checkbox" name="paths" value="${endpoint.path}" class="mt-1 w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2">
                        <div class="flex-1 min-w-0">
                            <div class="font-mono text-sm text-gray-900 group-hover:text-blue-900 transition-colors">${endpoint.path}</div>
                            <div class="text-xs text-gray-500 mt-1 line-clamp-2">${endpoint.summary}</div>
                        </div>
                    </label>
                `;
                endpointsList.appendChild(endpointDiv);
            });
            
            groupDiv.appendChild(header);
            groupDiv.appendChild(endpointsList);
            container.appendChild(groupDiv);
        }
    } catch (error) {
         const container = document.getElementById('path-list-container');
         container.innerHTML = `<div class="text-center py-8 text-red-600 font-medium">Failed to load paths: ${error.message}</div>`;
    }
}


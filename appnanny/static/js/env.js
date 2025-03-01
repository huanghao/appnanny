function addEnvRow() {
    const envRows = document.getElementById('envRows');
    const newRow = document.createElement('div');
    newRow.className = 'form-row mb-2 env-row';
    newRow.innerHTML = `
        <div class="col">
            <input type="text" class="form-control env-key" placeholder="Key">
        </div>
        <div class="col">
            <input type="text" class="form-control env-value" placeholder="Value">
        </div>
        <div class="col-auto">
            <button type="button" class="btn btn-danger btn-sm" onclick="removeEnvRow(this)">Remove</button>
        </div>
    `;
    envRows.appendChild(newRow);
}

function removeEnvRow(button) {
    button.closest('.env-row').remove();
}

document.getElementById('envForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const rows = document.querySelectorAll('.env-row');
    const env = {};
    
    rows.forEach(row => {
        const key = row.querySelector('.env-key').value.trim();
        const value = row.querySelector('.env-value').value.trim();
        if (key) {
            env[key] = value;
        }
    });

    // Get app name from URL
    const appName = window.location.pathname.split('/').pop();
    
    fetch(`/env/${appName}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(env)
    })
    .then(response => response.json())
    .then(result => {
        showNotification(result.message, 'success');
    })
    .catch(error => {
        showNotification('Error updating environment variables', 'error');
        console.error('Error:', error);
    });
});

function parseEnvText(text) {
    const env = {};
    const lines = text.split('\n');
    
    for (const line of lines) {
        const trimmed = line.trim();
        // Skip empty lines and full-line comments
        if (!trimmed || trimmed.startsWith('#')) continue;
        
        // Remove 'export' if present and trim again
        const envLine = trimmed.startsWith('export ') ? trimmed.slice(7).trim() : trimmed;
        
        // Find first unescaped = and first unescaped #
        const eqIndex = envLine.search(/(?<!\\)=/);
        if (eqIndex === -1) continue;

        const key = envLine.slice(0, eqIndex).trim();
        let valueWithComment = envLine.slice(eqIndex + 1);
        
        // Parse value considering quotes and comments
        let value = '';
        let inQuote = null;  // null, '"', or "'"
        let isEscaped = false;
        
        for (let i = 0; i < valueWithComment.length; i++) {
            const char = valueWithComment[i];
            
            if (isEscaped) {
                value += char;
                isEscaped = false;
                continue;
            }
            
            if (char === '\\') {
                isEscaped = true;
                continue;
            }
            
            if (inQuote) {
                if (char === inQuote) {
                    inQuote = null;
                } else {
                    value += char;
                }
                continue;
            }
            
            if (char === '"' || char === "'") {
                inQuote = char;
                continue;
            }
            
            if (char === '#') {
                break;  // Stop at unquoted, unescaped #
            }
            
            value += char;
        }
        
        value = value.trim();
        if (key) {
            env[key] = value;
        }
    }
    return env;
}

function updateEnvRows(env) {
    const envRows = document.getElementById('envRows');
    envRows.innerHTML = '';
    
    for (const [key, value] of Object.entries(env)) {
        const row = document.createElement('div');
        row.className = 'form-row mb-2 env-row';
        row.innerHTML = `
            <div class="col">
                <input type="text" class="form-control env-key" value="${key}" readonly>
            </div>
            <div class="col">
                <input type="text" class="form-control env-value" value="${value}">
            </div>
            <div class="col-auto">
                <button type="button" class="btn btn-danger btn-sm" onclick="removeEnvRow(this)">Remove</button>
            </div>
        `;
        envRows.appendChild(row);
    }
}

function getCurrentEnv() {
    const env = {};
    document.querySelectorAll('.env-row').forEach(row => {
        const key = row.querySelector('.env-key').value.trim();
        const value = row.querySelector('.env-value').value.trim();
        if (key) {
            env[key] = value;
        }
    });
    return env;
}

function importEnv(mode) {
    const text = document.getElementById('envBulk').value;
    const newEnv = parseEnvText(text);
    let finalEnv;
    
    if (mode === 'overwrite') {
        finalEnv = newEnv;
    } else { // update
        finalEnv = getCurrentEnv();
        Object.assign(finalEnv, newEnv);
    }
    
    updateEnvRows(finalEnv);
    document.getElementById('envBulk').value = ''; // Clear textarea
}
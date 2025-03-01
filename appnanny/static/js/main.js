document.addEventListener('DOMContentLoaded', function() {
    loadApps();
    setInterval(loadApps, 30000); // Refresh every 30 seconds

    // Handle form submission
    document.getElementById('createAppForm').addEventListener('submit', function(e) {
        e.preventDefault();
        createApp();
    });
});


function loadApps() {
    fetch('/apps')
        .then(response => response.json())
        .then(apps => {
            const tbody = document.getElementById('appsTableBody');
            tbody.innerHTML = '';
            
            Object.entries(apps).forEach(([name, app]) => {
                const row = document.createElement('tr');
                const appUrl = app.running ? `http://${window.location.hostname}:${app.port}` : '#';
                row.innerHTML = `
                    <td>
                        <a href="${appUrl}" target="_blank" 
                           class="${app.running ? '' : 'text-muted'}"
                           ${app.running ? '' : 'style="pointer-events: none;"'}>
                            ${name}
                        </a>
                    </td>
                    <td>${app.type}</td>
                    <td>${app.port || 'N/A'}</td>
                    <td><span class="status-${app.running ? 'active' : 'inactive'}">
                        ${app.running ? 'Running' : 'Stopped'}
                    </span></td>
                    <td><span class="uptime">${formatUptime(app.uptime)}</span></td>
                    <td>
                        ${app.running ? 
                            `<button onclick="stopApp('${name}')" class="btn btn-sm btn-danger">Stop</button>` :
                            `<button onclick="startApp('${name}')" class="btn btn-sm btn-success">Start</button>`
                        }
                        <button onclick="restartApp('${name}')" class="btn btn-sm btn-warning">Restart</button>
                        <button onclick="window.location.href='/env/${name}'" class="btn btn-sm btn-info">Env</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        })
        .catch(error => {
            showNotification('Error loading apps', 'error');
            console.error('Error loading apps:', error);
        });
}

function stopApp(name) {
    fetch(`/stop/${name}`, { method: 'POST' })
        .then(response => response.json())
        .then(result => {
            showNotification(result.message, 'success');
            loadApps();
        })
        .catch(error => {
            showNotification(`Error stopping ${name}`, 'error');
            console.error('Error stopping app:', error);
        });
}

function startApp(name) {
    fetch(`/start/${name}`, { method: 'POST' })
        .then(response => response.json())
        .then(result => {
            showNotification(result.message, 'success');
            loadApps();
        })
        .catch(error => {
            showNotification(`Error starting ${name}`, 'error');
            console.error('Error starting app:', error);
        });
}

function restartApp(name) {
    fetch(`/restart/${name}`, { method: 'POST' })
        .then(response => response.json())
        .then(result => {
            showNotification(result.message, 'success');
            loadApps();
        })
        .catch(error => {
            showNotification(`Error restarting ${name}`, 'error');
            console.error('Error restarting app:', error);
        });
}

function formatUptime(seconds) {
    if (!seconds) return 'N/A';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
}
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('createAppForm').addEventListener('submit', function(e) {
        e.preventDefault();
        createApp();
    });
});

function createApp() {
    const data = {
        name: document.getElementById('appName').value,
        type: document.getElementById('appType').value,
        repo: document.getElementById('repoUrl').value,
        path: document.getElementById('path').value,
        email: document.getElementById('email').value,
        env: JSON.parse(document.getElementById('envVars').value)
    };

    fetch('/create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        showNotification(result.message, 'success');
        document.getElementById('createAppForm').reset();
    })
    .catch(error => {
        showNotification(error.message || 'Error creating app', 'error');
        console.error('Error creating app:', error);
    });
}
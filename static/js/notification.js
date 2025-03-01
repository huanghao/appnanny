function showNotification(message, type = 'success') {
    const container = document.getElementById('notification-container');
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    container.appendChild(notification);

    if (type === 'success') {
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => {
                container.removeChild(notification);
            }, 500);
        }, 3000);
    } else {
        // Add close button for error notifications
        const closeButton = document.createElement('button');
        closeButton.className = 'close ml-2';
        closeButton.innerHTML = '&times;';
        closeButton.onclick = () => {
            notification.style.opacity = '0';
            setTimeout(() => {
                container.removeChild(notification);
            }, 500);
        };
        notification.appendChild(closeButton);
    }
}

// Export for use in other files
window.showNotification = showNotification;
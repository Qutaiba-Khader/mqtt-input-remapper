// App-wide utility functions
function showNotification(message, type = 'success') {
    const alertClass = type === 'success' ? 'alert-success' : 
                      type === 'warning' ? 'alert-warning' : 'alert-danger';
    
    const alert = document.createElement('div');
    alert.className = `alert ${alertClass}`;
    alert.textContent = message;
    alert.style.position = 'fixed';
    alert.style.top = '20px';
    alert.style.right = '20px';
    alert.style.zIndex = '1000';
    alert.style.minWidth = '300px';
    
    document.body.appendChild(alert);
    
    setTimeout(() => alert.remove(), 3000);
}

function formatTimestamp(timestamp) {
    return new Date(timestamp).toLocaleString();
}

// Set active nav link
document.addEventListener('DOMContentLoaded', () => {
    const currentPath = window.location.pathname;
    document.querySelectorAll('nav a').forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || 
            (currentPath === '/' && href === '/') ||
            (currentPath === '/index.html' && href === '/')) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
});

// Dashboard JavaScript
// Handles charts, logout, and data loading

let requestsChart = null;
let modelsChart = null;

// Logout handler
document.getElementById('logoutBtn').addEventListener('click', async () => {
    try {
        await fetch('/api/auth/logout', {
            method: 'POST',
            credentials: 'include'
        });
        window.location.href = '/';
    } catch (error) {
        console.error('Logout error:', error);
        window.location.href = '/';
    }
});

// Chart creation functions
function updateRequestsChart(data) {
    const ctx = document.getElementById('requestsChart').getContext('2d');
    
    // Sort by date and take last 7 days
    const sortedData = data.sort((a, b) => new Date(a.date) - new Date(b.date)).slice(-7);
    
    if (requestsChart) {
        requestsChart.destroy();
    }
    
    requestsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: sortedData.map(d => new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
            datasets: [{
                label: 'Requests',
                data: sortedData.map(d => d.count),
                borderColor: 'rgb(147, 51, 234)',
                backgroundColor: 'rgba(147, 51, 234, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

function updateModelsChart(data) {
    const ctx = document.getElementById('modelsChart').getContext('2d');
    
    // Take top 5 models
    const topModels = data.slice(0, 5);
    
    if (modelsChart) {
        modelsChart.destroy();
    }
    
    modelsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topModels.map(d => d.model_name || 'Unknown'),
            datasets: [{
                label: 'Requests',
                data: topModels.map(d => d.count),
                backgroundColor: [
                    'rgba(147, 51, 234, 0.8)',
                    'rgba(59, 130, 246, 0.8)',
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(251, 191, 36, 0.8)',
                    'rgba(239, 68, 68, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

// Load recent activity
async function loadRecentActivity() {
    try {
        const response = await fetch('/api/usage/logs?limit=5', { credentials: 'include' });
        if (!response.ok) return;

        const data = await response.json();
        const container = document.getElementById('recentActivity');
        
        if (data.logs.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center py-8">No recent activity</p>';
            return;
        }

        container.innerHTML = data.logs.map(log => {
            const date = new Date(log.request_time);
            const timeAgo = getTimeAgo(date);
            
            return `
                <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div class="flex-1">
                        <p class="font-medium text-gray-900">${log.model_name || 'Unknown Model'}</p>
                        <p class="text-sm text-gray-600">${log.endpoint} • ${log.token_name}</p>
                    </div>
                    <div class="text-right">
                        <p class="text-sm font-medium ${log.status_code === 200 ? 'text-green-600' : 'text-red-600'}">
                            ${log.status_code}
                        </p>
                        <p class="text-xs text-gray-500">${timeAgo}</p>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Error loading recent activity:', error);
    }
}

function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
}

// Initialize dashboard
async function initDashboard() {
    await loadUserInfo();
    await loadStats();
    await loadRecentActivity();
    
    // Refresh data every 30 seconds
    setInterval(async () => {
        await loadStats();
        await loadRecentActivity();
    }, 30000);
}

// Start loading data when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboard);
} else {
    initDashboard();
}

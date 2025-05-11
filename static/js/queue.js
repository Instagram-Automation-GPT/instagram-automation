function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function refreshQueue() {
    const queueList = document.getElementById('queueList');
    queueList.innerHTML = '<div class="col-span-full flex justify-center items-center py-8"><div class="queue-loading-spinner"></div></div>';

    fetch('/queue_log/')
        .then(response => response.json())
        .then(data => {
            queueList.innerHTML = '';
            if (data.length === 0) {
                queueList.innerHTML = '<div class="col-span-full text-center text-gray-500 py-8">No items in queue</div>';
                return;
            }

            // Loop through each queue item and add it to the grid
            data.forEach(item => {
                // Determine status based on true_percentage and Error
                const isComplete = item.true_percentage === 100;
                const hasError = item.Error === true;
                let status = 'pending';
                
                if (isComplete) {
                    status = 'completed';
                } else if (hasError) {
                    status = 'failed';
                } else if (item.true_percentage > 0) {
                    status = 'processing';
                }
                
                const statusClass = getStatusClass(status);
                const statusText = getStatusText(status);
                
                // Format timestamp for display
                const formattedDate = formatTimestamp(item.timestamp);
                
                // Create media preview based on file extension
                const fileExtension = item.image.split('.').pop().toLowerCase();
                const isVideo = fileExtension === 'mp4' || fileExtension === 'mov';
                const mediaPreview = isVideo ? 
                    `<div class="media-preview video-preview">
                        <i class="fas fa-play-circle"></i>
                        <span>Video</span>
                    </div>` : 
                    `<div class="media-preview image-preview">
                        <img src="/image/${item.image}" alt="Preview" onerror="this.onerror=null; this.src='/static/images/placeholder.jpg';">
                    </div>`;
                
                // Create the queue item element
                const queueItem = document.createElement('div');
                queueItem.className = 'queue-item';
                queueItem.innerHTML = `
                    <div class="queue-item-header">
                        <h3 class="queue-item-title">Queue #${item.id}</h3>
                        <span class="queue-item-status ${statusClass}">${statusText}</span>
                    </div>
                    <div class="queue-preview">
                        ${mediaPreview}
                    </div>
                    <div class="queue-item-details">
                        <div class="queue-item-detail">
                            <span class="queue-item-label">Created</span>
                            <span class="queue-item-value">${formattedDate}</span>
                        </div>
                        <div class="queue-item-detail">
                            <span class="queue-item-label">Caption</span>
                            <span class="queue-item-value queue-item-caption">${item.caption || 'No caption'}</span>
                        </div>
                        <div class="queue-item-detail">
                            <span class="queue-item-label">Accounts</span>
                            <span class="queue-item-value">${item.account_count || 0}</span>
                        </div>
                        <div class="queue-item-detail">
                            <span class="queue-item-label">Progress</span>
                            <div class="flex items-center gap-2">
                                <div class="flex-grow bg-gray-200 rounded-full h-2">
                                    <div class="bg-blue-600 h-2 rounded-full" style="width: ${item.true_percentage || 0}%"></div>
                                </div>
                                <span class="queue-item-value whitespace-nowrap">${item.true_percentage || 0}%</span>
                            </div>
                        </div>
                    </div>
                    <div class="queue-item-actions">
                        <a href="/queue_details?id=${item.id}" class="queue-item-button btn btn-info">
                            <i class="fas fa-info-circle mr-1"></i>Details
                        </a>
                        <button class="queue-item-button btn btn-primary" onclick="retryItem(${item.id})">
                            <i class="fas fa-redo mr-1"></i>Retry
                        </button>
                        <button class="queue-item-button btn btn-danger" onclick="deleteItem(${item.id})">
                            <i class="fas fa-trash mr-1"></i>Delete
                        </button>
                    </div>
                `;
                
                // Add the item to the grid
                queueList.appendChild(queueItem);
            });
        })
        .catch(error => {
            console.error('Error fetching queue:', error);
            queueList.innerHTML = '<div class="col-span-full text-center text-red-500 py-8">Error loading queue items</div>';
        });
}

function getStatusClass(status) {
    switch (status) {
        case 'pending':
            return 'status-pending';
        case 'processing':
            return 'status-processing';
        case 'completed':
            return 'status-completed';
        case 'failed':
            return 'status-failed';
        default:
            return 'status-pending';
    }
}

function getStatusText(status) {
    switch (status) {
        case 'pending':
            return 'Pending';
        case 'processing':
            return 'Processing';
        case 'completed':
            return 'Completed';
        case 'failed':
            return 'Failed';
        default:
            return 'Unknown';
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function retryItem(itemId) {
    fetch(`/queue_retry_data/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ id: itemId })
    })
    .then(response => {
        if (response.ok) {
            refreshQueue();
            alert('Queue item retry initiated successfully');
        } else {
            return response.json().then(data => {
                throw new Error(data.error || 'Failed to retry item');
            });
        }
    })
    .catch(error => {
        console.error('Error retrying item:', error);
        alert(error.message || 'Error retrying item');
    });
}

function deleteItem(itemId) {
    if (!confirm('Are you sure you want to delete this item?')) {
        return;
    }

    fetch(`/delete_queue/${itemId}/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => {
        if (response.ok) {
            refreshQueue();
            alert('Item deleted successfully');
        } else {
            return response.json().then(data => {
                throw new Error(data.error || 'Failed to delete item');
            });
        }
    })
    .catch(error => {
        console.error('Error deleting item:', error);
        alert(error.message || 'Error deleting item');
    });
}

// Helper function to format timestamp like "2025-05-10 103853" to readable date
function formatTimestamp(timestamp) {
    if (!timestamp) return 'Unknown';
    
    // Check if the timestamp is in the expected format
    const match = timestamp.match(/^(\d{4})-(\d{2})-(\d{2}) (\d{2})(\d{2})(\d{2})$/);
    if (match) {
        const [_, year, month, day, hour, minute, second] = match;
        return `${year}/${month}/${day} ${hour}:${minute}:${second}`;
    }
    
    return timestamp; // Return as is if not in expected format
}

// Initialize queue on page load
document.addEventListener('DOMContentLoaded', function() {
    refreshQueue();
});

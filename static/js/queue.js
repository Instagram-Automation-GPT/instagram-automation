// ===== Queue Page JS (latest first) =====

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

// Convert various timestamp formats into milliseconds for reliable sorting
function parseTimestamp(ts) {
    if (!ts) return 0;

    // Numeric epoch (seconds or milliseconds)
    const n = Number(ts);
    if (!Number.isNaN(n)) return n < 1e12 ? n * 1000 : n;

    // "YYYY-MM-DD HHMMSS"
    let m = String(ts).match(/^(\d{4})-(\d{2})-(\d{2}) (\d{2})(\d{2})(\d{2})$/);
    if (m) {
        const [, y, mo, d, h, mi, s] = m.map(Number);
        return new Date(y, mo - 1, d, h, mi, s).getTime();
    }

    // "YYYY-MM-DD HH:MM:SS" or ISO-like "YYYY-MM-DDTHH:MM:SS"
    m = String(ts).match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2}):(\d{2})$/);
    if (m) {
        const [, y, mo, d, h, mi, s] = m.map(Number);
        return new Date(y, mo - 1, d, h, mi, s).getTime();
    }

    const d = new Date(ts);
    return isNaN(d) ? 0 : d.getTime();
}

// Helper to format "2025-05-10 103853" -> "2025/05/10 10:38:53"
function formatTimestamp(timestamp) {
    if (!timestamp) return 'Unknown';
    const match = String(timestamp).match(/^(\d{4})-(\d{2})-(\d{2}) (\d{2})(\d{2})(\d{2})$/);
    if (match) {
        const [_, year, month, day, hour, minute, second] = match;
        return `${year}/${month}/${day} ${hour}:${minute}:${second}`;
    }
    // Fallback: show as-is (or you can use new Date(timestamp).toLocaleString())
    return timestamp;
}

function refreshQueue() {
    const queueList = document.getElementById('queueList');
    queueList.innerHTML = '<div class="col-span-full flex justify-center items-center py-8"><div class="queue-loading-spinner"></div></div>';

    fetch('/queue_log/')
        .then(response => response.json())
        .then(data => {
            if (!Array.isArray(data) || data.length === 0) {
                queueList.innerHTML = '<div class="col-span-full text-center text-gray-500 py-8">No items in queue</div>';
                return;
            }

            // Sort newest first by timestamp (then by id if equal/missing)
            data.sort((a, b) => {
                const tb = parseTimestamp(b.timestamp);
                const ta = parseTimestamp(a.timestamp);
                if (tb !== ta) return tb - ta;
                return (Number(b.id) || 0) - (Number(a.id) || 0);
            });

            // Clear the grid before rendering
            queueList.innerHTML = '';

            // Render items
            data.forEach(item => {
                const isComplete = item.true_percentage === 100;
                const hasError = item.Error === true;
                let status = 'pending';
                if (isComplete) status = 'completed';
                else if (hasError) status = 'failed';
                else if ((item.true_percentage || 0) > 0) status = 'processing';

                const statusClass = getStatusClass(status);
                const statusText = getStatusText(status);

                const formattedDate = formatTimestamp(item.timestamp);

                const imgName = item.image || '';
                const fileExtension = imgName.split('.').pop().toLowerCase();
                const isVideo = ['mp4', 'mov', 'webm'].includes(fileExtension);

                const safeSrc = `/image/${encodeURIComponent(imgName)}`;

                const mediaPreview = isVideo
                    ? `<div class="media-preview video-preview">
                          <i class="fas fa-play-circle"></i>
                          <span>Video</span>
                       </div>`
                    : `<div class="media-preview image-preview">
                          <img src="${safeSrc}" alt="Preview" onerror="this.onerror=null; this.src='/static/images/placeholder.jpg';">
                       </div>`;

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
                                    <div class="bg-blue-600 h-2 rounded-full" style="width: ${(item.true_percentage || 0)}%"></div>
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
        case 'pending': return 'status-pending';
        case 'processing': return 'status-processing';
        case 'completed': return 'status-completed';
        case 'failed': return 'status-failed';
        default: return 'status-pending';
    }
}

function getStatusText(status) {
    switch (status) {
        case 'pending': return 'Pending';
        case 'processing': return 'Processing';
        case 'completed': return 'Completed';
        case 'failed': return 'Failed';
        default: return 'Unknown';
    }
}

// Optional generic formatter (unused in rendering but kept if needed elsewhere)
function formatDate(dateString) {
    const date = new Date(dateString);
    return isNaN(date) ? String(dateString) : date.toLocaleString();
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
    if (!confirm('Are you sure you want to delete this item?')) return;

    fetch(`/delete_queue/${itemId}/`, {
        method: 'GET',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
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

// Initialize queue on page load
document.addEventListener('DOMContentLoaded', function () {
    refreshQueue();
});

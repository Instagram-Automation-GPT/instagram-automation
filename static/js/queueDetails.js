async function fetchQueueDetails(id) {
    try {
        let idAsInt = parseInt(id, 10);
        const response = await fetch(`/queue_d/`, {
            method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
            body: JSON.stringify({ id: idAsInt })
        });
        
        if (!response.ok) {
            throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Queue details data:', data);

        // Update the basic info section
        document.getElementById('queue-id').textContent = data.id;
        document.getElementById('queue-timestamp').textContent = formatTimestamp(data.timestamp);
        document.getElementById('queue-account-count').textContent = data.account_count;
        document.getElementById('queue-account-caption').textContent = data.caption || 'No caption';
        document.getElementById('queue-error').textContent = data.Error ? "Yes" : "No";
        document.getElementById('queue-true-percentage').textContent = data.true_percentage;
        
        // Handle media display
        const filePath = data.image;
        const fileExtension = filePath.split('.').pop().toLowerCase();
        const mediaElement = document.getElementById("queue-media");
        const videoLink = document.getElementById("queue-video-link");
        const videoPlayer = document.getElementById("queue-video");

        if (fileExtension === "mp4" || fileExtension === "mov") {
            // Show video link
            videoLink.href = `/video/${filePath}`;
            videoLink.classList.remove("hidden");
            mediaElement.classList.add("hidden");
            videoPlayer.classList.add("hidden");
        } else {
            // Show image
            mediaElement.src = `/image/${filePath}`;
            mediaElement.classList.remove("hidden");
            videoLink.classList.add("hidden");
            videoPlayer.classList.add("hidden");
        }

        // Display accounts information
        const accountsDiv = document.getElementById('accounts');
        accountsDiv.innerHTML = ''; // Clear previous content
        
        if (data.accounts && Array.isArray(data.accounts)) {
            data.accounts.forEach(account => {
                const accountDiv = document.createElement('div');
                accountDiv.classList.add('account', 'mb-4', 'p-4', 'bg-gray-50', 'rounded-lg', 'shadow-sm');
    
                const storyStatusClass = account.story_status === true ? 'text-green-600' : 
                                        account.story_status === false ? 'text-red-600' : 'text-gray-400';
                const postStatusClass = account.post_status === true ? 'text-green-600' : 
                                       account.post_status === false ? 'text-red-600' : 'text-gray-400';
    
                accountDiv.innerHTML = `
                    <p class="mb-2"><strong class="text-gray-700">Username:</strong> <span class="text-gray-900">${account.username || 'Unknown'}</span></p>
                    <p class="mb-2"><strong class="text-gray-700">Last Check:</strong> <span class="text-gray-900">${account.lastCheck || 'N/A'}</span></p>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
                        <div class="bg-white p-3 rounded-md shadow-sm">
                            <h4 class="font-semibold text-gray-800 mb-2">Story</h4>
                            <p class="mb-1"><strong class="text-gray-700">Status:</strong> <span class="${storyStatusClass}">${formatStatus(account.story_status)}</span></p>
                            <p class="mb-1"><strong class="text-gray-700">Message:</strong> <span class="text-gray-900">${account.story_message || 'N/A'}</span></p>
                        </div>
                        
                        <div class="bg-white p-3 rounded-md shadow-sm">
                            <h4 class="font-semibold text-gray-800 mb-2">Post</h4>
                            <p class="mb-1"><strong class="text-gray-700">Status:</strong> <span class="${postStatusClass}">${formatStatus(account.post_status)}</span></p>
                            <p class="mb-1"><strong class="text-gray-700">Message:</strong> <span class="text-gray-900">${account.post_message || 'N/A'}</span></p>
                        </div>
                    </div>
                    
                    <div class="mt-3 bg-gray-50 p-3 rounded-md">
                        <p><strong class="text-gray-700">Caption:</strong></p>
                        <p class="text-sm text-gray-800 whitespace-pre-line">${account.caption || 'No caption'}</p>
                    </div>
                `;
    
                accountsDiv.appendChild(accountDiv);
            });
        } else {
            accountsDiv.innerHTML = '<p class="text-gray-500">No account information available</p>';
        }
    } catch (error) {
        console.error('Error fetching queue details:', error);
        document.getElementById('queue-details').innerHTML = `
            <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
                <strong class="font-bold">Error!</strong>
                <span class="block sm:inline">Failed to load queue details: ${error.message}</span>
            </div>
        `;
    }
}

// Format status display
function formatStatus(status) {
    if (status === true) return 'Success';
    if (status === false) return 'Failed';
    return 'Pending';
}

// Format timestamp
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

function getQueryParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

document.addEventListener('DOMContentLoaded', () => {
    const id = getQueryParameter('id');
    if (id) {
        fetchQueueDetails(id);
    } else {
        document.getElementById('queue-details').innerHTML = `
            <div class="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded relative" role="alert">
                <strong class="font-bold">Warning:</strong>
                <span class="block sm:inline">No queue ID specified. Please go back to the queue list and select an item.</span>
            </div>
        `;
    }
});
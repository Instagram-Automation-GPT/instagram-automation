// Function to get a cookie value by name
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

// Function to show loading state
function showLoading() {
    document.body.classList.add('loading');
    const loadingContainer = document.createElement('div');
    loadingContainer.className = 'loading-container';
    loadingContainer.innerHTML = `
        <div class="loading-spinner"></div>
        <div class="loading-text">Loading dashboard...</div>
    `;
    document.body.appendChild(loadingContainer);
}

// Function to hide loading state
function hideLoading() {
    document.body.classList.remove('loading');
    const loadingContainer = document.querySelector('.loading-container');
    if (loadingContainer) {
        loadingContainer.remove();
    }
}

// Function to show progress
function showProgress(progress) {
    document.body.classList.add('loading');
    const progressContainer = document.createElement('div');
    progressContainer.className = 'progress-container';
    progressContainer.innerHTML = `
        <div class="progress-bar-container">
            <div class="progress-bar-fill" style="width: ${progress}%"></div>
        </div>
        <div class="progress-text">Loading ${progress}%</div>
    `;
    document.body.appendChild(progressContainer);
}

// Function to update progress
function updateProgress(progress) {
    const progressContainer = document.querySelector('.progress-container');
    if (progressContainer) {
        const progressBar = progressContainer.querySelector('.progress-bar-fill');
        const progressText = progressContainer.querySelector('.progress-text');
        if (progressBar) progressBar.style.width = `${progress}%`;
        if (progressText) progressText.textContent = `Loading ${progress}%`;
    }
}

// Function to hide progress
function hideProgress() {
    document.body.classList.remove('loading');
    const progressContainer = document.querySelector('.progress-container');
    if (progressContainer) {
        progressContainer.remove();
    }
}

// Combined JavaScript function to fetch data and edit account
async function fetchAndEditData() {
    showLoading();

    try {
        const headers = {
            'X-CSRFToken': getCookie('csrftoken'),
        };

        const response = await fetch('/insta_sessions/', { headers });
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }

        const responseData = await response.json();
        const accountData = Array.isArray(responseData.message) ? responseData.message : [responseData.message];
        console.log(accountData);
        initializeHTML(accountData);
    } catch (error) {
        console.error('Fetch error: ', error);
    } finally {
        hideLoading();
    }
}

// Function to initialize HTML elements with fetched data
function initializeHTML(accountData) {
    const container = document.querySelector('.data-container');
    container.innerHTML = '';

    let healthyCount = 0;
    let unhealthyCount = 0;

    accountData.forEach(account => {
        const accountDiv = document.createElement('div');
        accountDiv.classList.add('account-card');

        const accountHeader = document.createElement('div');
        accountHeader.classList.add('account-card-header');

        const accountTitle = document.createElement('div');
        accountTitle.classList.add('account-card-title');
        accountTitle.textContent = account.username;
        accountHeader.appendChild(accountTitle);

        const accountStatus = document.createElement('div');
        accountStatus.classList.add('account-card-status');
        accountStatus.classList.add(account.status.toLowerCase() === 'healthy' ? 'status-healthy' : 'status-unhealthy');
        accountStatus.textContent = account.status;
        accountHeader.appendChild(accountStatus);

        accountDiv.appendChild(accountHeader);

        const details = ['Username', 'Timestamp', 'AntiBan', 'Status', 'Message', 'Description', 'Hashtags'];
        details.forEach(detail => {
            const p = document.createElement('p');
            if (detail === 'Message') {
                p.textContent = `${detail}: ${account[detail.toLowerCase()] || 'OK!'}`;
            } else if (detail === 'AntiBan') {
                p.textContent = `${detail}: ${account[detail.toLowerCase()] === undefined ? 'soon!' : account[detail.toLowerCase()]}`;
            } else if (detail === 'Description' || detail === 'Hashtags') {
                const editableDiv = document.createElement('div');
                editableDiv.className = 'editable-field';

                const inputGroup = document.createElement('div');
                inputGroup.className = 'input-group';

                const input = document.createElement('input');
                input.type = 'text';
                input.className = 'form-control';
                input.placeholder = `Click to add ${detail.toLowerCase()}`;
                input.value = account[detail.toLowerCase()] || '';

                const buttonGroup = document.createElement('div');
                buttonGroup.className = 'input-group-append';

                const saveButton = document.createElement('button');
                saveButton.className = 'btn btn-outline-primary save-btn';
                saveButton.innerHTML = '<i class="fas fa-check"></i>';
                saveButton.title = 'Save changes';

                const cancelButton = document.createElement('button');
                cancelButton.className = 'btn btn-outline-secondary cancel-btn';
                cancelButton.innerHTML = '<i class="fas fa-times"></i>';
                cancelButton.title = 'Cancel';

                buttonGroup.appendChild(saveButton);
                buttonGroup.appendChild(cancelButton);
                inputGroup.appendChild(input);
                inputGroup.appendChild(buttonGroup);
                editableDiv.appendChild(inputGroup);

                // Add notification element
                const notification = document.createElement('div');
                notification.className = 'notification';
                editableDiv.appendChild(notification);

                // Handle save button click
                saveButton.addEventListener('click', async () => {
                    const value = input.value.trim();
                    if (value !== account[detail.toLowerCase()]) {
                        // Show in-progress notification
                        notification.className = 'notification in-progress';
                        notification.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';

                        try {
                            await saveUpdatedDetail(detail.toLowerCase(), value, account);
                            account[detail.toLowerCase()] = value;

                            // Show success notification
                            notification.className = 'notification success';
                            notification.innerHTML = '<i class="fas fa-check-circle"></i> Saved successfully!';

                            // Hide notification after 3 seconds
                            setTimeout(() => {
                                notification.className = 'notification';
                                notification.innerHTML = '';
                            }, 3000);
                        } catch (error) {
                            // Show error notification
                            notification.className = 'notification error';
                            notification.innerHTML = '<i class="fas fa-exclamation-circle"></i> Failed to save!';

                            // Hide notification after 3 seconds
                            setTimeout(() => {
                                notification.className = 'notification';
                                notification.innerHTML = '';
                            }, 3000);
                        }
                    }
                });

                // Handle cancel button click
                cancelButton.addEventListener('click', () => {
                    input.value = account[detail.toLowerCase()] || '';
                });

                p.textContent = `${detail}: `;
                p.appendChild(editableDiv);
            } else {
                p.textContent = `${detail}: ${account[detail.toLowerCase()]}`;
            }
            accountDiv.appendChild(p);
        });

        const actionsDiv = document.createElement('div');
        actionsDiv.classList.add('account-card-actions');

        if (account.status.toLowerCase() === 'unhealthy') {
            const reloginButton = document.createElement('button');
            reloginButton.textContent = 'Re-login';
            reloginButton.className = 'btn btn-primary';
            reloginButton.addEventListener('click', () => reloginAccount(account));
            actionsDiv.appendChild(reloginButton);
        }

        const editButton = document.createElement('button');
        editButton.textContent = 'Edit';
        editButton.className = 'btn btn-secondary';
        editButton.addEventListener('click', () => editAccount(account));
        actionsDiv.appendChild(editButton);

        const deleteButton = document.createElement('button');
        deleteButton.textContent = 'Delete';
        deleteButton.className = 'btn btn-danger';
        deleteButton.addEventListener('click', () => {
            if (confirm('Are you sure you want to delete this account?')) {
                deleteAccount(account);
            }
        });
        actionsDiv.appendChild(deleteButton);

        accountDiv.appendChild(actionsDiv);

        if (account.status.toLowerCase() === 'healthy') {
            healthyCount++;
        } else if (account.status.toLowerCase() === 'unhealthy') {
            unhealthyCount++;
        }

        container.appendChild(accountDiv);
    });

    document.getElementById('healthy').textContent = `Healthy accounts: ${healthyCount}`;
    document.getElementById('unhealthy').textContent = `Unhealthy accounts: ${unhealthyCount}`;
}

function deleteAccount(account) {
    var formData = new FormData();
    formData.append('user', account.username);

    fetch('/delete_session/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
    })
        .then(response => {
            if (response.ok) {
                window.location.reload(true);
            } else {
                throw new Error('Failed to delete session');
            }
        })
        .catch(error => {
            console.error('There was a problem with delete session:', error);
        });
}

// Function to handle edit button click
function editAccount(account) {
    const username = account.username;
    console.log(`Editing account: ${username}`);

    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('editModal'));
    modal.show();

    // Populate username field
    document.getElementById('currentUsername').value = username;

    // Clear previous tick marks
    document.getElementById('usernameChangeTick').checked = false;
    document.getElementById('fullnameChangeTick').checked = false;
    document.getElementById('imageChangeTick').checked = false;

    // When the form inputs change, tick the boxes
    document.getElementById('newUsername').addEventListener('input', function () {
        document.getElementById('usernameChangeTick').checked = this.value.trim() !== '';
    });
    document.getElementById('newFullname').addEventListener('input', function () {
        document.getElementById('fullnameChangeTick').checked = this.value.trim() !== '';
    });
    document.getElementById('imageUpload').addEventListener('change', function () {
        document.getElementById('imageChangeTick').checked = this.files.length > 0;
    });

    // When the form is submitted
    document.getElementById('editForm').onsubmit = function (event) {
        event.preventDefault();

        const newUsername = document.getElementById('newUsername').value.trim();
        const newFullname = document.getElementById('newFullname').value.trim();
        const image = document.getElementById('imageUpload').files[0];

        const payload = {
            old_username: username,
            new_username: newUsername || null,
            new_fullname: newFullname || null,
            image: image || null
        };

        // Show a progress bar or indicator
        const progressBar = document.getElementById('progress-bar');
        const progressBarFill = document.getElementById('progress-bar-fill');
        progressBar.style.display = 'flex';

        let progress = 0;
        const interval = setInterval(() => {
            if (progress < 100) {
                progress += 5;
                progressBarFill.style.width = `${progress}%`;
            } else {
                clearInterval(interval);
            }
        }, 70);

        // Handle separate requests based on changes
        const requests = [];

        // If username is changed, send the username change request
        if (newUsername) {
            requests.push(fetch('/username_change/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ old_username: username, new_username: newUsername })
            }));
        }

        // If fullname is changed, send the fullname change request
        if (newFullname) {
            requests.push(fetch('/new_fullname/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username: username, new_fullname: newFullname })
            }));
        }

        // If profile image is changed, send the image upload request
        if (image) {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('image', image);

            requests.push(fetch('/profile_change/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: formData
            }));
        }



        // Wait for all requests to finish
        Promise.all(requests)
            .then(responses => {
                return Promise.all(responses.map(response => response.json()));
            })
            .then(data => {
                clearInterval(interval);
                progressBar.style.display = 'none';

                // Check if all requests were successful
                const allSuccess = data.every(response => response.success);
                if (allSuccess) {
                    alert(`Changes saved successfully for ${username}!`);
                    if (newUsername) account.username = newUsername;
                    if (newFullname) account.fullname = newFullname;
                } else {
                    alert('Failed to update one or more fields!');
                }
                modal.hide();
            })
            .catch(error => {
                clearInterval(interval);
                progressBar.style.display = 'none';
                console.error('Error updating:', error);
                alert('Error updating!');
                modal.hide();
            });
    };
}

// Function to save updated account details
function saveUpdatedDetail(detail, value, account) {
    const csrftoken = getCookie('csrftoken');

    const formData = new FormData();
    formData.append('username', account.username);
    formData.append('description', detail === 'description' ? value : '');
    formData.append('hashtags', detail === 'hashtags' ? value : '');

    const fetchOptions = {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrftoken
        }
    };

    fetch('/edit_session_list/', fetchOptions)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            console.log('Detail updated successfully');
            window.alert('Updated successfully!');
        })
        .catch(error => {
            console.error('Failed to update detail:', error.message);
            window.alert('Failed to update: ' + error.message);
        });
}


function sleep(milliseconds) {
    return new Promise(resolve => setTimeout(resolve, milliseconds));
}

// Initialize data when the document is ready
document.addEventListener('DOMContentLoaded', fetchAndEditData);

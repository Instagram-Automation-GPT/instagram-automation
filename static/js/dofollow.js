document.addEventListener('DOMContentLoaded', function () {
    // Select/Deselect All for Accounts
    document.getElementById('selectAllAccounts').addEventListener('click', function () {
        document.querySelectorAll('.account-checkbox').forEach(function (checkbox) {
            checkbox.checked = true;
        });
    });

    document.getElementById('deselectAllAccounts').addEventListener('click', function () {
        document.querySelectorAll('.account-checkbox').forEach(function (checkbox) {
            checkbox.checked = false;
        });
    });

    // Select/Deselect All for People to Follow
    document.getElementById('selectAllPeople').addEventListener('click', function () {
        document.querySelectorAll('.people-checkbox').forEach(function (checkbox) {
            checkbox.checked = true;
        });
    });

    document.getElementById('deselectAllPeople').addEventListener('click', function () {
        document.querySelectorAll('.people-checkbox').forEach(function (checkbox) {
            checkbox.checked = false;
        });
    });
});

// JavaScript function to fetch data from the server-side
async function fetchData() {
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

    await sleep(700);

    const headers = {
        'X-CSRFToken': getCookie('csrftoken'),
    };

    try {
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
        progressBar.style.display = 'none';
    }
}

function sleep(milliseconds) {
    return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

document.addEventListener('DOMContentLoaded', fetchData);

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}


// Function to initialize HTML elements with fetched data
function initializeHTML(accountData) {
    const container = document.querySelector('.data-container');
    container.innerHTML = '';

    accountData.forEach(account => {
        const accountDiv = document.createElement('li');
        accountDiv.classList.add('user-details', 'flex', 'items-center', 'gap-2');
        
        // Assuming `account` is an object with properties `username` and `user_id`
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'account-checkbox';
        checkbox.id = `account-${account.username}`;
        checkbox.setAttribute('data-user-id', account.user_id); // Adding data-user-id
        checkbox.setAttribute('data-username', account.username); // Adding data-username
        
        // Append the checkbox to the accountDiv
        accountDiv.appendChild(checkbox);
        
        // Create the label and set the `for` attribute to match the checkbox ID
        const label = document.createElement('label');
        label.setAttribute('for', `account-${account.username}`);
        label.textContent = account.username;
        
        // Append the label to the accountDiv
        accountDiv.appendChild(label);
        
        // Append the accountDiv to the container (assuming `container` is already selected)
        container.appendChild(accountDiv);
    });

    // Update the progress bar or any other necessary UI elements here
}

// Api to show instagram followers
// Constants for pagination
let selectedFollowers = {}; // Format: { user_id: true }
let currentPage = 1; // Keep track of the current page
const ITEMS_PER_PAGE = 10; // Number of items per page


function renderFollowers() {
    const peopleList = document.getElementById('peopleList');
    peopleList.innerHTML = ''; // Clear current items

    followersList.forEach((follower, index) => {
        const followerItem = document.createElement('li');
        followerItem.className = `user-details flex items-center gap-2 py-1 ${isInCurrentPage(index) ? '' : 'hidden'}`; // Add hidden class if not on current page

        const followedByContent = follower.followed_by && follower.followed_by.length > 0
            ? follower.followed_by.join(', ')
            : 'None';

        // Unique ID for each checkbox
        const checkboxId = `person${index + 1}`;
        const isChecked = selectedFollowers[follower.user_id] || false;

        followerItem.innerHTML = `
            <input type="checkbox" class="people-checkbox" id="${checkboxId}" data-user-id="${follower.user_id}" data-username="${follower.username}" ${isChecked ? 'checked' : ''}>
            <label for="${checkboxId}">${follower.username}</label>
            <p><strong>User-ID:</strong> ${follower.user_id}</p>
            <p><strong>Follower-Category:</strong> ${follower.follow_category}</p>
            <!-- Button to trigger the modal -->
            <button type="button" class="btn-info btn-sm" data-bs-toggle="modal" data-bs-target="#followerModal"
                data-user-id="${follower.user_id}" data-username="${follower.username}" data-followed-by="${followedByContent}">
                <i class="fas fa-question-circle"></i> Followed-By
            </button>
        `;

        peopleList.appendChild(followerItem);

        // Update the global state when a checkbox is clicked
        followerItem.querySelector('input').addEventListener('change', function () {
            selectedFollowers[follower.user_id] = this.checked;
        });
    });

    updatePaginationControls();
}

// Add event listener for opening the modal
document.addEventListener('click', function (event) {
    if (event.target && event.target.matches('[data-bs-toggle="modal"]')) {
        const button = event.target;
        const userId = button.getAttribute('data-user-id');
        const username = button.getAttribute('data-username');
        const followedBy = button.getAttribute('data-followed-by');

        // Populate modal content
        document.getElementById('modal-user-id').textContent = userId;
        document.getElementById('modal-username').textContent = username;
        document.getElementById('modal-followed-by').textContent = followedBy;
    }
});

function isInCurrentPage(index) {
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    const end = start + ITEMS_PER_PAGE;
    return index >= start && index < end;
}

function updatePaginationControls() {
    const paginationControls = document.getElementById('pagination-controls');
    paginationControls.innerHTML = ''; // Clear current controls

    // Create Previous Button
    const prevButton = document.createElement('button');
    prevButton.innerText = 'Previous';
    prevButton.className = 'btn btn-secondary btn-sm me-2'; // Bootstrap classes for styling
    prevButton.disabled = currentPage === 1;
    prevButton.addEventListener('click', () => {
        currentPage--;
        renderFollowers();
    });
    paginationControls.appendChild(prevButton);

    // Create Next Button
    const nextButton = document.createElement('button');
    const totalPages = Math.ceil(followersList.length / ITEMS_PER_PAGE);
    nextButton.innerText = 'Next';
    nextButton.className = 'btn btn-secondary btn-sm'; // Bootstrap classes for styling
    nextButton.disabled = currentPage === totalPages;
    nextButton.addEventListener('click', () => {
        currentPage++;
        renderFollowers();
    });
    paginationControls.appendChild(nextButton);
}

// Function to fetch followers data and initialize pagination
async function fetchFollowersAndInitializePagination() {
    try {
        const response = await fetch('/showing_instagram_followers/');
        const data = await response.json();
        
        console.log(data); // Log data to inspect its structure

        // Check if data is an object with a followers property
        if (data.followers && Array.isArray(data.followers)) {
            followersList = data.followers;
        } else {
            console.error('Unexpected data format:', data);
            return;
        }
        
        renderFollowers(currentPage);

    } catch (error) {
        console.error('Error fetching followers:', error);
    }
}

// Select/Deselect All for People to Follow
document.getElementById('selectAllPeople').addEventListener('click', function () {
    followersList.forEach(follower => {
        selectedFollowers[follower.username] = true;
    });
    renderFollowers(currentPage); // Re-render the current page to reflect selection
});

document.getElementById('deselectAllPeople').addEventListener('click', function () {
    followersList.forEach(follower => {
        selectedFollowers[follower.username] = false;
    });
    renderFollowers(currentPage); // Re-render the current page to reflect deselection
});

// Call the function when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', fetchFollowersAndInitializePagination);

document.getElementById('followButton').addEventListener('click', function () {
    // Gather selected accounts (account names)
    const selectedAccounts = Array.from(document.querySelectorAll('#accountsList .account-checkbox:checked'))
        .map(checkbox => checkbox.getAttribute('data-username')); // Assuming `data-username` holds the account name

    // Gather selected people (user IDs)
    const selectedUserids = Array.from(document.querySelectorAll('#peopleList .people-checkbox:checked'))
        .map(checkbox => checkbox.getAttribute('data-user-id')); // Assuming `data-user-id` holds the user ID

    // Check if at least one account or person is selected
    if (selectedAccounts.length === 0 && selectedUserids.length === 0) {
        alert('Please select at least one account or person to follow.');   
        return;
    }

        // Perform the follow action with the selected accounts/people
        console.log(selectedAccounts, selectedUserids)
        followUsers(selectedAccounts, selectedUserids);
    });

// Function to handle following users
async function followUsers(accounts, people) {
    try {
        const formData = new FormData();

        // Convert the accounts and people arrays to JSON strings
        const accountsJSON = JSON.stringify(accounts);
        const peopleJSON = JSON.stringify(people);

        // Append the JSON strings to the FormData object
        formData.append('accounts', accountsJSON);
        formData.append('accountstofollow', peopleJSON);

        // Create the request options with the FormData object
        const requestOptions = {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: formData,
        };

         // Send the request with the FormData
        const response = await fetch('/follower_params/', requestOptions);

        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }

        const result = await response.json();
        console.log('Follow result:', result);
        alert('Follow action completed successfully!');
    } catch (error) {
        console.error('Error following users:', error);
        alert('An error occurred while trying to follow users.');
    }
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}
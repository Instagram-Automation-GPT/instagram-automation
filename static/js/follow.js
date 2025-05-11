function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function register() {
    // Get the values of username and password inputs
    var username = document.getElementById('username').value;
    var password = document.getElementById('password').value;
    var code = document.getElementById('code').value;
    // Create FormData object
    var formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    formData.append('code', code);

    // Now you can send this formData using AJAX or fetch
    // For example using fetch
    fetch('/follow_instagram_login/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(errorData => {
                // Throw an error with the error message from the server
                throw new Error(errorData.message || 'Network response was not ok');
            });
        }
        return response.json();
    })
    .then(data => {
        // Log the response data to the console
        console.log('Response data:', data);
        // Handle response data here
        // For example, display a success message to the user
        alert(data.message);
    })
    .catch(error => {
        // Log any errors to the console
        console.error('There was a problem with your fetch operation:', error);
        // Display an error message to the user            throw new Error('Network response was not ok');

        alert(`There was an error processing your registration. ${error}`);
    });
}

document.getElementById('openModalButton').addEventListener('click', function() {
    document.getElementById('myModal').classList.remove('hidden');
});

document.getElementById('closeModalButton').addEventListener('click', function() {
    document.getElementById('myModal').classList.add('hidden');
});


// Getting followers of a target user
document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('searchForm');
    const targetUsername = document.getElementById('targetUsername');
    const number = document.getElementById('number');
    const category = document.getElementById('category');
    const searchResults = document.getElementById('searchResults');

    searchForm.addEventListener('submit', function(event) {
        event.preventDefault();  // Prevent the default form submission

        const usernameValue = targetUsername.value.trim();
        const numberValue = parseInt(number.value, 10);
        const categoryValue = category.value;

        // Basic validation
        if (usernameValue === '') {
            alert('Username is required.');
            return;
        }
        if (isNaN(numberValue) || numberValue <= 0) {
            alert('Number must be greater than zero.');
            return;
        }
        if (categoryValue !== 'en') {
            alert('Category must be "en".');
            return;
        }

        const myHeaders = new Headers();
        myHeaders.append("Content-Type", "application/json");

        const raw = JSON.stringify({
            "targetusername": usernameValue,
            "number": numberValue,
            "category": categoryValue
        });

        const requestOptions = {
            method: "POST",
            headers: myHeaders,
            body: raw,
            redirect: "follow"
        };

        fetch("/getting_user_id/", requestOptions)
            .then(response => response.text())
            .then(result => {
                // Update the searchResults div with the result
                searchResults.innerHTML = `<pre>${result}</pre>`;
            })
            .catch(error => console.error('Error:', error));
    });
});


// Api to show instagram followers
// Constants for pagination
const ITEMS_PER_PAGE = 10; // Number of items per page
let currentPage = 1;
let followersList = []; // To store the fetched followers data

// Function to render followers for the current page
function renderFollowers(page) {
    const userList = document.getElementById('userList');
    const paginationControls = document.getElementById('pagination-controls');
    userList.innerHTML = ''; // Clear current items

    // Calculate start and end index for the current page
    const start = (page - 1) * ITEMS_PER_PAGE;
    const end = start + ITEMS_PER_PAGE;
    const paginatedFollowers = followersList.slice(start, end);

    // Render paginated items
    paginatedFollowers.forEach(follower => {
        const followerItem = document.createElement('li');
        followerItem.className = 'border-b border-gray-300 py-2';
        followerItem.innerHTML = `
            <p><strong>Username:</strong> ${follower.username}</p>
            <p><strong>Full Name:</strong> ${follower.full_name}</p>
            <p><strong>Profile Pic:</strong> <a href="${follower.profile_pic_url}" target="_blank" class="text-blue-500 underline">View</a></p>
            <p><strong>Target Username:</strong> ${follower.target_username}</p>
            <p><strong>Follow Category:</strong> ${follower.follow_category}</p>
        `;
        userList.appendChild(followerItem);
    });

    // Render pagination controls
    const totalPages = Math.ceil(followersList.length / ITEMS_PER_PAGE);
    paginationControls.innerHTML = ''; // Clear current controls
    
    // Add "Previous" button
    const prevButton = document.createElement('button');
    prevButton.className = `px-3 py-1 mx-1 rounded ${page > 1 ? 'bg-gray-300 hover:bg-gray-400' : 'bg-gray-200 cursor-not-allowed'}`;
    prevButton.innerText = 'Prev';
    prevButton.disabled = page <= 1;
    prevButton.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            renderFollowers(currentPage);
        }
    });
    paginationControls.appendChild(prevButton);

    // Determine the range of page numbers to display (3 page buttons)
    let startPage = Math.max(1, page - 1);
    let endPage = Math.min(totalPages, page + 1);

    // Adjust the range to ensure we always show 3 pages if possible
    if (endPage - startPage < 2) {
        if (page - 1 < 1) {
            endPage = Math.min(totalPages, endPage + (2 - (endPage - startPage)));
        } else if (page + 1 > totalPages) {
            startPage = Math.max(1, startPage - (2 - (endPage - startPage)));
        }
    }

    // Add page number buttons
    for (let i = startPage; i <= endPage; i++) {
        const button = document.createElement('button');
        button.className = `px-3 py-1 mx-1 rounded ${i === page ? 'bg-blue-500 text-white' : 'bg-gray-300'}`;
        button.innerText = i;
        button.addEventListener('click', () => {
            currentPage = i;
            renderFollowers(currentPage);
        });
        paginationControls.appendChild(button);
    }

    // Add "Next" button
    const nextButton = document.createElement('button');
    nextButton.className = `px-3 py-1 mx-1 rounded ${page < totalPages ? 'bg-gray-300 hover:bg-gray-400' : 'bg-gray-200 cursor-not-allowed'}`;
    nextButton.innerText = 'Next';
    nextButton.disabled = page >= totalPages;
    nextButton.addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            renderFollowers(currentPage);
        }
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

// Call the function when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', fetchFollowersAndInitializePagination);

// Function to fetch extractors data and show the progress bar
async function fetchExtractors() {
    const extractorsList = document.getElementById('extractors-list');
    
    try {
        const response = await fetch('/showing_instagram_extractors_account/');
        const data = await response.json();

        // Fill data into the container
        if (extractorsList) {
            extractorsList.innerHTML = ''; // Clear existing content

            if (data.username && data.password) {
                const sessionDiv = document.createElement('div');
                sessionDiv.innerHTML = `
                    <p><strong>Username:</strong> ${data.username}</p>
                    <p><strong>Password:</strong> ${data.password}</p>
                `;
                extractorsList.appendChild(sessionDiv);
            } else {
                console.error('No session data found or missing fields.');
            }
        }
    } 
    catch (error) {
        console.error('Error fetching followers:', error);
    } 
}

// Call the function when the page loads
document.addEventListener('DOMContentLoaded', fetchExtractors);
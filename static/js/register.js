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
    var twostep = document.getElementById('twostep').value;
    var description = document.getElementById('description').value;
    var hashtags = document.getElementById('hashtags').value;

    // Show the loading spinner
    var loadingSpinner = document.getElementById('loadingSpinner');
    loadingSpinner.style.display = 'inline-block';

    // Create FormData object
    var formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    formData.append('code', code);
    formData.append('twostep', twostep);
    formData.append('description', description);
    formData.append('hashtags', hashtags);

    // Now you can send this formData using AJAX or fetch
    // For example using fetch
    fetch('/submit_register/', {
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
        // Hide the loading spinner
        loadingSpinner.style.display = 'none';
        // Handle response data here
        // For example, display a success message to the user
        alert(data.message);
    })
    .catch(error => {
        // Log any errors to the console
        console.error('There was a problem with your fetch operation:', error);
        // Hide the loading spinner
        loadingSpinner.style.display = 'none';
        // Display an error message to the user
        alert(`There was an error processing your registration. ${error}`);
    });
}

// Function to load session data on page load
document.addEventListener('DOMContentLoaded', function () {

    const progressBarFill = document.getElementById('progressBarFill');
    const loadingProgress = document.getElementById('loadingProgress');

    // Set initial progress bar width
    progressBarFill.style.width = '0%';

    // Simulate progress bar filling up
    let progress = 0;
    const fillProgress = setInterval(() => {
        progress += 5; // Increment progress by 5% every 100ms
        progressBarFill.style.width = `${progress}%`;
        if (progress >= 130) {
            clearInterval(fillProgress); // Stop filling progress bar when it reaches 100%
        }
    }, 100);

    fetch('/insta_sessions/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {

            // Handle response data here
            const sessionData = document.getElementById('sessionData');
            sessionData.innerHTML = ''; // Clear previous data
            data.message.forEach(session => {
                const listItem = document.createElement('li');
                listItem.className = "list-group-item"; // Bootstrap class for styling
                listItem.textContent = `Username: ${session.username}, Timestamp: ${session.timestamp}, AntiBan: ${session.antiBan}, Status: ${session.status}`;
                sessionData.appendChild(listItem);
            });
            loadingProgress.style.display = 'none'; // Hide progress bar
        })
        .catch(error => {
            console.error('There was a problem with your fetch operation:', error);
        });
});

// Initialize Bootstrap tooltips
$(function () {
    $('[data-toggle="tooltip"]').tooltip();
});

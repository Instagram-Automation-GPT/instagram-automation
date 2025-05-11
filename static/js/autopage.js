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

// Function to initialize HTML elements with fetched data
function initializeHTML(accountData) {
    const container = document.querySelector('.data-container');
    container.innerHTML = '';

    let healthyCount = 0;
    let unhealthyCount = 0;

    accountData.forEach(account => {
        const accountDiv = document.createElement('div');
        accountDiv.classList.add('user-details');



        // Add an event listener to select the account when clicked
        accountDiv.addEventListener('click', () => {
            // Toggle the "selected" class to indicate selection
            document.querySelectorAll('.user-details').forEach(div => div.classList.remove('selected'));
            accountDiv.classList.add('selected');

            // Store the selected element in a global variable
            selectedElement = account.username;

            // Log the account number and the current time
            const accountNumber = accountDiv.dataset.accountNumber;
            const currentTime = new Date().toLocaleString();
            console.log(`Selected Account Number: ${selectedElement}, Time: ${currentTime}`);
        });

        const userHeader = document.createElement('h3');
        userHeader.textContent = `${account.username}`;
        accountDiv.appendChild(userHeader);

        // Increment healthy or unhealthy count
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

// Track the currently selected element (account or username box)
let selectedElement = null;

function sleep(milliseconds) {
    return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

document.addEventListener('DOMContentLoaded', fetchData);

// Add an event listener to the username input box
document.getElementById('username').addEventListener('click', () => {
    selectedElement = {
        type: 'username',
        value: document.getElementById('username').value
    };
    console.log('Username box selected');
});

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function register() {
    var username = document.getElementById('username').value;
    var password = document.getElementById('password').value;
    var code = document.getElementById('code').value;

    var formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    formData.append('code', code);

    fetch('/submit_register/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        alert(data.message);
    })
    .catch(error => {
        console.error('There was a problem with your fetch operation:', error);
        alert('There was an error processing your registration. Please check your email and try again.');
    });
}

function testFunction() {
    const newsAccountNumber = document.getElementById('news-account-number').value;
    const newsAccountHours = document.getElementById('news-account-minutes').value;
    const datetime = document.getElementById('news-datetime').value.replace("T"," ") + ":00+03:30";
    const country = document.getElementById('news-name').value;


    if (selectedElement) {
            console.log(`News Account Number: ${newsAccountNumber}, Hours: ${newsAccountHours}.${selectedElement}----${datetime}----${country}`);
            const myHeaders = new Headers();
            myHeaders.append("Content-Type", "application/json");

            const raw = JSON.stringify({
              "country": country,
              "user": selectedElement,
              "gap": parseInt(newsAccountHours),
              "news_count": parseInt(newsAccountNumber),
              "execution_time": datetime
            });

            const requestOptions = {
              method: "POST",
              headers: myHeaders,
              body: raw,
              redirect: "follow"
            };

            fetch("/save_schedule/", requestOptions)
              .then((response) => response.text())
              .then((result) => console.log(result))
              .catch((error) => console.error(error));





    }
    else {
        console.log('No account or username selected');
    }
}

// Event listener for the execute button
document.getElementById('execute-button').addEventListener('click', testFunction);

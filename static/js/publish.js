// Get the checkbox and caption input elements
const postCheckbox = document.getElementById('postCheckbox');
const captionInput = document.getElementById('caption');
const reelsCheckbox = document.getElementById('reelsCheckbox')
const aiCaption = document.getElementById('aiCaption')
const storyCheckbox = document.getElementById('storyCheckbox');
const captionHelper = document.getElementById('captionHelper');

// Function to enable/disable caption input based on checkbox status
function toggleCaption() {
  const onlyStory = storyCheckbox.checked && !postCheckbox.checked && !reelsCheckbox.checked;
  const aiCaptionChecked = aiCaption.checked;
  
  // Determine if caption should be enabled
  if (onlyStory) {
    captionInput.disabled = true;
    captionInput.classList.add('opacity-50', 'bg-gray-100');
    if (captionHelper) {
      captionHelper.textContent = "(Disabled - not needed for Story)";
    }
  } else {
    captionInput.disabled = false;
    captionInput.classList.remove('opacity-50', 'bg-gray-100');
    
    // Update helper text based on AI caption status
    if (captionHelper) {
      if (aiCaptionChecked) {
        captionHelper.textContent = "(Enter keywords for AI to generate caption)";
        captionInput.placeholder = "Enter keywords like: beach, sunset, vacation, friends";
      } else {
        captionHelper.textContent = "(Enter your caption text)";
        captionInput.placeholder = "Enter your caption here...";
      }
    }
  }
  
  // Visually indicate which options are selected
  [postCheckbox, reelsCheckbox, storyCheckbox, aiCaption].forEach(checkbox => {
    const label = checkbox.nextElementSibling;
    if (checkbox.checked) {
      label.classList.add('font-semibold', 'text-blue-700');
    } else {
      label.classList.remove('font-semibold', 'text-blue-700');
    }
  });
}

// Add event listeners to all checkboxes to update the UI
postCheckbox.addEventListener('change', toggleCaption);
reelsCheckbox.addEventListener('change', toggleCaption);
storyCheckbox.addEventListener('change', toggleCaption);
aiCaption.addEventListener('change', toggleCaption);

// Call the function initially to set the initial state
toggleCaption();


// Get the checkbox and caption input elements
const preCreatedCheckbox = document.getElementById('preCreatedCheckBox');
const preCreatedInput = document.getElementById('pre-created-photo');
const preCreatedCoverInput = document.getElementById('pre-created-cover');
const coverImageCheckbox = document.getElementById('coverImageCheckbox');
const stockImageFinderBtn = document.getElementById('aiImageFinderBtn');

// Updated selector to specifically exclude the publish button by using an attribute selector
const elementsToDisable = document.querySelectorAll('input[type="file"]:not(#pre-created-photo, #pre-created-cover), button:not([onclick="publishImage()"]):not(#selectDeselect):not(#publishPosts)');

// Function to enable/disable caption input based on checkbox status
function togglePreCreated() {
  const preCreatedSection = document.querySelector('.pre-created-section');
  const removeBtn = document.getElementById('removePreviewBtn');
  
  if (preCreatedCheckbox.checked) {
      preCreatedInput.disabled = false;
      
      // Enable cover image input only if the cover checkbox is checked
      if (coverImageCheckbox && coverImageCheckbox.checked) {
          preCreatedCoverInput.disabled = false;
      } else if (preCreatedCoverInput) {
          preCreatedCoverInput.disabled = true;
      }
      
      // Disable elements except for essential ones
      elementsToDisable.forEach(el => {
          // Skip the remove button to ensure it stays enabled
          if (el !== removeBtn) {
              el.disabled = true;
              el.classList.add('opacity-50', 'cursor-not-allowed');
          }
      });
      
      // Handle Stock Image Finder button specifically
      if (stockImageFinderBtn) {
          stockImageFinderBtn.disabled = true;
          stockImageFinderBtn.classList.add('opacity-50', 'cursor-not-allowed');
          stockImageFinderBtn.title = "Disabled while using pre-created content";
          
          // Add a special style to make it clear this button is disabled
          stockImageFinderBtn.classList.remove('btn-primary');
          stockImageFinderBtn.classList.add('btn-secondary');
      }
      
      // Explicitly ensure the publish button is enabled
      const publishButton = document.querySelector('button[onclick="publishImage()"]');
      if (publishButton) {
          publishButton.disabled = false;
          publishButton.classList.remove('opacity-50', 'cursor-not-allowed');
      }
      
      // Explicitly ensure the remove button stays enabled if content is in the preview
      if (removeBtn && document.getElementById('imagePreviewContainer').innerHTML.trim() !== '') {
          removeBtn.disabled = false;
          removeBtn.classList.remove('hidden', 'opacity-50', 'cursor-not-allowed');
      }
      
      // Add visual indication that pre-created mode is active
      if (preCreatedSection) {
          preCreatedSection.classList.add('border-2', 'border-green-500', 'p-3', 'rounded-md');
          
          // Add message indicating mode is active if it doesn't exist
          if (!document.getElementById('preCreatedActiveMsg')) {
              const activeMsg = document.createElement('div');
              activeMsg.id = 'preCreatedActiveMsg';
              activeMsg.className = 'bg-green-100 text-green-800 text-xs p-2 mb-3 rounded';
              activeMsg.innerHTML = '<i class="fas fa-check-circle mr-1"></i> Pre-created content mode active';
              preCreatedSection.prepend(activeMsg);
          }
      }
      
  } else {
      preCreatedInput.disabled = true;
      if (preCreatedCoverInput) preCreatedCoverInput.disabled = true;
      elementsToDisable.forEach(el => {
          // Skip the remove button to ensure its state is managed separately
          if (el !== removeBtn) {
              el.disabled = false;
              el.classList.remove('opacity-50', 'cursor-not-allowed');
          }
      });
      
      // Restore Stock Image Finder button
      if (stockImageFinderBtn) {
          stockImageFinderBtn.disabled = false;
          stockImageFinderBtn.classList.remove('opacity-50', 'cursor-not-allowed', 'btn-secondary');
          stockImageFinderBtn.classList.add('btn-primary');
          stockImageFinderBtn.title = "";
      }
      
      // Remove visual indication that pre-created mode is active
      if (preCreatedSection) {
          preCreatedSection.classList.remove('border-2', 'border-green-500', 'p-3', 'rounded-md');
          
          // Remove the active message if it exists
          const activeMsg = document.getElementById('preCreatedActiveMsg');
          if (activeMsg) {
              activeMsg.remove();
          }
      }
  }
  
  // Update remove button visibility based on content in preview container,
  // regardless of pre-created checkbox state
  checkAndUpdateRemoveButton();
}

// Toggle cover image input based on cover checkbox
if (coverImageCheckbox) {
    coverImageCheckbox.addEventListener('change', function() {
        if (preCreatedCheckbox.checked) {
            preCreatedCoverInput.disabled = !this.checked;
            if (!this.checked) {
                // Clear any selected cover file when unchecked
                preCreatedCoverInput.value = '';
            }
        }
    });
}

// Add event listener to checkbox to toggle caption input
preCreatedCheckbox.addEventListener('change', function() {
    togglePreCreated();
    // Ensure the remove button state is properly updated
    checkAndUpdateRemoveButton();
});

// Function to remove selected content from preview
function removePreviewContent() {
    // Clear the preview container
    const imagePreviewContainer = document.getElementById('imagePreviewContainer');
    if (imagePreviewContainer) {
        imagePreviewContainer.innerHTML = '';
    }
    
    // Update the remove button state
    checkAndUpdateRemoveButton();
    
    // Reset the global selected URL
    FinalselectedImageUrl = null;
    selectedImageUrl = "";
    
    // Reset pre-created file inputs if they have values
    const preCreatedInput = document.getElementById('pre-created-photo');
    if (preCreatedInput && preCreatedInput.value) {
        preCreatedInput.value = '';
    }
    
    const preCreatedCoverInput = document.getElementById('pre-created-cover');
    if (preCreatedCoverInput && preCreatedCoverInput.value) {
        preCreatedCoverInput.value = '';
    }
    
    console.log('Content removed from preview');
}

// Event listener for file selection to show preview
preCreatedInput.addEventListener('change', function() {
    const file = this.files[0];
    if (file) {
        const imagePreviewContainer = document.getElementById('imagePreviewContainer');
        imagePreviewContainer.innerHTML = ''; // Clear previous image

        // Create a preview image/video based on file type
        if (file.type.startsWith('image/')) {
            // Handle image files
            const imgPreview = document.createElement('img');
            imgPreview.src = URL.createObjectURL(file);
            imgPreview.style.width = '100%';
            imgPreview.style.height = 'auto';
            imgPreview.onload = function() {
                URL.revokeObjectURL(imgPreview.src); // Free memory
            };
            imagePreviewContainer.appendChild(imgPreview);
            
            // Set the global FinalselectedImageUrl to the file object
            FinalselectedImageUrl = file.name;
            console.log('Selected pre-created image:', file.name);
        } else if (file.type.startsWith('video/')) {
            // Handle video files
            const videoPreview = document.createElement('video');
            videoPreview.src = URL.createObjectURL(file);
            videoPreview.controls = true;
            videoPreview.style.width = '100%';
            videoPreview.style.height = 'auto';
            videoPreview.onloadedmetadata = function() {
                URL.revokeObjectURL(videoPreview.src); // Free memory
            };
            imagePreviewContainer.appendChild(videoPreview);
            
            // Set the global FinalselectedImageUrl to the file object
            FinalselectedImageUrl = file.name;
            console.log('Selected pre-created video:', file.name);
        }
        
        // Update the remove button visibility
        checkAndUpdateRemoveButton();
    }
});

// Event listener for cover image selection to show a small preview
if (preCreatedCoverInput) {
    preCreatedCoverInput.addEventListener('change', function() {
        const file = this.files[0];
        if (file && file.type.startsWith('image/')) {
            // Handle image files
            console.log('Selected cover image:', file.name);
            
            // Create a small preview if desired
            // Since this is just a cover image, we could add a small thumbnail
            // to the imagePreviewContainer or another container
        }
    });
}

// Call the function initially to set the initial state
togglePreCreated();

// Function to open Stock Image Finder modal
function openAiImageFinder() {
    document.getElementById('aiImageFinderModal').style.display = "flex";
}

// Function to close Stock Image Finder modal
function closeAiImageFinder() {
    document.getElementById('aiImageFinderModal').style.display = "none";
}

function searchAiImages() {
    var key_words = document.getElementById('aiImageSearchInput').value;
    var apiUrl = "/find_image/" + key_words.replace(' ', "+");
    var spinner = document.querySelector('.spinner-border.centerSpinner')
    spinner.style.display = 'flex'

    fetch(apiUrl, {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Handle the response data here, such as displaying the images on the page
            var imageContainer = document.getElementById('findimageContainer');
            imageContainer.innerHTML = ""; // Clear previous images
            data.image_urls.forEach(url => {
                var img = document.createElement('img');
                img.src = url;
                img.style.width = "20%"; // Set width as per your requirement
                img.style.height = "20%"; // Maintain aspect ratio
                img.style.padding = "5px";
                
                spinner.style.display = 'none'
                // Add event listener for image selection
                img.addEventListener('click', function() {
                    // Remove selection from previously selected image
                    var previouslySelected = document.querySelector('.selected');
                    if (previouslySelected) {
                        previouslySelected.classList.remove('selected');
                    }

                    // Select the clicked image
                    img.classList.add('selected');
                    selectedImageUrl = img.src;
                });

                imageContainer.appendChild(img);
            });
        })
        .catch(error => {
            // Handle any errors that occur during the fetch request
            alert("Failed to search for AI images. Error: " + error.message);
        });
}
var selectedImageUrl = "";

function selectImage() {
    // Check if an image is selected
    if (selectedImageUrl) {
        // Display the selected image in the preview container
        var imagePreviewContainer = document.getElementById('imagePreviewContainer');
        imagePreviewContainer.innerHTML = ""; // Clear previous image
        var selectedImage = document.createElement('img');
        selectedImage.src = selectedImageUrl;
        selectedImage.style.width = "100%";
        selectedImage.style.height = "auto";
        imagePreviewContainer.appendChild(selectedImage);
        document.getElementById('aiImageFinderModal').style.display = "none";

        // Update the remove button state
        checkAndUpdateRemoveButton();

        var imagePreviewContainerDownload = document.getElementById('imagePreviewContainer');
        var imgElement = imagePreviewContainerDownload.querySelector('img');
        if (imgElement) {
            FinalselectedImageUrl = imgElement.src;
            console.log('Selected Image URL:', FinalselectedImageUrl);
    
            // You can now use FinalselectedImageUrl wherever needed in your code
        } else {
            console.log('No image found in the container.');
        }
    } else {
        alert("Please select an image first.");
    }
}

// Function to show uploaded image in poreview 
// document.addEventListener('DOMContentLoaded', (event) => {
//     // Find the image element inside the container
//     const imagePreviewContainer = document.getElementById('imagePreviewContainer');
//     const imgElement = imagePreviewContainer.querySelector('img');

//     // Check if the image element exists and retrieve the src attribute
//     if (imgElement) {
//         const FinalselectedImageUrl = imgElement.src;
//         console.log('Selected Image URL:', FinalselectedImageUrl);

//         // You can now use FinalselectedImageUrl wherever needed in your code
//     } else {
//         console.log('No image found in the container.');
//     }
// });

function sendSelectedImage() {
    if (selectedImageUrl !== "") {
        // Create a FormData object
        var formData = new FormData();
        var csrftoken = getCookie('csrftoken');
        // Get the text value
        var text = document.getElementById('text').value;
        var image_name = document.getElementById('aiImageSearchInput').value;

        var spinnerProcess = document.querySelector('.spinner-grow')

        spinnerProcess.style.display = 'flex'
        // Create a blob from the selected image URL
        fetch(selectedImageUrl)
            .then(response => response.blob())
            .then(blob => {
                // Create a new File object with the blob and specify the name and extension
                const fileName = image_name + ".jpg"; // Change the file name and extension as needed
                const file = new File([blob], fileName, { type: blob.type });

                // Append the file to the FormData object
                formData.append('photo', file);
                formData.append('text', text);

                // Make a POST request to the desired URL with the FormData as the body
                fetch('/upload_photo/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrftoken
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
                    // Display response body in the label
                    // document.getElementById('responseLabel').innerText = JSON.stringify(data);

                    var imageContainer = document.getElementById('imageContainer');
                    // Clear previous images
                    imageContainer.innerHTML = '';

                    // Display images

                    const arr = Array.from(data.message);

                    // Loop through the image URLs and create image elements
                    arr.forEach(url => {
                        var img = createImage(url);
                        imageContainer.appendChild(img);
                    });
                    spinnerProcess.style.display = 'none'
                    //return data.text();
                })

            })
            .catch(error => {
                // Handle any errors that occur while fetching the image blob
                alert("Failed to fetch image blob. Error: " + error.message);
            });
    } else {
        alert("Please select an image first.");
    }
}

function applyBold() {
    var textArea = document.getElementById("text");
    var selectedText = textArea.value.substring(textArea.selectionStart, textArea.selectionEnd);
    var textBeforeSelection = textArea.value.substring(0, textArea.selectionStart);
    var textAfterSelection = textArea.value.substring(textArea.selectionEnd);

    if (selectedText.length > 0) {
        // Wrap selected text with bold tags
        textArea.value = textBeforeSelection + "<b>" + selectedText + "</b>" + textAfterSelection;
    } else {
        // If no text is selected, do nothing
        return;
    }
}

function changeFont() {
    var font = document.getElementById("fontSelector").value;
    document.getElementById("text").style.fontFamily = font;
}
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function createImage(url) {
    var img = document.createElement('img');
    img.src = "/image/" + url; // Add base URL
    img.className = "image-style"

    // Add click event listener to select the image
    img.addEventListener('click', function() {
        // Remove any previously selected image border
        var images = document.querySelectorAll('img');
        images.forEach(function(img) {
            img.classList.remove('selected-image');
        });

        // Add border to the selected image
        img.classList.add('selected-image');
        FinalselectedImageUrl = url; // Store the selected image URL
    });

    return img;
}

var FinalselectedImageUrl = null; // Variable to store the selected image URL

function uploadImage(mode) {

    var csrftoken = getCookie('csrftoken');

    // Get the selected photo
    var photo = document.getElementById('photo').files[0];
    // Check if a photo was selected
    if (!photo) {
        alert("Please select an image.");
        return;
    }


    // Get the text value
    var text = document.getElementById('text').value;

    // Construct the request body
    var formData = new FormData();
    formData.append('photo', photo);
    formData.append('text', text);

    // Make a POST request using Fetch API
    fetch('/upload_photo/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken
        },
        body: formData
    })
    .then(response => {
        // Check if response status is ok
        if (response.ok) {
            // Change label color to green
            document.getElementById('responseLabel').style.color = 'green';
            return response.json(); // Return the JSON data for further processing
        } else {
            // Change label color to red
            document.getElementById('responseLabel').style.color = 'red';
            throw new Error('Failed to upload image');
        }
    })
    .then(data => {
        // Display response body in the label
        document.getElementById('responseLabel').innerText = JSON.stringify(data);

        var imageContainer = document.getElementById('imageContainer');
        imageContainer.innerHTML = '';

        const arr = Array.from(data.message);

        // Loop through the image URLs and create image elements
        arr.forEach(url => {
            var img = createImage(url);
            imageContainer.appendChild(img);
        });
    })
    .catch(error => {
        // Handle error
        console.error('There was a problem with your fetch operation:', error);
    });
}

function publishPosts(selectedUsernames) {
    console.log(selectedUsernames);

    var inputElement = document.getElementById("scrollInput");
    var time_gap = inputElement.value;

    const form = document.getElementById('preferenceForm');
    const checkboxes = form.elements['preference'];
    const captionInput = document.getElementById('caption');
    const captionText = captionInput.value;
    const checkedItems = [];

    for (let i = 0; i < checkboxes.length; i++) {
        if (checkboxes[i].checked) {
            checkedItems.push(checkboxes[i].value);
        }
    }
    console.log(FinalselectedImageUrl);

    let imageUrl = FinalselectedImageUrl;
    if (imageUrl) {
        // Create a new FormData object
        var formData = new FormData();
        formData.append('image_url', imageUrl);
        formData.append('types', JSON.stringify(checkedItems)); // Convert array to JSON string
        formData.append('caption', captionText);
        formData.append('accounts', JSON.stringify(selectedUsernames)); // Convert array to JSON string
        formData.append('time_gap', time_gap);
        // formData.append('cover', cover);

        console.log('FormData Entries:');
        for (var pair of formData.entries()) {
            console.log(pair[0] + ': ' + pair[1]);
        }

        // Send the FormData object using fetch
        fetch('/publish_story/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: formData
        })
        .then(response => {
            if (response.ok) {
                alert("Image published successfully!");
            } else {
                throw new Error('Failed to publish image');
            }
        })
        .catch(error => {
            console.error('There was a problem with publishing the image:', error);
        });
    } else {
        alert("Please select an image to publish.");
    }
}


function publishPreCreated(selectedUsernames){

    // Gettign Time gap
    var inputElement = document.getElementById("scrollInput");
    var time_gap = inputElement.value;

    const form = document.getElementById('preferenceForm');
    const checkboxes = form.elements['preference'];
    const captionInput = document.getElementById('caption');
    const captionText = captionInput.value;
    const accounts = selectedUsernames
    const checkedItems = [];
    for (let i = 0; i < checkboxes.length; i++) {
        if (checkboxes[i].checked) {
            checkedItems.push(checkboxes[i].value);
            }
    }
    // Get the selected photo
    var photo = document.getElementById('pre-created-photo').files[0];
    console.log(photo)
    // Check if a photo was selected
    if (!photo) {
        alert("Please select an image.");
        return;
    }

    // Get the selected video
    var cover = document.getElementById('pre-created-cover').files[0];
    console.log(cover)
    // Check if a photo was selected
    // if (!cover) {
    //     alert("Please select an image.");
    //     return;
    // }
    var formData = new FormData();
    formData.append('photo', photo);
    formData.append('caption', captionText);
    formData.append('types', JSON.stringify(checkedItems));
    formData.append('accounts', JSON.stringify(accounts));
    formData.append('time_gap', time_gap);
    formData.append('cover', cover);

    console.log('FormData Entries:');
    for (var pair of formData.entries()) {
        console.log(pair[0]+ ': ' + pair[1]);
    }

    fetch('/publish_story/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
        })
        .then(response => {
            if (response.ok) {
                alert("Image published successfully!");
            } else {
                throw new Error('Failed to publish image');
            }
        })
        .catch(error => {
            console.error('There was a problem with publishing the image:', error);
        });


}

// Function to show accounts before publishing
function initializeHTML(accountData) {
    // Get the modal content container
    const modalContent = document.getElementById('data-container');
    modalContent.innerHTML = ''; // Clear any previous content

    accountData.forEach(account => {

        // Skip accounts with 'unhealthy' status
        if (account.status.toLowerCase() === 'unhealthy') {
            return;
        }
        // Create a div for each account
        const accountDiv = document.createElement('div');
        accountDiv.classList.add('data-container');

        // Define the details to be displayed
        const details = ['Username', 'Timestamp', 'AntiBan', 'Status', 'Message'];
        
        // Loop through each detail and create corresponding elements
        details.forEach(detail => {
            const p = document.createElement('p');
            const detailKey = detail.toLowerCase();
            
            if (detail === 'Message') {
                p.textContent = `${detail}: ${account[detailKey] || 'OK!'}`;
            } else if (detail === 'AntiBan') {
                p.textContent = `${detail}: ${account[detailKey] === undefined ? 'soon!' : account[detailKey]}`;
            } else {
                p.textContent = `${detail}: ${account[detailKey]}`;
            }
            
            accountDiv.appendChild(p);
        });

        // Create the div containing the checkbox and label
        const divCheckbox = document.createElement('div');
        divCheckbox.classList.add('checkbox-wrapper-17');
            
        // Create the checkbox input
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = 'switch-' + account.username; // Unique ID based on username
        checkbox.value = account.username; // Assuming each account has a unique username
            
        // Create the label for the checkbox
        const label = document.createElement('label');
        label.htmlFor = 'switch-' + account.username;
            
        // Append the checkbox and label to the div
        divCheckbox.appendChild(checkbox);
        divCheckbox.appendChild(label);
            
        // Append the div to the accountDiv
        accountDiv.appendChild(divCheckbox);

        // Add a click event listener to the account div
        accountDiv.addEventListener('click', () => {
            checkbox.checked = !checkbox.checked;
        });
        
        // Prevent event propagation to avoid toggling when clicking on the checkbox or label directly
        checkbox.addEventListener('click', (event) => {
            event.stopPropagation();
        });
        label.addEventListener('click', (event) => {
            event.stopPropagation();
        });
            
        // Append the account div to the modal content
        modalContent.appendChild(accountDiv);
    });
}

// Fetching data
async function fetchData() {
  
    // Define headers for the fetch request
    const headers = {
      'X-CSRFToken': getCookie('csrftoken'),
  };
  
    // Make the fetch request with the appropriate headers
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
  }
  }

// Showing accounts list before publishing
async function publishImage() {
    // Fetch account data
    var spinnerBg = document.querySelector('.beforePublishSpinner')
    var spinner = document.querySelector('.publishSpinner')

    spinnerBg.style.display = 'flex'
    spinner.style.display = 'flex'
    await fetchData();

    // Show the publish modal
    spinnerBg.style.display = 'none'
    spinner.style.display = 'none'
    const modal = document.getElementById('publishModal');
    modal.style.display = 'flex';
}

// Function to close the modal
function closeModal() {
    const modal = document.getElementById('publishModal');
    modal.style.display = 'none';
}

// Function to confirm the publish action
function confirmPublish() {
    // Get selected accounts
    const accounts_checkboxes = document.querySelectorAll('#data-container input[type="checkbox"]:checked');
    console.log(accounts_checkboxes)
    var selectedUsernames = [];
    var inputElement = document.getElementById("scrollInput");
    var time_gap = inputElement.value;
    if (accounts_checkboxes.length > 0) {
        selectedUsernames = Array.from(accounts_checkboxes).map(accounts_checkboxes => accounts_checkboxes.value);
        console.log('Selected clients\' usernames:', selectedUsernames.join(', '));
    } 
    else {
        console.log('No clients selected.');
    }

    // Check if the preCreatedCheckBox is selected
    const preCreatedCheckBox = document.getElementById('preCreatedCheckBox');
    if (preCreatedCheckBox && preCreatedCheckBox.checked) {
        publishPreCreated(selectedUsernames);
    } else {
        publishPosts(selectedUsernames);
    }

    // Close the modal
    closeModal();
}

// selecting and deselecting checkboxes in publish modal
function selectDeselect() {
    const checkboxes = document.querySelectorAll('.data-container .checkbox-wrapper-17 input[type="checkbox"]');
    const allChecked = Array.from(checkboxes).every(checkbox => checkbox.checked);
    const button = document.querySelector('.select-deselect-button');

    checkboxes.forEach(checkbox => {
        checkbox.checked = !allChecked;
    });

    button.innerHTML = allChecked ? '<i class="fas fa-check-square"></i> Select All' : '<i class="fas fa-check-square"></i> Deselect All';

    console.log("Select/Deselect All triggered");
}

// Initialize interface elements on page load
document.addEventListener('DOMContentLoaded', function() {
    // Check if there's content in the preview container and show/hide remove button accordingly
    const imagePreviewContainer = document.getElementById('imagePreviewContainer');
    const removeBtn = document.getElementById('removePreviewBtn');
    
    if (imagePreviewContainer && removeBtn) {
        // If the container has content, show the remove button
        if (imagePreviewContainer.innerHTML.trim() !== '') {
            removeBtn.classList.remove('hidden');
        } else {
            removeBtn.classList.add('hidden');
        }
    }
    
    // Call initial toggles to set proper state
    toggleCaption();
    togglePreCreated();
});

// Function to check if there's content in the preview and update remove button accordingly
function checkAndUpdateRemoveButton() {
    const imagePreviewContainer = document.getElementById('imagePreviewContainer');
    const removeBtn = document.getElementById('removePreviewBtn');
    
    if (imagePreviewContainer && removeBtn) {
        if (imagePreviewContainer.innerHTML.trim() !== '') {
            // There's content in the preview, show the remove button
            removeBtn.classList.remove('hidden');
            removeBtn.disabled = false;
        } else {
            // No content in the preview, hide the remove button
            removeBtn.classList.add('hidden');
        }
    }
}
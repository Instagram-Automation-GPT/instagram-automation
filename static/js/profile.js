
document.addEventListener("DOMContentLoaded", () => {
    const accounts = [
        { username: "johnmilner367", instagramUrl: "https://www.instagram.com/johnmilner367" },
    ];

    const dataContainer = document.querySelector(".data-container");

    accounts.forEach(async (account) => {
        const profileDiv = document.createElement("div");
        profileDiv.className = "d-flex align-items-center mb-4";

        const imageElement = document.createElement("img");
        imageElement.className = "profile-picture";

        try {
            const imageUrl = await fetchInstagramProfileImage(account.instagramUrl);
            imageElement.src = imageUrl;
        } catch (error) {
            console.error(`Error fetching image for ${account.username}:`, error);
            imageElement.src = "/images/default-avatar.png"; 
        }

        const usernameElement = document.createElement("span");
        usernameElement.className = "ml-2 font-medium";
        usernameElement.textContent = account.username;

        profileDiv.appendChild(imageElement);
        profileDiv.appendChild(usernameElement);

        dataContainer.appendChild(profileDiv);
    });
});

async function fetchInstagramProfileImage(instagramUrl) {
    const apiUrl = "https://indownloader.app/request";

    const formData = new FormData();
    formData.append("link", instagramUrl);
    formData.append("downloader", "avatar");

    const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
            "Cookie": `PHPSESSID=${token}`,
        },
        body: formData,
    });

    if (response.ok) {
        const data = await response.json();
        return data.avatar; 
    } else {
        throw new Error("Failed to fetch profile image");
    }
}


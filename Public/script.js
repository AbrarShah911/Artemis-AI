document.getElementById('registerForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    const response = await fetch('http://127.0.0.1:5000/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password })
    });

    const result = await response.json();
    
    document.getElementById('responseMessage').innerText = result.message || result.error;
});


document.getElementById('loginForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    const response = await fetch('http://127.0.0.1:5000/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    });

    const result = await response.json();
    
    if (response.ok) {
        document.getElementById('loginResponse').innerText = "Login Successful! Welcome, " + result.username;
    } else {
        document.getElementById('loginResponse').innerText = result.error;
    }
});

document.getElementById('deleteForm').addEventListener('submit', async function(event) {
    event.preventDefault();

    const email = document.getElementById('deleteEmail').value;

    const response = await fetch('http://127.0.0.1:5000/delete', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
    });

    const result = await response.json();
    document.getElementById('deleteResponse').innerText = result.message || result.error;
});

async function updateUser(field) {
    const email = prompt("Enter your email (for verification):");
    if (!email) return alert("Email is required!");

    let newValue = prompt(`Enter new ${field}:`);
    if (!newValue) return alert(`${field} is required!`);

    const response = await fetch("http://127.0.0.1:5000/update", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, field, newValue })
    });

    const result = await response.json();
    alert(result.message || result.error);
}


document.getElementById('uploadForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    
    const fileInput = document.getElementById('imageFile');
    const files = fileInput.files;
    const userEmail = document.getElementById('userEmail').value;

    if (files.length === 0 || !userEmail) {
        alert("Please select at least one image and enter your email!");
        return;
    }

    const formData = new FormData();
    formData.append("email", userEmail);

    for (let i = 0; i < files.length; i++) {
        formData.append("images", files[i]);  // Append multiple images
    }

    const response = await fetch("http://127.0.0.1:5000/upload", {
        method: "POST",
        body: formData
    });

    const result = await response.json();
    
    if (response.ok) {
        document.getElementById('uploadMessage').innerText = result.message;
        displayImages(result.uploaded_images, 'uploadedImagesContainer');
    } else {
        document.getElementById('uploadMessage').innerText = result.error;
    }
});

document.getElementById('downloadForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    
    const userEmail = document.getElementById('downloadEmail').value;
    const imageUrl = document.getElementById('downloadUrl').value;

    if (!userEmail || !imageUrl) {
        alert("Please enter an email and image URL!");
        return;
    }

    const response = await fetch("http://127.0.0.1:5000/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: userEmail, image_url: imageUrl })
    });

    const result = await response.json();
    
    if (response.ok) {
        document.getElementById('downloadMessage').innerText = result.message;
        displayImages(result.downloaded_images, 'downloadedImagesContainer');
    } else {
        document.getElementById('downloadMessage').innerText = result.error;
    }
});

function displayImages(imageUrls, containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";  // Clear existing images

    imageUrls.forEach(url => {
        const img = document.createElement("img");
        img.src = url;
        img.style = "max-width: 150px; margin: 5px;";
        container.appendChild(img);
    });
}
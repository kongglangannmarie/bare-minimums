const API_URL = "http://127.0.0.1:8000";

function showAlert(message, type) {
  const alertDiv = document.getElementById("alert");
  alertDiv.textContent = message;
  alertDiv.className = `alert show ${type}`;
  
  // Auto-hide after 5 seconds
  setTimeout(() => {
    alertDiv.classList.remove("show");
  }, 5000);
}

async function handleSignup(event) {
  event.preventDefault();

  const email = document.getElementById("email").value.trim();
  const businessName = document.getElementById("business_name").value.trim();
  const password = document.getElementById("password").value;
  const confirmPassword = document.getElementById("confirm_password").value;
  const signupBtn = document.getElementById("signup-btn");

  // Validate that passwords match
  if (password !== confirmPassword) {
    showAlert("Passwords do not match!", "error");
    return;
  }

  // Validate password length
  if (password.length < 8) {
    showAlert("Password must be at least 8 characters long!", "error");
    return;
  }

  // Disable button during request
  signupBtn.disabled = true;
  signupBtn.textContent = "Creating account...";

  try {
    const response = await fetch(`${API_URL}/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: email,
        business_name: businessName,
        password: password,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      // Handle specific error messages from backend
      if (response.status === 400 && data.detail.includes("Email already registered")) {
        showAlert("This email is already registered. Please login or use a different email.", "error");
      } else {
        showAlert(data.detail || "Sign up failed. Please try again.", "error");
      }
      return;
    }

    // Success
    showAlert("Account created successfully! Redirecting to login...", "success");
    
    // Redirect to login after 2 seconds
    setTimeout(() => {
      window.location.href = "index.html";
    }, 2000);

  } catch (error) {
    console.error("Sign up error:", error);
    showAlert("Network error. Please check your connection and try again.", "error");
  } finally {
    signupBtn.disabled = false;
    signupBtn.textContent = "Sign Up";
  }
}

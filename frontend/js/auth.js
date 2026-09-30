/**
 * ShopNow - Online Shopping System
 * Customer Authentication & Profile JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    initRegisterForm();
    initLoginForm();
    initProfilePage();
});

/**
 * Handle Customer Registration Form Validation & Submission
 */
function initRegisterForm() {
    const registerForm = document.getElementById('registerForm');
    if (!registerForm) return;

    registerForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        // Form Fields
        const fullName = document.getElementById('fullName').value.trim();
        const email = document.getElementById('email').value.trim();
        const phone = document.getElementById('phone').value.trim();
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const address = document.getElementById('address').value.trim();

        // Clear previous error messages
        clearErrors();

        let isValid = true;

        // Validation Checks
        if (!fullName) {
            showFieldError('fullNameError', 'Full name is required.');
            isValid = false;
        }

        if (!email || !validateEmail(email)) {
            showFieldError('emailError', 'Please enter a valid email address.');
            isValid = false;
        }

        if (!phone || phone.length < 7) {
            showFieldError('phoneError', 'Please enter a valid phone number.');
            isValid = false;
        }

        if (!password || password.length < 6) {
            showFieldError('passwordError', 'Password must be at least 6 characters.');
            isValid = false;
        }

        if (password !== confirmPassword) {
            showFieldError('confirmPasswordError', 'Passwords do not match.');
            isValid = false;
        }

        if (!address) {
            showFieldError('addressError', 'Shipping address is required.');
            isValid = false;
        }

        if (!isValid) return;

        // Check if email already registered in mock storage
        const registeredUsers = JSON.parse(localStorage.getItem('shopnow_registered_users')) || [];
        const existingUser = registeredUsers.find(u => u.email.toLowerCase() === email.toLowerCase());

        if (existingUser) {
            showAlert('authAlert', 'An account with this email address already exists. Please login.', 'error');
            return;
        }

        // Create new user object
        const newUser = {
            user_id: 'USR-' + Math.floor(100 + Math.random() * 900),
            name: fullName,
            email: email,
            phone: phone,
            password: password, // Note: Python backend will hash password with SHA-256
            address: address,
            created_at: new Date().toISOString().replace('T', ' ').substring(0, 19)
        };

        // Save to temporary registered users array
        registeredUsers.push(newUser);
        localStorage.setItem('shopnow_registered_users', JSON.stringify(registeredUsers));

        showAlert('authAlert', 'Registration successful! Redirecting to login...', 'success');

        setTimeout(() => {
            window.location.href = 'login.html';
        }, 1500);
    });
}

/**
 * Handle Customer Login Form
 */
function initLoginForm() {
    const loginForm = document.getElementById('loginForm');
    if (!loginForm) return;

    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const email = document.getElementById('loginEmail').value.trim();
        const password = document.getElementById('loginPassword').value;

        clearErrors();

        if (!email || !validateEmail(email)) {
            showFieldError('emailError', 'Please enter a valid email address.');
            return;
        }

        if (!password) {
            showFieldError('passwordError', 'Password is required.');
            return;
        }

        // Check against mock registered users
        const registeredUsers = JSON.parse(localStorage.getItem('shopnow_registered_users')) || [];
        let user = registeredUsers.find(u => u.email.toLowerCase() === email.toLowerCase());

        // Demo Fallback User
        if (!user && email === 'john@example.com' && password === '123456') {
            user = {
                user_id: 'USR-101',
                name: 'John Doe',
                email: 'john@example.com',
                phone: '+1234567890',
                address: '123 University Campus St, Apt 4B, NY 10001'
            };
        }

        if (user && user.password && user.password !== password) {
            showAlert('authAlert', 'Invalid email or password. Please try again.', 'error');
            return;
        }

        if (!user) {
            // For testing demo before backend python server is started
            user = {
                user_id: 'USR-' + Math.floor(100 + Math.random() * 900),
                name: email.split('@')[0],
                email: email,
                phone: '+1 555-0199',
                address: '123 University Campus St'
            };
        }

        // Set session
        setCurrentUser(user);
        showAlert('authAlert', 'Login successful! Redirecting to homepage...', 'success');

        setTimeout(() => {
            window.location.href = 'index.html';
        }, 1000);
    });
}

/**
 * Pre-fill & Handle User Profile Updates
 */
function initProfilePage() {
    const profileForm = document.getElementById('profileForm');
    if (!profileForm) return;

    const user = getCurrentUser();
    if (!user) {
        window.location.href = 'login.html';
        return;
    }

    // Fill form elements
    document.getElementById('profileFullName').value = user.name || '';
    document.getElementById('profileEmail').value = user.email || '';
    document.getElementById('profilePhone').value = user.phone || '';
    document.getElementById('profileAddress').value = user.address || '';

    const sidebarName = document.getElementById('sidebarProfileName');
    const sidebarEmail = document.getElementById('sidebarProfileEmail');
    if (sidebarName) sidebarName.textContent = user.name;
    if (sidebarEmail) sidebarEmail.textContent = user.email;

    profileForm.addEventListener('submit', (e) => {
        e.preventDefault();

        const updatedName = document.getElementById('profileFullName').value.trim();
        const updatedPhone = document.getElementById('profilePhone').value.trim();
        const updatedAddress = document.getElementById('profileAddress').value.trim();

        if (!updatedName || !updatedPhone || !updatedAddress) {
            showAlert('profileAlert', 'Please fill in all required profile fields.', 'error');
            return;
        }

        user.name = updatedName;
        user.phone = updatedPhone;
        user.address = updatedAddress;

        setCurrentUser(user);
        showAlert('profileAlert', 'Profile updated successfully!', 'success');
    });

    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logoutUser);
    }
}

/**
 * Form Helper Utilities
 */
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function showFieldError(errorElementId, message) {
    const elem = document.getElementById(errorElementId);
    if (elem) {
        elem.textContent = message;
    }
}

function clearErrors() {
    document.querySelectorAll('.error-text').forEach(el => el.textContent = '');
    const alertBox = document.querySelector('.alert-message');
    if (alertBox) alertBox.classList.add('hidden');
}

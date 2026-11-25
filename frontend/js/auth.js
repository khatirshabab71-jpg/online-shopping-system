/**
 * ShopNow - Online Shopping System
 * Customer Authentication & Profile JavaScript
 * Connects directly to the Python backend API and MySQL database.
 * Phase 2: Strong password validation, email verification, and profile management.
 */

document.addEventListener('DOMContentLoaded', () => {
    initRegisterForm();
    initLoginForm();
    initProfilePage();
});

function validatePasswordRule(password) {
    if (password.length < 8) return "Password must be at least 8 characters.";
    if (!/[A-Z]/.test(password)) return "Password must contain at least one uppercase letter.";
    if (!/[a-z]/.test(password)) return "Password must contain at least one lowercase letter.";
    if (!/[0-9]/.test(password)) return "Password must contain at least one digit.";
    if (!/[!@#$%^&*(),.?":{}|<>_\-+=~`[\]\\/]/.test(password)) return "Password must contain at least one special character.";
    return "";
}

/**
 * Handle Customer Registration Form Submission
 */
function initRegisterForm() {
    const registerForm = document.getElementById('registerForm');
    if (!registerForm) return;

    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const fullName = document.getElementById('fullName').value.trim();
        const email = document.getElementById('email').value.trim();
        const phone = document.getElementById('phone').value.trim();
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const address = document.getElementById('address').value.trim();

        clearErrors();

        let isValid = true;

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

        const pwdErr = validatePasswordRule(password);
        if (pwdErr) {
            showFieldError('passwordError', pwdErr);
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

        const submitBtn = registerForm.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Creating Account...';
        }

        const res = await apiFetch('/register', 'POST', {
            fullName,
            email,
            phone,
            password,
            address
        });

        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create My Account';
        }

        if (res && res.success) {
            if (res.token) setAuthToken(res.token);
            if (res.user) setCurrentUser(res.user);
            showAlert('authAlert', res.message || 'Registration successful! Verification email sent.', 'success');
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1500);
        } else {
            showAlert('authAlert', res ? res.message : 'Registration failed. Please try again.', 'error');
        }
    });
}

/**
 * Handle Customer Login Form Submission
 */
function initLoginForm() {
    const loginForm = document.getElementById('loginForm');
    if (!loginForm) return;

    loginForm.addEventListener('submit', async (e) => {
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

        const submitBtn = loginForm.querySelector('button[type="submit"]') || document.getElementById('loginBtn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Logging in...';
        }

        const res = await apiFetch('/login', 'POST', { email, password });

        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Login to Account';
        }

        if (res && res.success) {
            setAuthToken(res.token);
            setCurrentUser(res.user);
            showAlert('authAlert', 'Login successful! Redirecting to storefront...', 'success');
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 800);
        } else {
            showAlert('authAlert', res ? res.message : 'Invalid email or password.', 'error');
        }
    });
}

/**
 * Handle Customer Profile Page (Fetching from MySQL and Updating)
 */
async function initProfilePage() {
    const profileForm = document.getElementById('profileForm');
    if (!profileForm) return;

    if (!getAuthToken()) {
        window.location.href = 'login.html';
        return;
    }

    // Fetch verified profile from Python backend
    const res = await apiFetch('/me');
    if (!res || !res.success || !res.user) {
        removeUserSession();
        window.location.href = 'login.html';
        return;
    }

    const user = res.user;
    setCurrentUser(user);

    // Populate form fields
    const nameInput = document.getElementById('profileFullName');
    const emailInput = document.getElementById('profileEmail');
    const phoneInput = document.getElementById('profilePhone');
    const addressInput = document.getElementById('profileAddress');

    if (nameInput) nameInput.value = user.name || '';
    if (emailInput) emailInput.value = user.email || '';
    if (phoneInput) phoneInput.value = user.phone || '';
    if (addressInput) addressInput.value = user.address || '';

    const sidebarName = document.getElementById('sidebarProfileName');
    const sidebarEmail = document.getElementById('sidebarProfileEmail');
    if (sidebarName) sidebarName.textContent = user.name || '';
    if (sidebarEmail) sidebarEmail.textContent = user.email || '';

    // Email verification status
    const verifyBadge = document.getElementById('emailVerifyStatusBadge');
    const resendBtn = document.getElementById('resendVerifyBtn');

    if (verifyBadge) {
        if (user.is_verified) {
            verifyBadge.textContent = '✓ Verified Customer Account';
            verifyBadge.style.backgroundColor = '#d1fae5';
            verifyBadge.style.color = '#065f46';
            if (resendBtn) resendBtn.classList.add('hidden');
        } else {
            verifyBadge.textContent = '⚠️ Unverified Email';
            verifyBadge.style.backgroundColor = '#fef3c7';
            verifyBadge.style.color = '#92400e';
            if (resendBtn) {
                resendBtn.classList.remove('hidden');
                resendBtn.onclick = async () => {
                    resendBtn.disabled = true;
                    resendBtn.textContent = 'Sending...';
                    const sendRes = await apiFetch('/auth/resend-verification', 'POST');
                    resendBtn.disabled = false;
                    resendBtn.textContent = 'Resend Verification Link';
                    if (sendRes && sendRes.success) {
                        showAlert('profileAlert', sendRes.message, 'success');
                    } else {
                        showAlert('profileAlert', sendRes ? sendRes.message : 'Failed to resend.', 'error');
                    }
                };
            }
        }
    }

    // Quick stats: orders count & wishlist count
    const ordersCountEl = document.getElementById('userTotalOrdersCount');
    const wishlistCountEl = document.getElementById('userWishlistCount');

    apiFetch('/orders').then(ordRes => {
        if (ordRes && ordRes.success && ordRes.orders && ordersCountEl) {
            ordersCountEl.textContent = ordRes.orders.length;
        }
    });

    apiFetch('/wishlist').then(wRes => {
        if (wRes && wRes.success && wRes.wishlist && wishlistCountEl) {
            wishlistCountEl.textContent = wRes.wishlist.total_count;
        }
    });

    profileForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const updatedName = nameInput ? nameInput.value.trim() : '';
        const updatedPhone = phoneInput ? phoneInput.value.trim() : '';
        const updatedAddress = addressInput ? addressInput.value.trim() : '';
        
        const currentPasswordInput = document.getElementById('profileCurrentPassword');
        const newPasswordInput = document.getElementById('profileNewPassword');
        const confirmPasswordInput = document.getElementById('profileConfirmPassword');

        const currentPassword = currentPasswordInput ? currentPasswordInput.value : '';
        const newPassword = newPasswordInput ? newPasswordInput.value : '';
        const confirmPassword = confirmPasswordInput ? confirmPasswordInput.value : '';

        if (!updatedName || !updatedPhone || !updatedAddress) {
            showAlert('profileAlert', 'Please fill in all required profile fields.', 'error');
            return;
        }

        if (newPassword) {
            if (!currentPassword) {
                showAlert('profileAlert', 'Current password is required to change your password.', 'error');
                return;
            }
            const pwdErr = validatePasswordRule(newPassword);
            if (pwdErr) {
                showAlert('profileAlert', pwdErr, 'error');
                return;
            }
            if (newPassword !== confirmPassword) {
                showAlert('profileAlert', 'New passwords do not match.', 'error');
                return;
            }
        }

        const updateBtn = document.getElementById('updateProfileBtn');
        if (updateBtn) {
            updateBtn.disabled = true;
            updateBtn.textContent = 'Saving Changes...';
        }

        const payload = {
            fullName: updatedName,
            phone: updatedPhone,
            address: updatedAddress
        };

        if (newPassword) {
            payload.currentPassword = currentPassword;
            payload.newPassword = newPassword;
        }

        const updateRes = await apiFetch('/profile/update', 'POST', payload);

        if (updateBtn) {
            updateBtn.disabled = false;
            updateBtn.textContent = 'Update Profile Settings';
        }

        if (updateRes && updateRes.success) {
            user.name = updatedName;
            user.phone = updatedPhone;
            user.address = updatedAddress;
            setCurrentUser(user);

            if (sidebarName) sidebarName.textContent = updatedName;
            if (currentPasswordInput) currentPasswordInput.value = '';
            if (newPasswordInput) newPasswordInput.value = '';
            if (confirmPasswordInput) confirmPasswordInput.value = '';

            showAlert('profileAlert', updateRes.message || 'Profile updated successfully!', 'success');
        } else {
            showAlert('profileAlert', updateRes ? updateRes.message : 'Failed to update profile.', 'error');
        }
    });

    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logoutUser);
    }
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function showFieldError(errorElementId, message) {
    const elem = document.getElementById(errorElementId);
    if (elem) elem.textContent = message;
}

function clearErrors() {
    document.querySelectorAll('.error-text').forEach(el => el.textContent = '');
    const alertBox = document.querySelector('.alert-message');
    if (alertBox) alertBox.classList.add('hidden');
}

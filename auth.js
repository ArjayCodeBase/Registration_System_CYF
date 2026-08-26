// auth.js

// ========================================
// LOGOUT
// ========================================
function logout(event) {

    if (event) {
        event.preventDefault();
    }

    // Mark user as logged out
    sessionStorage.setItem("loggedOut", "true");

    // Go to login page
    window.location.replace("login.html");
}


// ========================================
// PROTECTED PAGE CHECK
// ========================================
(function checkLogoutStatus() {

    const currentPage = window.location.pathname
        .split("/")
        .pop()
        .toLowerCase();

    // Login page is always allowed to load.
    // DO NOT reset loggedOut here.
    if (currentPage === "login.html") {
        return;
    }

    // Home page is always allowed.
    if (currentPage === "home.html") {
        return;
    }

    // If user logged out, prevent access
    // to protected pages.
    if (sessionStorage.getItem("loggedOut") === "true") {

        window.location.replace("home.html");

    }

})();
function logout() {
    window.location.href = "login.html";
}
function details() {
    const user = JSON.parse(localStorage.getItem("User"));
    document.getElementById("username").textContent = "Username: " + user.username;
    document.getElementById("user").style.display = "block";
}
function closeUser() {
    document.getElementById("user").style.display = "none"; 
}
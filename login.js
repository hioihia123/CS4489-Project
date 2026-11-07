const account = {
    username: "guest",
    password: "password"
};

localStorage.setItem("account", JSON.stringify(account));

const form = document.querySelector("form");

form.addEventListener("submit", function (event) {
    event.preventDefault();

    const username = document.querySelector("#username").value;
    const password = document.querySelector("#password").value;

    const storedAccount = JSON.parse(
        localStorage.getItem("account")
    );

    if (
        username === storedAccount.username &&
        password === storedAccount.password
    ) {

        localStorage.setItem("User", JSON.stringify(storedAccount));
        alert("Login successful!");
        window.location.href = "landingpage.html";

    } else {
        alert("Incorrect email or password.");
    }
});

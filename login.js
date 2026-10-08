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
        alert("Login successful!");

    } else {
        alert("Incorrect email or password.");
    }
});
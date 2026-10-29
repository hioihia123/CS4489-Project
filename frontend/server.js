// No external Node packages required. Serves the frontend files on Azure App Service.
const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");

const routes = {
  "/": "index.html",
  "/index.html": "index.html",
  "/login.css": "login.css",
  "/login.js": "login.js",

  // Dashboard pages
  "/dashboard.html": "dashboard.html",
  "/dashboard.js": "dashboard.js"
};
const mime = { ".html": "text/html", ".css": "text/css", ".js": "text/javascript" };

http.createServer((request, response) => {
  const { pathname } = new URL(request.url, "http://localhost");
  const filename = routes[pathname];
  if (!filename) {
    response.writeHead(404, { "Content-Type": "text/plain" });
    response.end("Not found");
    return;
  }

  const filePath = path.join(__dirname, filename);
  fs.readFile(filePath, (err, file) => {
    if (err) {
      response.writeHead(500, { "Content-Type": "text/plain" });
      response.end("Server error");
      return;
    }
    response.writeHead(200, {
      "Content-Type": `${mime[path.extname(filename)]}; charset=utf-8`,
      "X-Content-Type-Options": "nosniff",
      "Referrer-Policy": "no-referrer"
    });
    response.end(file);
  });
}).listen(process.env.PORT || 8080, "0.0.0.0");

from fastapi import FastAPI

app = FastAPI(
    title="CS4489 Vulnerable Backend",
    description="Intentionally vulnerable backend for cybersecurity demonstration.",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "CS4489 Vulnerable Backend is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

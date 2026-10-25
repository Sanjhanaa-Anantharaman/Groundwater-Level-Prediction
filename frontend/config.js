// Single place to configure the backend URL.
// frontend/serve.py forwards /api/* to the FastAPI backend, so the relative path just works.
// Pointing this at "http://127.0.0.1:8000/api/v1" directly would need CORS enabled in the backend.
window.API_BASE = "/api/v1";

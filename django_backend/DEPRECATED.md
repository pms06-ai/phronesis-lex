# Django Backend - DEPRECATED

**This backend is deprecated in favor of the FastAPI backend.**

## Migration Notice

The FastAPI backend (`backend/`) is now the canonical implementation with:
- JWT authentication
- Rate limiting
- Audit logging
- Full FCIP analysis engines (more sophisticated than Django version)
- Lighter weight for single-user deployments

## Why FastAPI?

For a single-user project with AI agent teammates:
1. **Faster**: Native async support, lower overhead
2. **Simpler**: No ORM overhead, direct SQL control
3. **Better FCIP**: The FastAPI backend has more sophisticated analysis engines
4. **Lighter**: Fewer dependencies, faster startup

## Running the FastAPI Backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Or with uvicorn directly:
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## Authentication

Default credentials:
- Username: `admin`
- Password: `phronesis2024`

Or disable auth entirely:
```bash
AUTH_DISABLED=true python app.py
```

## Removal

This directory may be removed in a future version. The Django backend
code is preserved for reference but is no longer maintained.

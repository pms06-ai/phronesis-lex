# Project Audit Report - `phronesis-lex-1`

**Date**: 2025-12-10
**Status**: ⚠️ **CRITICAL ISSUES DETECTED**

## Executive Summary

The project is currently in a **broken state**. The recent integration of the "Documentary Analysis" feature has introduced dependencies and code paths that prevent the backend application from starting in the current environment. The new feature is also hardcoded for a specific use case and lacks frontend integration.

## 1. Critical Issues

### 🚨 Backend Startup Failure

The `backend/app.py` file imports `services.documentary_analysis` at the top level. This module imports `face_recognition`, `faster_whisper`, `pyannote.audio`, and `easyocr` at the top level.
**Result**: Because these dependencies are missing in the current environment, **`app.py` will crash on startup**.

### 🛠️ Missing Complex Dependencies

The following required packages are not installed:

- `face_recognition` (Requires `dlib` + C++ build tools on Windows)
- `faster_whisper` & `pyannote.audio` (Require heavily `torch` + CUDA setup)
- `easyocr`

**Impact**: Even if the code runs, the features will fail. Installing these on Windows is non-trivial and may require specific build tools (Visual Studio C++).

## 2. Architectural Concerns

### 🔒 Hardcoded Business Logic

The file `services/documentary_analysis.py` contains hardcoded patterns specific to **"Channel 4 24 Hours in Police Custody"**:

- `REFERENCE_PATTERNS` (e.g., "paul", "samantha")
- `CRITICAL_EVIDENCE` (e.g., "alderton_praised_paul")

**Impact**: The feature is not reusable for other cases without modifying the source code. This violates the platform's design as a generic "Forensic Case Intelligence Platform".

### 🔌 API Endpoint Issues

The endpoint `POST /api/fcip/documentary/analyze` accepts a `video_path` string but does not handle file uploads.
**Impact**: Users cannot upload videos via the API. They must manually place files on the server filesystem, which breaks the web-app abstraction.

## 3. Incomplete Integration

### 🖥️ Frontend (Next.js)

There are **no frontend components** or pages created to interface with the new Documentary Analysis features.

- No file upload UI for videos.
- No dashboard to view Video Analysis results (Transcripts, Timelines, etc.).

## 4. Recommendations

### Immediate Fixes (To restore app functionality)

1. **Lazy Imports**: Refactor `services/documentary_analysis.py` to import heavy dependencies *inside* the functions that use them, not at the top level. This allows `app.py` to start even if dependencies are missing.
2. **Generic Config**: Move the hardcoded `REFERENCE_PATTERNS` to a JSON configuration file or pass them as arguments to the analysis function.

### Infrastructure

3. **Dependency Script**: Create a specific installation script (e.g., `install_ml_deps.ps1`) that handles the complex Windows installation of `dlib` and `torch`.

### Future Development

4. **Frontend**: Build a `VideoAnalysis` page in the frontend.
5. **Refactor**: Convert the "Documentary Analysis" script into a proper class-based Service that fits the existing `fcip` architecture.

# Dead Code Analysis Report

Generated: 2025-01-27

## Issues Fixed ✅

### 1. Duplicate Imports
- **File**: `django_backend/analysis/tasks.py`
  - **Issue**: Redundant try/except block importing the same module twice
  - **Fixed**: Removed duplicate import logic

- **File**: `django_backend/analysis/views.py`
  - **Issue**: Redundant try/except block with duplicate imports
  - **Fixed**: Simplified to single import attempt, removed unused `get_claude_service` import

### 2. Unused Variables
- **File**: `django_backend/analysis/tasks.py`
  - **Issue**: Variable `total_docs` was assigned but never used
  - **Fixed**: Removed unused variable

### 3. Unused Imports
- **File**: `django_backend/analysis/views.py`
  - **Issue**: `get_claude_service` imported but never used
  - **Fixed**: Removed unused import

### 4. Commented Code Cleanup
- **File**: `django_backend/documents/models.py`
  - **Issue**: Long block of commented-out code (8 lines) explaining field naming decisions
  - **Fixed**: Removed outdated comments, kept only essential field definition

## Potential Dead Code (Needs Review) ⚠️

### 1. Unused Utility Function
- **File**: `django_backend/analysis/utils.py`
  - **Function**: `run_async()` - Helper to run async coroutines from sync context
  - **Status**: Not imported or used anywhere in the codebase
  - **Recommendation**: Remove if not needed, or document if planned for future use

### 2. Unused Import
- **File**: `django_backend/analysis/tasks.py`
  - **Import**: `from cases.models import Case`
  - **Status**: `Case` model imported but never referenced in the file
  - **Recommendation**: Remove if not needed

### 3. Legacy Scripts (One-off Utilities)
- **Files**: 
  - `attribute_documents.py` - Document attribution script
  - `generate_dashboard.py` - HTML dashboard generator
- **Status**: Appear to be one-off utility scripts, not part of main application
- **Recommendation**: Move to `scripts/` directory or remove if no longer needed

### 4. Legacy HTML Files
- **Files**:
  - `index_new.html`
  - `index_refactored.html`
  - `index_temp.html`
- **Status**: Appear to be old versions/backups
- **Recommendation**: Remove if superseded by current `index.html`

### 5. Legacy Backend Folder
- **Path**: `backend/` (separate from `django_backend/`)
- **Status**: Contains old backend code structure
- **Recommendation**: Review and remove if `django_backend/` is the active backend

## Summary

**Fixed Issues**: 5
- 2 duplicate import blocks
- 1 unused variable
- 1 unused import
- 1 commented code cleanup

**Needs Review**: 5 items
- 1 unused utility function
- 1 unused import
- 2 legacy scripts
- 3 legacy HTML files
- 1 legacy backend folder

## Recommendations

1. **Immediate**: Remove unused `Case` import from `analysis/tasks.py` if confirmed unused
2. **Consider**: Remove or document `analysis/utils.py` if `run_async()` is not needed
3. **Organize**: Move utility scripts to `scripts/` directory or remove if obsolete
4. **Cleanup**: Remove old HTML backup files if no longer needed
5. **Review**: Verify if `backend/` folder can be removed in favor of `django_backend/`


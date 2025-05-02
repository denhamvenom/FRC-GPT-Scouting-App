# File: backend/app/services/global_cache.py

# In-memory simple cache (dictionary-based)

cache = {
    "manual_text": None,
    "manual_year": None,
    "last_uploaded_sheet_id": None,
}

# Extend this cache with other session-based info later if needed

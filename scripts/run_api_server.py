#!/usr/bin/env python3
"""
Run the FastAPI server for Logical Version API.
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("src.api.app:app", host="127.0.0.1", port=8000, reload=False)

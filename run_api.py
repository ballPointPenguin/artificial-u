#!/usr/bin/env python3
"""
Script to run the FastAPI server for the Artificial University API
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "artificial_u.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

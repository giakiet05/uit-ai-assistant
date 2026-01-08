#!/usr/bin/env python3
"""
Launch UIT Knowledge Builder Dashboard.

Streamlit runs dashboard files as scripts, so they cannot use relative imports.
Just run streamlit directly - no need for special module loading.
"""
import subprocess
import sys
from pathlib import Path


def main():
    project_root = Path(__file__).parent
    
    print("Starting UIT Knowledge Builder Dashboard...")
    print("Dashboard will open at http://localhost:8501")
    print("\nPress Ctrl+C to stop\n")

    try:
        # Run streamlit normally - dashboard handles its own imports
        subprocess.run([
            "streamlit",
            "run",
            "src/dashboard/app.py",
            "--server.headless", "true",
            "--server.port", "8501"
        ], cwd=project_root)
    except KeyboardInterrupt:
        print("\nDashboard stopped")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

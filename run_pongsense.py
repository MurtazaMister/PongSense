"""
PongSense Launcher Script
Run this from the project root to start PongSense.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run main
if __name__ == "__main__":
    try:
        from main import main
        main()
    except KeyboardInterrupt:
        print("\nPongSense stopped by user")
    except Exception as e:
        print(f"Error starting PongSense: {e}")
        sys.exit(1)

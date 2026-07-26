import sys
import os

# Add root directory to python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.app import main

if __name__ == "__main__":
    main()

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'frontend')))

from frontend.main import main


if __name__ == "__main__":
    main()
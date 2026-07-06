import sys
import os
import multiprocessing

if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.path.insert(0, os.path.dirname(__file__))
    from woodwind_designer.main import main
    main()

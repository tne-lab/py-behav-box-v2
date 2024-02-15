try:
    from pybehave import pybehave
except ImportError:
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from pybehave import pybehave

if __name__ == '__main__':
    pybehave()

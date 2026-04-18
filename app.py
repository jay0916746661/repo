import os, sys
sys.path.insert(0, os.path.dirname(__file__))
exec(compile(open(os.path.join(os.path.dirname(__file__), "dashboard.py")).read(),
             "dashboard.py", "exec"))

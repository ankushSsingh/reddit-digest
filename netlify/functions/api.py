import sys
import os

# Make sure the project root is on the path so backend can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from mangum import Mangum
from backend.main import app

handler = Mangum(app, lifespan="off")

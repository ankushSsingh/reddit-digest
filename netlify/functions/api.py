import sys
import os

# backend/ is copied alongside this file during the build step (see package.json)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mangum import Mangum
from backend.main import app

_mangum = Mangum(app, lifespan="off")


def handler(event, context):
    return _mangum(event, context)

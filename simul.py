import fire
import importlib
import os
import app.core.logging as log
import app.core.simulation as sim
import app.core.script as script
from app.core.app import Application

app=Application(os.path.dirname(os.path.realpath(__file__)))
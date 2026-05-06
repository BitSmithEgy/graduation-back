# At the top, add these imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import Base   # your SQLAlchemy Base
import models               # ensures all models are registered

# Then find this line:
target_metadata = None

# And replace it with:
target_metadata = Base.metadata
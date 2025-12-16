import os

import casbin
import casbin_sqlalchemy_adapter

from app.core.database import engine
from app.model.casbin_rule import CasbinRule

# Get the absolute path to the model file
model_path = os.path.join(os.path.dirname(__file__), "../../rbac_model.conf")

# Initialize the Casbin adapter with SQLAlchemy
adapter = casbin_sqlalchemy_adapter.Adapter(engine, CasbinRule)

# Create the Casbin enforcer
enforcer = casbin.Enforcer(model_path, adapter)

# Load existing policies from the database
enforcer.load_policy()

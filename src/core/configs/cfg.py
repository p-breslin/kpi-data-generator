import logging
import os

from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)

# Customer info
CUSTOMER_EMAIL = "peter.breslin+1@experienceflow.ai"
INDUSTRY_ID = 1915

# Settings for the Model Definition API (dats-api)
ONBOARDING_API_URL = "https://onboarding-dev-1.xflow-in.dev"
DATS_API_URL = "https://domain-dev-1.xflow-in.dev"

# Credentials for an admin with permissions to create new partners/customers
ADMIN_EMAIL = "peter.breslin@experienceflow.ai"
ADMIN_PASSWORD = os.getenv("XFLOW_PWD")

# Connection details for the ArangoDB instance where graphs are stored
ARANGO_HOST = "http://arangodb.in.dev.xflow/"
ARANGO_USER = "root"
ARANGO_PASSWORD = ""

# Graph engine API settings
EDNS_GRAPH_API_BASE_URL = "http://graph.in.dev.xflow"
GRAPH_API_EMAIL = "graph-test@xflow.ai"
GRAPH_API_PASSWORD = os.getenv("XFLOW_PWD")

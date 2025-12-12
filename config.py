import yaml
import os

# BASE_DIR should be the directory that contains policy.yml
BASE_DIR = "/Users/howardhuntermckeon/Desktop/593 project"

POLICY_PATH = os.path.join(BASE_DIR, "policy.yml")

with open(POLICY_PATH, "r") as f:
    POLICY_CONFIG = yaml.safe_load(f)

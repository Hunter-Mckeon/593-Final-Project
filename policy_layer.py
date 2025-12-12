# policy_layer.py

from dataclasses import dataclass
from typing import Any, Callable
from config import POLICY_CONFIG

# ---- Context type used by all policies ----
@dataclass
class Context:
    user_id: int
    role: str         # "user", "admin", "dpo", etc.
    purpose: str      # "task_view", "task_edit", "sar_access", etc.


# ---- Base policy class ----
class Policy:
    def check(self, ctx: Context) -> bool:
        raise NotImplementedError


# ---- Policy Container (Sesame-lite PCon) ----
class PCon:
    def __init__(self, data: Any, policy: Policy):
        self._data = data
        self._policy = policy

    def with_privacy(self, fn: Callable[[Any], Any]) -> "PCon":
        # In real Sesame, static analysis decides verified vs sandboxed.
        # Here we just call the function directly.
        result = fn(self._data)
        # Keep the same policy on the transformed data
        return PCon(result, self._policy)

    def reveal(self, ctx: Context) -> Any:
        if not self._policy.check(ctx):
            raise PermissionError("Policy check failed")
        return self._data


# ---- TaskPolicy: THIS is the part that must match your test code ----
class TaskPolicy(Policy):
    """
    Minimal Sesame-like policy for tasks.
    Reads access rules from policy.yml under data_categories.task.
    """

    def __init__(self, project_id: int, project_owner_id: int):
        # These names MUST match how you call TaskPolicy(...)
        self.project_id = project_id
        self.project_owner_id = project_owner_id

        # Load YAML config section for tasks
        self.config = POLICY_CONFIG["data_categories"]["task"]

    def check(self, ctx: Context) -> bool:
        """
        Use the YAML rules to decide if this context can see the task.
        For now we implement a simple subset:

        - If purpose matches a rule and:
          - ctx.user_id == project_owner_id and 'project_owner'/'owner' allowed
          - or ctx.role == 'admin' and 'admin' allowed
          - or ctx.role == 'dpo' and 'dpo' allowed
        then allow.
        Otherwise deny.
        """
        for rule in self.config["access_policies"]:
            if rule["purpose"] != ctx.purpose:
                continue

            allowed = rule["allow"]

            # Owner (project_owner / owner)
            if ("project_owner" in allowed or "owner" in allowed) and ctx.user_id == self.project_owner_id:
                return True

            # Admin
            if "admin" in allowed and ctx.role == "admin":
                return True

            # DPO
            if "dpo" in allowed and ctx.role == "dpo":
                return True

            # NOTE: project_member logic would require a DB lookup;
            # you can add that later if you want.
            # if "project_member" in allowed: ...

        # If we didn't match any allowed rule → deny
        return False
    
class UserPolicy(Policy):
    """
    Policy for rows in the users table (user-profile data).

    Uses policy.yml -> data_categories.user_profile.access_policies.

    Semantics:
      - 'self' means ctx.user_id == this user's id
      - 'owner' is treated the same as 'self' here
      - 'admin' means ctx.role == 'admin'
      - 'dpo' means ctx.role == 'dpo'
    """
    def __init__(self, user_id: int):
        self.user_id = user_id

        # Be defensive: handle missing keys or null values
        dcats = POLICY_CONFIG.get("data_categories") or {}
        cat = dcats.get("user_profile") or {}
        self.access_policies = cat.get("access_policies") or []

    def check(self, ctx: Context) -> bool:
        for rule in self.access_policies:
            # Match by purpose (e.g., 'sar_access', 'task_view')
            if rule.get("purpose") != ctx.purpose:
                continue

            allowed = set(rule.get("allow", []))

            # Self / owner (same idea here)
            if ("self" in allowed or "owner" in allowed) and ctx.user_id == self.user_id:
                return True

            # Admin
            if "admin" in allowed and ctx.role == "admin":
                return True

            # DPO
            if "dpo" in allowed and ctx.role == "dpo":
                return True

        # No rule matched -> deny
        return False



class ProjectPolicy(Policy):
    """
    Policy for rows in the projects table.

    Uses policy.yml -> data_categories.project.access_policies.

    Semantics:
      - 'owner' / 'project_owner' means ctx.user_id == project.owner_id
      - 'admin' means ctx.role == 'admin'
      - 'dpo' means ctx.role == 'dpo'
    """
    def __init__(self, owner_id: int):
        self.owner_id = owner_id

        dcats = POLICY_CONFIG.get("data_categories") or {}
        cat = dcats.get("project") or {}
        self.access_policies = cat.get("access_policies") or []

    def check(self, ctx: Context) -> bool:
        for rule in self.access_policies:
            if rule.get("purpose") != ctx.purpose:
                continue

            allowed = set(rule.get("allow", []))

            # Project owner
            if ("owner" in allowed or "project_owner" in allowed) and ctx.user_id == self.owner_id:
                return True

            # Admin
            if "admin" in allowed and ctx.role == "admin":
                return True

            # DPO
            if "dpo" in allowed and ctx.role == "dpo":
                return True

        return False


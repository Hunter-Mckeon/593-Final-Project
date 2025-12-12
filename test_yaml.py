from policy_layer import PCon, Context, TaskPolicy
from config import POLICY_CONFIG

# === Example DB row (pretend we fetched from DB) ===
task_row = {
    "id": 10,
    "project_id": 123,
    "title": "Finish DS593",
    "owner_id": 42   # this matters for ownership
}

# === Build a TaskPolicy using the YAML rules ===
policy = TaskPolicy(
    project_id=task_row["project_id"],
    project_owner_id=task_row["owner_id"]
)

# === Wrap the title in a PCon ===
p = PCon(task_row["title"], policy)

# === Case 1: Allowed context (owner viewing task) ===
allowed_ctx = Context(
    user_id=42,
    role="user",
    purpose="task_view"
)

print("\n=== Allowed User ===")
try:
    print("Reveal:", p.reveal(allowed_ctx))
except Exception as e:
    print("Reveal failed:", e)

# === Case 2: NOT allowed (random user tries to view task) ===
blocked_ctx = Context(
    user_id=99,
    role="user",
    purpose="task_view"
)

print("\n=== Blocked User ===")
try:
    print("Reveal:", p.reveal(blocked_ctx))
except Exception as e:
    print("Reveal failed:", e)

# === Case 3: Admin user (allowed) ===
admin_ctx = Context(
    user_id=1,
    role="admin",
    purpose="task_view"
)

print("\n=== Admin User ===")
try:
    print("Reveal:", p.reveal(admin_ctx))
except Exception as e:
    print("Reveal failed:", e)

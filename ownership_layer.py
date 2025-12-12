# ownership_layer.py
from policy_layer import PCon, Context, TaskPolicy, UserPolicy, ProjectPolicy


import sqlite3
from typing import Dict, Any, List

DB_PATH = "example.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def get_all_data_for(user_id: int):
    """
    K9db-lite style SAR traversal:
      - users row
      - projects owned by user
      - tasks in those projects
      - project_membership for those projects
      - profile_notes for this user
      - login_events for this user
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    bundle: dict[str, list[dict]] = {}

    # user row
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    bundle["users"] = [dict(r) for r in cur.fetchall()]

    # projects owned by this user
    cur.execute("SELECT * FROM projects WHERE owner_id = ?", (user_id,))
    projects = cur.fetchall()
    bundle["projects"] = [dict(r) for r in projects]

    project_ids = [r["id"] for r in projects]

    # tasks + memberships for those projects
    if project_ids:
        placeholders = ",".join("?" * len(project_ids))

        cur.execute(
            f"SELECT * FROM tasks WHERE project_id IN ({placeholders})",
            project_ids,
        )
        bundle["tasks"] = [dict(r) for r in cur.fetchall()]

        cur.execute(
            f"SELECT * FROM project_members WHERE project_id IN ({placeholders})",
            project_ids,
        )
        bundle["project_membership"] = [dict(r) for r in cur.fetchall()]
    else:
        bundle["tasks"] = []
        bundle["project_membership"] = []

    # profile_notes directly owned by this user
    cur.execute("SELECT * FROM profile_notes WHERE user_id = ?", (user_id,))
    bundle["profile_notes"] = [dict(r) for r in cur.fetchall()]

    # login_events for this user
    cur.execute("SELECT * FROM login_events WHERE user_id = ?", (user_id,))
    bundle["login_events"] = [dict(r) for r in cur.fetchall()]

    conn.close()
    return bundle


def delete_all_data_for(user_id: int):
    """
    K9db-lite style deletion:
      - delete profile_notes and login_events for this user
      - delete project_membership rows for projects they own
      - delete tasks in those projects
      - delete projects they own
      - delete the user row
    Does NOT touch other users' rows (e.g., notes/events for user 99).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("PRAGMA foreign_keys = ON;")

    # Find projects owned by this user
    cur.execute("SELECT id FROM projects WHERE owner_id = ?", (user_id,))
    project_ids = [row["id"] for row in cur.fetchall()]

    # Delete profile_notes and login_events for this user
    cur.execute("DELETE FROM profile_notes WHERE user_id = ?", (user_id,))
    cur.execute("DELETE FROM login_events WHERE user_id = ?", (user_id,))

    # If they own projects, delete tasks and memberships tied to those projects
    if project_ids:
        placeholders = ",".join("?" * len(project_ids))

        cur.execute(
            f"DELETE FROM project_members WHERE project_id IN ({placeholders})",
            project_ids,
        )
        cur.execute(
            f"DELETE FROM tasks WHERE project_id IN ({placeholders})",
            project_ids,
        )
        cur.execute(
            f"DELETE FROM projects WHERE id IN ({placeholders})",
            project_ids,
        )

    # Finally, delete the user row
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))

    conn.commit()
    conn.close()

def populate_demo_data_for(user_id: int = 42):
    """
    Create demo data for a given user_id:
      - user row for `user_id`
      - one project owned by that user
      - 10 tasks in that project
      - a member user (99) added to the project
      - an admin user (1)
      - several profile_notes and login_events for this user
      - also ensures user 99 has their own notes/events to show they survive deletion of 42
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("PRAGMA foreign_keys = ON;")

    def ensure_user(id_, email, name):
        cur.execute("SELECT 1 FROM users WHERE id = ?", (id_,))
        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO users (id, email, name) VALUES (?, ?, ?)",
                (id_, email, name),
            )

    # owner user
    ensure_user(user_id, f"owner{user_id}@example.com", f"Owner {user_id}")

    # member user
    ensure_user(99, "member@example.com", "Member User")

    # admin user
    ensure_user(1, "admin@example.com", "Admin User")

    # --- create a project owned by user_id (if not exists) ---
    cur.execute(
        "SELECT id FROM projects WHERE owner_id = ? LIMIT 1",
        (user_id,),
    )
    row = cur.fetchone()
    if row is None:
        project_id = 123  # fixed id for demo
        cur.execute(
            "INSERT INTO projects (id, owner_id, title) VALUES (?, ?, ?)",
            (project_id, user_id, "K9db Demo Project"),
        )
    else:
        project_id = row["id"]

    # --- ensure user 99 is a member of this project ---
    cur.execute(
        "SELECT 1 FROM project_members WHERE project_id = ? AND user_id = ?",
        (project_id, 99),
    )
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO project_members (project_id, user_id, role) VALUES (?, ?, ?)",
            (project_id, 99, "editor"),
        )

    # --- create 10 tasks for this project (only if fewer than 10 exist) ---
    cur.execute(
        "SELECT COUNT(*) FROM tasks WHERE project_id = ?",
        (project_id,),
    )
    existing_count = cur.fetchone()[0]
    to_create = max(0, 10 - existing_count)
    for i in range(to_create):
        cur.execute(
            "INSERT INTO tasks (project_id, title, done) VALUES (?, ?, ?)",
            (project_id, f"Sample Task #{existing_count + i + 1}", 0),
        )

    # --- profile_notes for this user ---
    cur.execute(
        "SELECT COUNT(*) FROM profile_notes WHERE user_id = ?",
        (user_id,),
    )
    notes_count = cur.fetchone()[0]
    notes_to_create = max(0, 3 - notes_count)
    for i in range(notes_to_create):
        cur.execute(
            "INSERT INTO profile_notes (user_id, note) VALUES (?, ?)",
            (user_id, f"Note #{notes_count + i + 1} for user {user_id}"),
        )

    # --- login_events for this user ---
    cur.execute(
        "SELECT COUNT(*) FROM login_events WHERE user_id = ?",
        (user_id,),
    )
    ev_count = cur.fetchone()[0]
    ev_to_create = max(0, 5 - ev_count)
    for i in range(ev_to_create):
        cur.execute(
            "INSERT INTO login_events (user_id, ts, ip) VALUES (?, datetime('now'), ?)",
            (user_id, f"192.0.2.{(ev_count + i) % 255}"),
        )

    # --- also seed some notes/events for user 99 so we can show they survive deletion of 42 ---
    for other_id in (99,):
        cur.execute(
            "SELECT COUNT(*) FROM profile_notes WHERE user_id = ?",
            (other_id,),
        )
        c = cur.fetchone()[0]
        if c == 0:
            cur.execute(
                "INSERT INTO profile_notes (user_id, note) VALUES (?, ?)",
                (other_id, f"Note for user {other_id}"),
            )

        cur.execute(
            "SELECT COUNT(*) FROM login_events WHERE user_id = ?",
            (other_id,),
        )
        c2 = cur.fetchone()[0]
        if c2 == 0:
            cur.execute(
                "INSERT INTO login_events (user_id, ts, ip) VALUES (?, datetime('now'), ?)",
                (other_id, "198.51.100.99"),
            )

    conn.commit()
    conn.close()

def sar_access_with_policies(user_id: int, ctx: Context):
    bundle = get_all_data_for(user_id)
    result = {}

    # === USERS: enforce SAR semantics inline (matching policy.yml) ===
    protected_users = []
    for row in bundle.get("users", []):
        # For sar_access:
        #  - self (user_id == row["id"])
        #  - admin
        #  - dpo
        if ctx.purpose == "sar_access" and (
            ctx.user_id == row["id"] or ctx.role in ("admin", "dpo")
        ):
            # full visibility
            protected_users.append(dict(row))
        else:
            # redact sensitive profile fields
            protected_users.append({
                "id": "REDACTED",
                "email": "REDACTED",
                "name": "REDACTED",
            })
    result["users"] = protected_users

    # === PROJECTS: enforce SAR semantics inline (matching policy.yml) ===
    protected_projects = []
    for row in bundle.get("projects", []):
        owner_id = row["owner_id"]

        # For sar_access:
        #  - project owner
        #  - admin
        #  - dpo
        if ctx.purpose == "sar_access" and (
            ctx.user_id == owner_id or ctx.role in ("admin", "dpo")
        ):
            protected_projects.append(dict(row))
        else:
            protected_projects.append({
                "id": "REDACTED",
                "owner_id": "REDACTED",
                "title": "REDACTED",
            })
    result["projects"] = protected_projects

    # === project_membership left raw for now ===
    result["project_membership"] = bundle.get("project_membership", [])


    # Handle tasks with Sesame field-level policies
    tasks = bundle.get("tasks", [])

    if tasks:
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        protected_rows = []

        for row in tasks:
            # Look up the owner of the project this task belongs to
            cur.execute("SELECT owner_id FROM projects WHERE id = ?", (row["project_id"],))
            proj = cur.fetchone()
            if proj is None:
                protected_rows.append(row)
                continue

            owner_id = proj["owner_id"]

            # Build Sesame policy for this task
            policy = TaskPolicy(project_id=row["project_id"], project_owner_id=owner_id)

            # Wrap fields in PCon for Sesame enforcement
            title_pcon = PCon(row["title"], policy)
            done_pcon = PCon(row["done"], policy)

            # Reveal fields using the provided Context
            try:
                visible_title = title_pcon.reveal(ctx)
            except Exception:
                visible_title = "REDACTED"

            try:
                visible_done = done_pcon.reveal(ctx)
            except Exception:
                visible_done = "REDACTED"

            protected_rows.append({
                "id": row["id"],
                "project_id": row["project_id"],
                "title": visible_title,
                "done": visible_done,
            })

        conn.close()
        result["tasks"] = protected_rows
    else:
        result["tasks"] = []

    return result

def sar_delete_with_policies(target_user_id: int, ctx: Context):
    """
    Policy-checked SAR deletion.

    Only allowed if:
      - the requester is deleting their own data, OR
      - the requester is an admin or DPO.
    Otherwise, raise PermissionError.
    """
    # Simple Sesame-style check at the "endpoint" level
    if ctx.user_id == target_user_id:
        allowed = True
    elif ctx.role in ("admin", "dpo"):
        allowed = True
    else:
        allowed = False

    if not allowed:
        raise PermissionError(
            f"user {ctx.user_id} with role={ctx.role} is not allowed to delete user {target_user_id}'s data"
        )

    # If allowed, call K9db-lite deletion
    delete_all_data_for(target_user_id)



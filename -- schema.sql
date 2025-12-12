-- schema.sql

PRAGMA foreign_keys = ON;

CREATE TABLE users (
  id        INTEGER PRIMARY KEY,
  email     TEXT NOT NULL UNIQUE,
  name      TEXT NOT NULL
  -- OWNED BY: user.id (root)
);

CREATE TABLE projects (
  id        INTEGER PRIMARY KEY,
  owner_id  INTEGER NOT NULL,
  title     TEXT NOT NULL,
  FOREIGN KEY (owner_id) REFERENCES users(id)
  -- OWNED BY: users.id VIA owner_id
);

CREATE TABLE project_members (
  project_id INTEGER NOT NULL,
  user_id    INTEGER NOT NULL,
  role       TEXT NOT NULL, -- e.g. "owner", "editor", "viewer"
  PRIMARY KEY (project_id, user_id),
  FOREIGN KEY (project_id) REFERENCES projects(id),
  FOREIGN KEY (user_id)    REFERENCES users(id)
  -- OWNED BY: users.id VIA user_id
);

CREATE TABLE tasks (
  id         INTEGER PRIMARY KEY,
  project_id INTEGER NOT NULL,
  title      TEXT NOT NULL,
  done       INTEGER NOT NULL DEFAULT 0, -- 0=false, 1=true
  FOREIGN KEY (project_id) REFERENCES projects(id)
  -- OWNED BY: projects.id VIA project_id
  -- => ultimately owned by the same user as the project owner
);

"""
API tests run against a real PostgreSQL database (DATABASE_URL, migrated with
`alembic upgrade head`). Every test uses uniquely named data, so a dev database
can be reused; do not point this at production.
"""
import os
import sys
import uuid
import tempfile

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault("UPLOAD_DIR", tempfile.mkdtemp(prefix="dbwiki-uploads-"))

from main import app  # noqa: E402
from app.database import get_session_local  # noqa: E402
from app.models.db_models import User, Role  # noqa: E402
from app.crud import user_space_roles as usr_crud  # noqa: E402


def _uid() -> str:
    return uuid.uuid4().hex[:8]


class Actor:
    """A logged-in (or anonymous) API client."""

    def __init__(self, email=None):
        self.client = TestClient(app)
        self.email = email
        self.id = None

    def __getattr__(self, name):  # get/post/put/patch/delete passthrough
        return getattr(self.client, name)


def make_user(superuser=False) -> Actor:
    uid = _uid()
    email = f"t{uid}@example.com"
    actor = Actor(email)
    r = actor.client.post("/api/auth/register", json={
        "email": email, "username": f"u{uid}", "password": "password123", "name": uid})
    assert r.status_code == 200, r.text
    actor.id = r.json()["id"]
    if superuser:
        db = get_session_local()()
        db.query(User).filter(User.id == actor.id).update({"is_superuser": True})
        db.commit()
        db.close()
    r = actor.client.post("/api/auth/login", json={"email": email, "password": "password123"})
    assert r.status_code == 200, r.text
    return actor


def add_member(space_id: str, user: Actor, role_name: str):
    db = get_session_local()()
    role = db.query(Role).filter(Role.name == role_name).one()
    usr_crud.add_user_to_space(db, user.id, space_id, role.id)
    db.close()


@pytest.fixture()
def admin():
    return make_user(superuser=True)


@pytest.fixture()
def anon():
    return Actor()


@pytest.fixture()
def space(admin):
    """A public space owned by the superuser."""
    r = admin.post("/api/spaces", json={"key": f"k{_uid()}", "name": "Test", "is_public": True})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture()
def private_space(admin):
    r = admin.post("/api/spaces", json={"key": f"p{_uid()}", "name": "Private"})
    assert r.status_code == 200, r.text
    return r.json()


def create_page(actor, space_id, title="Page", **extra):
    r = actor.post("/api/pages", json={"space_id": space_id, "title": title, **extra})
    assert r.status_code == 201, r.text
    return r.json()


def node_of(actor, space_id, page_id):
    nodes = actor.get(f"/api/tree/space/{space_id}").json()
    return next(n for n in nodes if n["page_id"] == page_id)

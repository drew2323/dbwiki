import io

from tests.conftest import create_page, node_of, make_user, add_member


# ---------------------------------------------------------------- bug fixes

def test_post_pages_without_trailing_slash_does_not_redirect(admin, space):
    r = admin.post("/api/pages", json={"space_id": space["id"], "title": "x"}, follow_redirects=False)
    assert r.status_code == 201


def test_duplicate_titles_get_unique_slugs(admin, space):
    a = create_page(admin, space["id"], "Same")
    b = create_page(admin, space["id"], "Same")
    c = create_page(admin, space["id"], "Same")
    assert [a["slug"], b["slug"], c["slug"]] == ["same", "same-2", "same-3"]


def test_symbol_only_title_still_gets_a_slug(admin, space):
    assert create_page(admin, space["id"], "!!!")["slug"] == "page"


def test_bad_parent_is_rejected_and_leaves_no_orphan_page(admin, space):
    parent_page = create_page(admin, space["id"], "P")
    # a page id is not a tree node id
    r = admin.post("/api/pages", json={"space_id": space["id"], "title": "Child",
                                       "parent_id": parent_page["id"]})
    assert r.status_code == 400
    pages = admin.get(f"/api/pages/space/{space['id']}/list").json()
    assert [p["title"] for p in pages] == ["P"]
    # retry with the proper node id works and nests below the parent
    parent_node = node_of(admin, space["id"], parent_page["id"])
    child = create_page(admin, space["id"], "Child", parent_id=parent_node["id"])
    assert node_of(admin, space["id"], child["id"])["parent_id"] == parent_node["id"]


def test_parent_from_other_space_is_rejected(admin, space, private_space):
    other = create_page(admin, private_space["id"], "Other")
    other_node = node_of(admin, private_space["id"], other["id"])
    r = admin.post("/api/pages", json={"space_id": space["id"], "title": "x",
                                       "parent_id": other_node["id"]})
    assert r.status_code == 400


def test_anonymous_can_read_public_space_but_not_private(admin, anon, space, private_space):
    page = create_page(admin, space["id"], "Open")
    admin.put(f"/api/pages/{page['id']}/draft",
              json={"draft_json": {"type": "doc", "content": []}, "draft_text": "secret draft"})
    assert anon.get(f"/api/tree/space/{space['id']}").status_code == 200
    assert anon.get(f"/api/spaces/{space['id']}").status_code == 200
    r = anon.get(f"/api/pages/{page['id']}")
    assert r.status_code == 200
    assert r.json()["draft_json"] is None and r.json()["draft_text"] is None  # drafts stay private
    assert anon.get(f"/api/pages/{page['id']}/draft").status_code == 401

    hidden = create_page(admin, private_space["id"], "Hidden")
    assert anon.get(f"/api/tree/space/{private_space['id']}").status_code == 401
    assert anon.get(f"/api/pages/{hidden['id']}").status_code == 401
    assert anon.get(f"/api/spaces/{private_space['id']}").status_code == 401


def test_visibility_and_is_public_stay_in_sync(admin):
    r = admin.post("/api/spaces", json={"key": "v" + make_user().email[:6], "name": "v", "is_public": True})
    assert r.json()["visibility"] == "public"
    sid = r.json()["id"]
    r = admin.put(f"/api/spaces/{sid}", json={"is_public": False})
    assert (r.json()["visibility"], r.json()["is_public"]) == ("private", False)
    r = admin.put(f"/api/spaces/{sid}", json={"visibility": "public"})
    assert (r.json()["visibility"], r.json()["is_public"]) == ("public", True)


def test_update_space_requires_auth(anon, space):
    assert anon.put(f"/api/spaces/{space['id']}", json={"name": "hacked"}).status_code == 401


# ------------------------------------------------------------- access control

def test_roles_read_cannot_write_edit_can(admin, private_space):
    sid = private_space["id"]
    reader, editor, outsider = make_user(), make_user(), make_user()
    add_member(sid, reader, "read")
    add_member(sid, editor, "edit")
    page = create_page(admin, sid, "Doc")

    assert reader.get(f"/api/pages/{page['id']}").status_code == 200
    assert reader.post("/api/pages", json={"space_id": sid, "title": "no"}).status_code == 403
    assert reader.patch(f"/api/pages/{page['id']}", json={"title": "no"}).status_code == 403
    assert reader.delete(f"/api/pages/{page['id']}").status_code == 403
    assert reader.put(f"/api/pages/{page['id']}/draft", json={"draft_text": "x"}).status_code == 403

    assert editor.patch(f"/api/pages/{page['id']}", json={"title": "Renamed"}).status_code == 200
    assert outsider.get(f"/api/pages/{page['id']}").status_code == 403


def test_creator_of_space_becomes_admin_member():
    creator = make_user()
    r = creator.post("/api/spaces", json={"key": "c" + creator.id[:6], "name": "Mine"})
    sid = r.json()["id"]
    assert sid in [s["id"] for s in creator.get("/api/spaces").json()]
    assert create_page(creator, sid, "Mine")["title"] == "Mine"


# --------------------------------------------------------------- page ops

def test_rename_changes_title_and_slug_and_rejects_empty(admin, space):
    page = create_page(admin, space["id"], "Old name")
    r = admin.patch(f"/api/pages/{page['id']}", json={"title": "  New name  "})
    assert (r.json()["title"], r.json()["slug"]) == ("New name", "new-name")
    assert admin.patch(f"/api/pages/{page['id']}", json={"title": "   "}).status_code == 422


def test_rename_to_existing_slug_is_made_unique_and_explicit_clash_is_409(admin, space):
    create_page(admin, space["id"], "Taken")
    other = create_page(admin, space["id"], "Other")
    r = admin.patch(f"/api/pages/{other['id']}", json={"title": "Taken"})
    assert r.json()["slug"] == "taken-2"
    assert admin.patch(f"/api/pages/{other['id']}", json={"slug": "taken"}).status_code == 409


def test_delete_archives_page_and_descendants_hard_delete_removes_them(admin, space):
    sid = space["id"]
    root = create_page(admin, sid, "Root")
    child = create_page(admin, sid, "Child", parent_id=node_of(admin, sid, root["id"])["id"])
    grand = create_page(admin, sid, "Grand", parent_id=node_of(admin, sid, child["id"])["id"])
    sibling = create_page(admin, sid, "Sibling")

    assert admin.delete(f"/api/pages/{child['id']}").status_code == 204
    titles = {p["title"] for p in admin.get(f"/api/pages/space/{sid}/list").json()}
    assert titles == {"Root", "Sibling"}  # Child and Grand archived
    archived = {p["title"] for p in admin.get(f"/api/pages/space/{sid}/list?include_archived=true").json()}
    assert {"Child", "Grand"} <= archived

    assert admin.delete(f"/api/pages/{root['id']}?hard_delete=true").status_code == 204
    assert admin.get(f"/api/pages/{root['id']}").status_code == 404
    assert admin.get(f"/api/pages/{sibling['id']}").status_code == 200


def test_duplicate_copies_content_next_to_original(admin, space):
    sid = space["id"]
    a = create_page(admin, sid, "A")
    b = create_page(admin, sid, "B")
    doc = {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "hello"}]}]}
    admin.put(f"/api/pages/{a['id']}/draft", json={"draft_json": doc, "draft_text": "hello"})

    r = admin.post(f"/api/pages/{a['id']}/duplicate")
    assert r.status_code == 201
    copy = r.json()
    assert copy["title"] == "A (copy)" and copy["id"] != a["id"]
    assert admin.get(f"/api/pages/{copy['id']}").json()["draft_json"] == doc

    order = [n["page_id"] for n in sorted(admin.get(f"/api/tree/space/{sid}").json(),
                                          key=lambda n: n["position"]) if n["page_id"]]
    assert order == [a["id"], copy["id"], b["id"]]

    named = admin.post(f"/api/pages/{a['id']}/duplicate", json={"title": "Custom"}).json()
    assert named["title"] == "Custom"


def test_duplicate_uses_published_content_when_no_draft(admin, space):
    page = create_page(admin, space["id"], "Pub")
    doc = {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "v1"}]}]}
    admin.put(f"/api/pages/{page['id']}/draft", json={"draft_json": doc, "draft_text": "v1"})
    assert admin.post(f"/api/pages/{page['id']}/publish", json={}).status_code == 201
    copy = admin.post(f"/api/pages/{page['id']}/duplicate").json()
    assert admin.get(f"/api/pages/{copy['id']}").json()["draft_text"] == "v1"


def test_templates_listing_and_create_from_template(admin, space):
    templates = admin.get("/api/pages/templates").json()
    ids = {t["id"] for t in templates}
    assert {"blank", "meeting-notes", "how-to", "decision-record"} <= ids

    page = create_page(admin, space["id"], "Standup", template_id="meeting-notes")
    detail = admin.get(f"/api/pages/{page['id']}").json()
    assert detail["draft_json"]["type"] == "doc"
    assert "Agenda" in detail["draft_text"]
    assert detail["draft_etag"] is None or isinstance(detail["draft_etag"], str)

    blank = create_page(admin, space["id"], "Empty", template_id="blank")
    assert admin.get(f"/api/pages/{blank['id']}").json()["draft_json"] is None
    r = admin.post("/api/pages", json={"space_id": space["id"], "title": "x", "template_id": "nope"})
    assert r.status_code == 400


def test_draft_etag_conflict_and_publish_flow_still_work(admin, space):
    page = create_page(admin, space["id"], "Flow")
    doc = {"type": "doc", "content": []}
    r = admin.put(f"/api/pages/{page['id']}/draft", json={"draft_json": doc, "draft_text": "a"})
    etag = r.json()["draft_etag"]
    assert admin.put(f"/api/pages/{page['id']}/draft",
                     json={"draft_json": doc, "if_match": "bogus"}).status_code == 409
    assert admin.put(f"/api/pages/{page['id']}/draft",
                     json={"draft_json": doc, "if_match": etag}).status_code == 200
    assert admin.post(f"/api/pages/{page['id']}/publish", json={"notes": "v1"}).json()["version_number"] == 1
    assert len(admin.get(f"/api/pages/{page['id']}/versions").json()) == 1


# ------------------------------------------------------------------ search

def test_search_matches_title_and_body_prefix_and_ranks_title_first(admin, space):
    sid = space["id"]
    body_only = create_page(admin, sid, "Notes")
    admin.put(f"/api/pages/{body_only['id']}/draft",
              json={"draft_json": {"type": "doc", "content": []}, "draft_text": "volatility surface calibration"})
    title_hit = create_page(admin, sid, "Volatility overview")

    r = admin.post("/api/pages/search", json={"query": "volat", "space_id": sid})
    results = r.json()["results"]
    assert [x["page_id"] for x in results] == [title_hit["id"], body_only["id"]]
    assert results[0]["rank"] > results[1]["rank"] > 0
    assert results[0]["space_name"] == "Test"

    assert admin.post("/api/pages/search", json={"query": "surface calib", "space_id": sid}).json()["total"] == 1
    assert admin.post("/api/pages/search", json={"query": "100%_", "space_id": sid}).json()["total"] == 0


def test_search_hides_private_spaces_and_snippets_from_non_editors(admin, anon, space, private_space):
    marker = "zzmarker" + make_user().id[:6]
    pub = create_page(admin, space["id"], marker + " public")
    admin.put(f"/api/pages/{pub['id']}/draft",
              json={"draft_json": {"type": "doc", "content": []}, "draft_text": marker + " body text"})
    create_page(admin, private_space["id"], marker + " private")

    admin_hits = admin.post("/api/pages/search", json={"query": marker}).json()
    assert admin_hits["total"] == 2
    assert next(x for x in admin_hits["results"] if x["page_id"] == pub["id"])["snippet"]

    anon_hits = anon.post("/api/pages/search", json={"query": marker}).json()
    assert [x["page_id"] for x in anon_hits["results"]] == [pub["id"]]
    assert anon_hits["results"][0]["snippet"] is None
    assert anon.post("/api/pages/search", json={"query": marker, "space_id": private_space["id"]}).status_code == 401


# -------------------------------------------------------------- attachments

PNG = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
       b"\x00\x00\x00\rIDATx\x9cc\xf8\xcf\xc0\x00\x00\x03\x01\x01\x00\xc9\xfe\x92\xef\x00\x00\x00\x00IEND\xaeB`\x82")


def upload(actor, space_id, name, data, mime, page_id=None):
    params = {"space_id": space_id}
    if page_id:
        params["page_id"] = page_id
    return actor.post("/api/attachments/upload", params=params, files={"file": (name, io.BytesIO(data), mime)})


def test_upload_serve_list_and_delete_attachment(admin, anon, space):
    page = create_page(admin, space["id"], "With files")
    r = upload(admin, space["id"], "../../etc/pic.png", PNG, "image/png", page["id"])
    assert r.status_code == 200, r.text
    att = r.json()
    assert att["filename"] == "pic.png" and att["size_bytes"] == len(PNG) and att["page_id"] == page["id"]

    # public space: anonymous can fetch bytes, images render inline
    f = anon.get(f"/api/attachments/{att['id']}/file")
    assert f.status_code == 200 and f.content == PNG
    assert f.headers["content-type"] == "image/png"
    assert f.headers["content-disposition"].startswith("inline")
    assert f.headers["x-content-type-options"] == "nosniff"

    assert [a["id"] for a in anon.get(f"/api/attachments/page/{page['id']}/list").json()] == [att["id"]]

    assert admin.delete(f"/api/attachments/{att['id']}").status_code == 204
    assert admin.get(f"/api/attachments/{att['id']}/file").status_code == 404


def test_risky_types_download_instead_of_rendering(admin, space):
    att = upload(admin, space["id"], "x.svg", b"<svg onload=alert(1)/>", "image/svg+xml").json()
    f = admin.get(f"/api/attachments/{att['id']}/file")
    assert f.headers["content-disposition"].startswith("attachment")
    assert f.headers["content-type"] == "application/octet-stream"


def test_identical_upload_shares_storage_but_deleting_one_keeps_the_file(admin, space):
    a = upload(admin, space["id"], "a.png", PNG, "image/png").json()
    b = upload(admin, space["id"], "b.png", PNG, "image/png").json()
    assert a["id"] != b["id"] and a["url"] == b["url"]
    assert admin.delete(f"/api/attachments/{a['id']}").status_code == 204
    assert admin.get(f"/api/attachments/{b['id']}/file").content == PNG


def test_upload_requires_write_access_and_valid_input(admin, anon, private_space, space):
    reader = make_user()
    add_member(private_space["id"], reader, "read")
    assert upload(reader, private_space["id"], "a.png", PNG, "image/png").status_code == 403
    assert upload(anon, space["id"], "a.png", PNG, "image/png").status_code == 401
    assert upload(admin, space["id"], "empty.txt", b"", "text/plain").status_code == 400
    other = create_page(admin, private_space["id"], "Elsewhere")
    assert upload(admin, space["id"], "a.png", PNG, "image/png", other["id"]).status_code == 404


def test_private_space_attachment_is_not_public(admin, anon, private_space):
    att = upload(admin, private_space["id"], "s.png", PNG, "image/png").json()
    assert anon.get(f"/api/attachments/{att['id']}/file").status_code == 401
    assert make_user().get(f"/api/attachments/{att['id']}/file").status_code == 403


def test_oversized_upload_is_rejected(admin, space, monkeypatch):
    from app.routers import attachments
    monkeypatch.setattr(attachments, "MAX_UPLOAD_BYTES", 10)
    assert upload(admin, space["id"], "big.txt", b"x" * 11, "text/plain").status_code == 413


# ------------------------------------------------------------- space lookup

def test_space_by_key_reports_edit_rights(admin, anon, space, private_space):
    reader = make_user()
    add_member(private_space["id"], reader, "read")
    editor = make_user()
    add_member(private_space["id"], editor, "edit")

    r = anon.get(f"/api/spaces/by-key/{space['key']}")
    assert r.status_code == 200 and r.json()["can_edit"] is False
    assert admin.get(f"/api/spaces/by-key/{space['key']}").json()["can_edit"] is True

    assert anon.get(f"/api/spaces/by-key/{private_space['key']}").status_code == 401
    assert reader.get(f"/api/spaces/by-key/{private_space['key']}").json()["can_edit"] is False
    assert editor.get(f"/api/spaces/by-key/{private_space['key']}").json()["can_edit"] is True
    assert make_user().get(f"/api/spaces/by-key/{private_space['key']}").status_code == 403
    assert anon.get("/api/spaces/by-key/nope-nope").status_code == 404


def test_archived_pages_are_only_visible_to_editors(admin, anon, space):
    page = create_page(admin, space["id"], "Old news")
    assert admin.patch(f"/api/pages/{page['id']}", json={"is_archived": True}).status_code == 200

    assert admin.get(f"/api/pages/{page['id']}").status_code == 200      # editors can still open it
    assert admin.get(f"/api/pages/{page['id']}/versions").status_code == 200
    assert anon.get(f"/api/pages/{page['id']}").status_code == 404       # readers cannot
    assert anon.get(f"/api/pages/{page['id']}/versions").status_code == 404
    assert admin.patch(f"/api/pages/{page['id']}", json={"is_archived": False}).status_code == 200
    assert anon.get(f"/api/pages/{page['id']}").status_code == 200


def test_tree_hides_archived_pages_from_readers_and_reports_children(admin, anon, space):
    sid = space["id"]
    parent = create_page(admin, sid, "Parent")
    child = create_page(admin, sid, "Child", parent_id=node_of(admin, sid, parent["id"])["id"])
    secret = create_page(admin, sid, "Hidden away")
    admin.patch(f"/api/pages/{secret['id']}", json={"is_archived": True})

    admin_nodes = {n["page_id"]: n for n in admin.get(f"/api/tree/space/{sid}").json() if n["page_id"]}
    assert admin_nodes[secret["id"]]["is_archived"] is True
    assert admin_nodes[parent["id"]]["has_children"] is True
    assert admin_nodes[child["id"]]["has_children"] is False

    anon_nodes = {n["page_id"]: n for n in anon.get(f"/api/tree/space/{sid}").json() if n["page_id"]}
    assert secret["id"] not in anon_nodes
    assert {parent["id"], child["id"]} <= set(anon_nodes)


# ------------------------------------------------- favorites, activity, history

def test_favorites_add_list_remove_and_access(admin, anon, space, private_space):
    page = create_page(admin, space["id"], "Star me")
    hidden = create_page(admin, private_space["id"], "Private star")
    reader = make_user()

    assert anon.get("/api/pages/favorites/me").status_code == 401
    assert reader.put(f"/api/pages/{page['id']}/favorite").status_code == 204
    assert reader.put(f"/api/pages/{page['id']}/favorite").status_code == 204  # idempotent
    assert reader.put(f"/api/pages/{hidden['id']}/favorite").status_code == 403  # no access

    favs = reader.get("/api/pages/favorites/me").json()
    assert [f["page_id"] for f in favs] == [page["id"]]
    assert favs[0]["space_key"] == space["key"]

    assert reader.delete(f"/api/pages/{page['id']}/favorite").status_code == 204
    assert reader.delete(f"/api/pages/{page['id']}/favorite").status_code == 204  # idempotent
    assert reader.get("/api/pages/favorites/me").json() == []


def test_favorites_disappear_when_page_is_archived_or_access_lost(admin, space):
    page = create_page(admin, space["id"], "Will go")
    admin.put(f"/api/pages/{page['id']}/favorite")
    assert len(admin.get("/api/pages/favorites/me").json()) == 1
    admin.patch(f"/api/pages/{page['id']}", json={"is_archived": True})
    assert admin.get("/api/pages/favorites/me").json() == []


def test_versions_carry_author_names(admin, space):
    page = create_page(admin, space["id"], "History")
    admin.put(f"/api/pages/{page['id']}/draft",
              json={"draft_json": {"type": "doc", "content": []}, "draft_text": "x"})
    version = admin.post(f"/api/pages/{page['id']}/publish", json={}).json()
    assert version["author_name"]
    listed = admin.get(f"/api/pages/{page['id']}/versions").json()
    assert listed[0]["author_name"] == version["author_name"]


def test_space_activity_feed(admin, anon, space, private_space):
    page = create_page(admin, space["id"], "Feed page")
    admin.put(f"/api/pages/{page['id']}/draft",
              json={"draft_json": {"type": "doc", "content": []}, "draft_text": "x"})
    admin.post(f"/api/pages/{page['id']}/publish", json={"notes": "n"})
    draft_only = create_page(admin, space["id"], "Draft only")

    events = anon.get(f"/api/spaces/{space['id']}/activity").json()
    kinds = [(e["type"], e["page_id"]) for e in events]
    assert ("published", page["id"]) in kinds
    assert ("created", page["id"]) in kinds
    assert ("created", draft_only["id"]) in kinds
    assert all(e["type"] != "published" or e["page_id"] != draft_only["id"] for e in events)
    assert [e["at"] for e in events] == sorted((e["at"] for e in events), reverse=True)
    assert events[0]["user_name"]

    assert len(anon.get(f"/api/spaces/{space['id']}/activity?limit=1").json()) == 1
    assert anon.get(f"/api/spaces/{private_space['id']}/activity").status_code == 401

    admin.patch(f"/api/pages/{page['id']}", json={"is_archived": True})
    assert all(e["page_id"] != page["id"] for e in anon.get(f"/api/spaces/{space['id']}/activity").json())

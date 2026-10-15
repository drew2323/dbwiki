# Quick Start Guide

**Status:** All planned CMS features are implemented (see [CMS_IMPLEMENTATION_STATUS.md](CMS_IMPLEMENTATION_STATUS.md)).
**Updated:** October 2026

---

## 🚀 Getting started in 5 minutes

### 1. Database
```bash
cd backend
cp .env.example .env        # set DATABASE_URL, JWT_SECRET_KEY, Google OAuth keys
alembic upgrade head        # expected head: f1a2b3c4d5e6
```

### 2. Backend (port 8000)
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```
API docs: http://localhost:8000/docs

### 3. Frontend (port 5173)
```bash
cd frontend
npm install
npm run dev
```

### 4. First steps in the app
1. Register at `/auth/register` and log in.
2. Make yourself superuser: `UPDATE users SET is_superuser = true WHERE email = '...';`
3. Create a space in `/admin/spaces` (tick *public* to see it on the landing page).
4. Open `/<space-key>`, create a page (try a template), edit, publish, press `Ctrl/Cmd+K`.

---

## 🧪 Tests
```bash
cd backend && pip install -r requirements-dev.txt && pytest tests   # API + access control
cd frontend && npm test                                             # renderer + diff unit tests
```

---

## 🔑 Roles and access
| Who | Read | Write |
|---|---|---|
| Anonymous | public spaces (published content only) | - |
| Member `read` | spaces they belong to | - |
| Member `edit` / `admin`, space creator, superuser | yes (incl. drafts, archived pages) | yes |

The frontend asks `GET /api/spaces/by-key/{key}` for `can_edit`.

---

## 📂 Important file locations

### Backend
```
backend/app/
├── dependencies/access.py     # require_space_read / require_space_write
├── routers/pages.py           # pages, drafts, versions, duplicate, favorites, search
├── routers/tree.py            # tree + moves
├── routers/attachments.py     # upload, serve, delete
├── routers/spaces.py          # spaces, by-key lookup, activity feed
├── crud/                      # DB logic (pages.py has slug + search logic)
├── utils/page_templates.py    # built-in page templates
└── models/                    # SQLAlchemy models + Pydantic schemas
backend/tests/                 # pytest API tests
```

### Frontend
```
frontend/src/
├── views/cms/                 # Space.vue, SpaceHome.vue, PageView.vue
├── components/cms/            # PageTree, CreatePageDialog, SearchPalette,
│                              # PageAttachments, VersionDiffDialog, TiptapEditor, ...
├── composables/               # useAutosave, useFavorites, useRecentPages, ...
├── utils/                     # renderTiptap.ts (safe HTML), diffTiptap.ts
├── stores/cmsStore.ts         # cross-component refresh signals
└── services/                  # pageService, spaceService, attachmentService
```

---

## 🔑 Key concepts

### ETag concurrency
Draft autosave sends the last known ETag; on mismatch the API answers `409` and the editor offers a refresh.

### Gapped positioning
Tree nodes use positions 1024, 2048, ... so a node can be inserted without renumbering; the API rebalances when gaps run out.

### Rendering user content
Never put page content into `v-html` without `renderTiptap()` - it escapes text and only allows
http(s)/mailto/tel/relative URLs.

---

## 🐛 Known limitations
- Search indexes the draft text, so editors find unpublished text; readers only see title matches and no snippets.
- Uploaded files live on local disk (`UPLOAD_DIR`); use object storage for multi-instance deployments.
- Optional ideas not implemented: comments, Meilisearch, real-time collaboration, export/import.

---

## 📚 Reference documentation
- [DEVELOPMENT.md](DEVELOPMENT.md), [ARCHITECTURE.md](ARCHITECTURE.md), [AUTHENTICATION.md](AUTHENTICATION.md)
- [DEPLOYMENT.md](DEPLOYMENT.md), [UI_FRAMEWORK.md](UI_FRAMEWORK.md)

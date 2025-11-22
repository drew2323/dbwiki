# Quick Start Guide - Next Development Session

**Status:** Sprint 4 Complete ✅
**Next:** Sprint 5 - Tiptap Editor
**Updated:** November 21, 2025

---

## 🚀 Getting Started in 5 Minutes

### 1. Verify Database Migration
```bash
cd backend
alembic current
# Expected: e1f2g3h4i5j6 (head)
```

If not at correct version:
```bash
alembic upgrade head
```

### 2. Start Backend
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

Visit http://localhost:8000/docs to verify API is running.

### 3. Start Frontend
```bash
cd frontend
npm run dev
```

Visit http://localhost:5173 to see the landing page.

### 4. Quick Test
1. Go to http://localhost:5173
2. Should see landing page with public spaces section
3. If no spaces, login and create one at http://localhost:5173/admin
4. Set a space to public, then verify it appears on landing page
5. Click on a public space to test viewing experience

---

## 📖 What's Working Now

### ✅ Backend (Port 8000)
- **Database:** All CMS tables created (pages, versions, tree, backlinks, attachments)
- **API Endpoints:** 25+ endpoints for pages, tree, attachments
- **Features:** ETag concurrency, full-text search, gapped positioning

**Key Endpoints:**
- `GET /api/spaces/public/discover` - Public spaces
- `GET /api/tree/space/{space_id}` - Page tree
- `GET /api/pages/{page_id}` - Page details
- `GET /api/pages/slug/{space_id}/{slug}` - Page by slug

### ✅ Frontend (Port 5173)
- **Routes:**
  - `/` - Public landing page
  - `/admin/*` - Admin dashboard (superuser only)
  - `/:spaceKey` - Space home
  - `/:spaceKey/p/:pageId-slug` - Page view

- **Features:** Page tree navigation, breadcrumbs, view pages

---

## 🎯 Sprint 5 Checklist (Next Session)

### Install Dependencies
```bash
cd frontend
npm install @tiptap/vue-3 @tiptap/starter-kit @tiptap/extension-link @tiptap/extension-image @tiptap/extension-table @tiptap/extension-code-block @tiptap/extension-heading
```

### Files to Create
1. `frontend/src/components/cms/TiptapEditor.vue` - Main editor component
2. `frontend/src/components/cms/EditorToolbar.vue` - Formatting toolbar
3. `frontend/src/composables/useAutosave.ts` - Autosave logic

### Files to Update
1. `frontend/src/views/cms/PageView.vue` - Add edit mode with Tiptap
2. `frontend/src/layout/SpaceLayout.vue` - Handle edit mode toggle

### Key Features to Implement
- ✅ Tiptap editor with basic extensions
- ✅ Autosave with 3-10s debounce
- ✅ ETag conflict detection
- ✅ Image upload (drag/paste)
- ✅ Edit/View mode toggle
- ✅ Unsaved changes warning

---

## 📂 Important File Locations

### Backend
```
backend/app/
├── routers/
│   ├── pages.py          # Page CRUD + autosave
│   ├── tree.py           # Tree operations
│   └── attachments.py    # File uploads
├── crud/
│   ├── pages.py          # Page logic
│   └── page_versions.py  # Version logic
└── models/
    ├── db_models.py      # SQLAlchemy models
    └── page.py           # Pydantic schemas
```

### Frontend
```
frontend/src/
├── views/cms/
│   ├── Space.vue         # Space wrapper
│   ├── SpaceHome.vue     # Space landing
│   └── PageView.vue      # Page display
├── components/cms/
│   └── PageTree.vue      # Tree navigation
├── layout/
│   └── SpaceLayout.vue   # 3-column layout
└── services/
    ├── pageService.ts    # Page API calls
    └── spaceService.ts   # Space API calls
```

---

## 🔑 Key Concepts

### ETag Concurrency
```typescript
// Get draft with ETag
const { draft_json, draft_etag } = await pageService.getDraft(pageId)

// Update with If-Match header
try {
  await pageService.updateDraft(pageId, content, text, draft_etag)
} catch (err) {
  if (err.response?.status === 409) {
    // Conflict - show merge UI
  }
}
```

### Gapped Positioning
```
Position values: 1024, 2048, 3072, ...
When inserting between nodes: use midpoint
When gaps < 2: trigger rebalance
```

### Tree Structure
```
Root Sentinel (page_id = null)
  ├── Page A (position: 1024)
  │   ├── Page A1 (position: 1024)
  │   └── Page A2 (position: 2048)
  └── Page B (position: 2048)
```

---

## 🐛 Known Issues

1. **Space Loading:** SpaceLayout tries public API first, should check auth
2. **Permissions:** Always checks `is_superuser`, needs proper role checking
3. **Content Rendering:** Basic HTML only, needs Tiptap renderer
4. **No Create Page UI:** Placeholder in Sprint 4, implement in Sprint 6

---

## 📚 Reference Documentation

- **Full Status:** `docs/CMS_IMPLEMENTATION_STATUS.md`
- **Project Overview:** `CLAUDE.md`
- **Architecture:** `docs/ARCHITECTURE.md`
- **API Reference:** `docs/API.md`
- **Authentication:** `docs/AUTHENTICATION.md`

---

## 💡 Tips for Development

### Debug Backend
```bash
# View logs
tail -f backend/logs/*.log

# Test API directly
curl http://localhost:8000/api/spaces/public/discover

# Check database
psql -U user -d dbwiki
\dt  # List tables
SELECT * FROM pages LIMIT 5;
```

### Debug Frontend
```javascript
// In browser console
localStorage.getItem('auth')  // Check auth state
localStorage.getItem('currentSpaceId')  // Check space
```

### Common Commands
```bash
# Backend
cd backend
alembic revision -m "description"  # Create migration
alembic upgrade head               # Run migrations
python -m uvicorn main:app --reload

# Frontend
cd frontend
npm run dev          # Start dev server
npm run build        # Build for production
npm run lint         # Lint code
```

---

## 🎨 UI/UX Notes

### PrimeVue Components Used
- Tree, Card, Button, Skeleton, Dialog, Breadcrumb
- Toast service for notifications
- Theme variables for styling

### Design Principles
- Compact, information-dense
- Professional appearance
- Consistent with PrimeVue theme
- Responsive (mobile-friendly)

---

## 📞 Need Help?

**Check these first:**
1. API docs: http://localhost:8000/docs
2. Console errors in browser DevTools
3. Network tab for API call failures
4. Backend logs for Python errors

**Common Issues:**
- **401 Unauthorized:** Check if logged in
- **404 Not Found:** Verify route exists
- **409 Conflict:** ETag mismatch, refresh page
- **500 Server Error:** Check backend logs

---

**Ready to Continue?** → Start with Sprint 5 - Tiptap Editor!

See `docs/CMS_IMPLEMENTATION_STATUS.md` for detailed Sprint 5 plan.

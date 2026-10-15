"""
Tree management API endpoints for hierarchical page organization.
Handles tree node operations with gapped positioning and circular reference protection.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.database import get_db
from app.dependencies.auth import get_current_user, get_current_user_optional
from app.dependencies.access import require_space_read, require_space_write, user_can_write_space
from app.models.db_models import User, Page
from app.models.page import TreeNodeMove, TreeNodeReorder
from app.crud import tree_nodes as tree_crud
from app.crud import pages as page_crud
from app.crud import spaces as space_crud

router = APIRouter(prefix="/api/tree", tags=["tree"])


# ============================================================================
# Response Models
# ============================================================================

class TreeNodeResponse(BaseModel):
    """Tree node with populated page info"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    space_id: str
    page_id: Optional[str] = None
    parent_id: Optional[str] = None
    position: int

    # Populated from page
    title: Optional[str] = None
    slug: Optional[str] = None
    is_archived: bool = False
    has_children: bool = False


class BreadcrumbItem(BaseModel):
    """Breadcrumb trail item"""
    id: str
    title: str
    slug: str


# ============================================================================
# Tree Retrieval Endpoints
# ============================================================================

@router.get("/space/{space_id}", response_model=List[TreeNodeResponse])
async def get_space_tree(
    space_id: str,
    parent_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get tree structure for a space.
    If parent_id is provided, returns children of that node.
    Otherwise, returns ALL nodes in the space for client-side tree building.
    """
    space = require_space_read(db, space_id, user)
    can_see_archived = bool(user and user_can_write_space(db, user, space))

    # Get ALL nodes in the space (not just root level) plus their pages in one query
    nodes = tree_crud.get_nodes_by_space(db, space_id)
    pages = {
        p.id: p for p in db.query(Page).filter(Page.space_id == space_id).all()
    }

    # Readers never see archived pages (not even their titles)
    visible = []
    for node in nodes:
        page = pages.get(node.page_id) if node.page_id else None
        if page and page.is_archived and not can_see_archived:
            continue
        visible.append((node, page))

    parents_with_children = {node.parent_id for node, _ in visible if node.parent_id}

    result = []
    for node, page in visible:
        result.append(TreeNodeResponse(
            id=node.id,
            space_id=node.space_id,
            page_id=node.page_id,
            parent_id=node.parent_id,
            position=node.position,
            title=page.title if page else None,
            slug=page.slug if page else None,
            is_archived=page.is_archived if page else False,
            has_children=node.id in parents_with_children
        ))

    return result


@router.get("/node/{node_id}", response_model=TreeNodeResponse)
async def get_tree_node(
    node_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get a specific tree node by ID.
    """
    node = tree_crud.get_node_by_id(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Tree node not found")
    require_space_read(db, node.space_id, user)

    node_data = {
        "id": node.id,
        "space_id": node.space_id,
        "page_id": node.page_id,
        "parent_id": node.parent_id,
        "position": node.position,
        "title": None,
        "slug": None,
        "is_archived": False,
        "has_children": False
    }

    if node.page_id:
        page = page_crud.get_page_by_id(db, node.page_id, include_archived=True)
        if page:
            node_data["title"] = page.title
            node_data["slug"] = page.slug
            node_data["is_archived"] = page.is_archived

    children = tree_crud.get_children(db, node.id)
    node_data["has_children"] = len(children) > 0

    return TreeNodeResponse(**node_data)


@router.get("/page/{page_id}/breadcrumb", response_model=List[BreadcrumbItem])
async def get_breadcrumb(
    page_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get breadcrumb trail for a page (all ancestors from root to page).
    """
    page = page_crud.get_page_by_id(db, page_id, include_archived=True)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    require_space_read(db, page.space_id, user)
    breadcrumb = tree_crud.get_breadcrumb(db, page_id)
    return [BreadcrumbItem(**item) for item in breadcrumb]


# ============================================================================
# Tree Manipulation Endpoints
# ============================================================================

@router.post("/node/{node_id}/move", response_model=TreeNodeResponse)
async def move_node(
    node_id: str,
    move_data: TreeNodeMove,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Move a tree node to a new parent and position.
    Includes circular reference protection.

    Returns:
        400 Bad Request if attempting to create circular reference
    """
    existing = tree_crud.get_node_by_id(db, node_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Tree node not found")
    require_space_write(db, existing.space_id, user)
    if move_data.parent_id:
        new_parent = tree_crud.get_node_by_id(db, move_data.parent_id)
        if not new_parent or new_parent.space_id != existing.space_id:
            raise HTTPException(status_code=400, detail="Parent must be a node in the same space")

    try:
        node = tree_crud.move_node(
            db=db,
            node_id=node_id,
            new_parent_id=move_data.parent_id,
            new_position=move_data.position
        )

        if not node:
            raise HTTPException(status_code=404, detail="Tree node not found")

        # Enrich response
        node_data = {
            "id": node.id,
            "space_id": node.space_id,
            "page_id": node.page_id,
            "parent_id": node.parent_id,
            "position": node.position,
            "title": None,
            "slug": None,
            "is_archived": False,
            "has_children": False
        }

        if node.page_id:
            page = page_crud.get_page_by_id(db, node.page_id, include_archived=True)
            if page:
                node_data["title"] = page.title
                node_data["slug"] = page.slug
                node_data["is_archived"] = page.is_archived

        children = tree_crud.get_children(db, node.id)
        node_data["has_children"] = len(children) > 0

        return TreeNodeResponse(**node_data)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/node/reorder", status_code=status.HTTP_200_OK)
async def reorder_nodes(
    reorder_data: TreeNodeReorder,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Batch reorder multiple nodes.
    Useful for optimistic UI updates.

    Body:
        updates: List of {id, position} objects
    """
    for update in reorder_data.updates:
        node = tree_crud.get_node_by_id(db, update["id"])
        if node:
            require_space_write(db, node.space_id, user)
            node.position = update["position"]

    db.commit()
    return {"success": True, "updated": len(reorder_data.updates)}


@router.post("/node/{node_id}/rebalance", status_code=status.HTTP_200_OK)
async def rebalance_subtree(
    node_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger position rebalancing for a node's children.
    Usually automatic but can be triggered if needed.
    """
    node = tree_crud.get_node_by_id(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Tree node not found")

    require_space_write(db, node.space_id, user)
    tree_crud.rebalance_positions(db, node_id)
    return {"success": True, "message": "Positions rebalanced"}


@router.delete("/node/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(
    node_id: str,
    delete_descendants: bool = True,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a tree node.

    Query params:
        delete_descendants: If True (default), cascade to children.
                           If False, reparent children to this node's parent.
    """
    node = tree_crud.get_node_by_id(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Tree node not found")
    require_space_write(db, node.space_id, user)
    tree_crud.delete_node(db, node_id, delete_descendants)


# ============================================================================
# Tree Utility Endpoints
# ============================================================================

@router.get("/node/{node_id}/ancestors", response_model=List[TreeNodeResponse])
async def get_ancestors(
    node_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get all ancestor nodes (parent, grandparent, etc.) up to root.
    """
    start = tree_crud.get_node_by_id(db, node_id)
    if not start:
        raise HTTPException(status_code=404, detail="Tree node not found")
    require_space_read(db, start.space_id, user)
    ancestors = tree_crud.get_ancestors(db, node_id)

    result = []
    for node in ancestors:
        node_data = {
            "id": node.id,
            "space_id": node.space_id,
            "page_id": node.page_id,
            "parent_id": node.parent_id,
            "position": node.position,
            "title": None,
            "slug": None,
            "is_archived": False,
            "has_children": False
        }

        if node.page_id:
            page = page_crud.get_page_by_id(db, node.page_id, include_archived=True)
            if page:
                node_data["title"] = page.title
                node_data["slug"] = page.slug
                node_data["is_archived"] = page.is_archived

        result.append(TreeNodeResponse(**node_data))

    return result


@router.get("/node/{node_id}/descendants", response_model=List[TreeNodeResponse])
async def get_descendants(
    node_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Get all descendant nodes (children, grandchildren, etc.).
    Returns flat list, not hierarchical.
    """
    def get_all_descendants(node_id: str, result: List = None):
        if result is None:
            result = []

        children = tree_crud.get_children(db, node_id)
        for child in children:
            node_data = {
                "id": child.id,
                "space_id": child.space_id,
                "page_id": child.page_id,
                "parent_id": child.parent_id,
                "position": child.position,
                "title": None,
                "slug": None,
                "is_archived": False,
                "has_children": False
            }

            if child.page_id:
                page = page_crud.get_page_by_id(db, child.page_id, include_archived=True)
                if page:
                    node_data["title"] = page.title
                    node_data["slug"] = page.slug
                    node_data["is_archived"] = page.is_archived

            result.append(TreeNodeResponse(**node_data))
            get_all_descendants(child.id, result)

        return result

    start = tree_crud.get_node_by_id(db, node_id)
    if not start:
        raise HTTPException(status_code=404, detail="Tree node not found")
    require_space_read(db, start.space_id, user)
    return get_all_descendants(node_id)

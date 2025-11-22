"""
Tree management API endpoints for hierarchical page organization.
Handles tree node operations with gapped positioning and circular reference protection.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.db_models import User
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
    user: User = Depends(get_current_user)
):
    """
    Get tree structure for a space.
    If parent_id is provided, returns children of that node.
    Otherwise, returns ALL nodes in the space for client-side tree building.
    """
    # Verify space exists
    space = space_crud.get_space_by_id(db, space_id)
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")

    # Get ALL nodes in the space (not just root level)
    nodes = tree_crud.get_nodes_by_space(db, space_id)

    # Enrich with page info
    result = []
    for node in nodes:
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

        # Check if node has children
        children = tree_crud.get_children(db, node.id)
        node_data["has_children"] = len(children) > 0

        result.append(TreeNodeResponse(**node_data))

    return result


@router.get("/node/{node_id}", response_model=TreeNodeResponse)
async def get_tree_node(
    node_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Get a specific tree node by ID.
    """
    node = tree_crud.get_node_by_id(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Tree node not found")

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
    user: User = Depends(get_current_user)
):
    """
    Get breadcrumb trail for a page (all ancestors from root to page).
    """
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
    success = tree_crud.delete_node(db, node_id, delete_descendants)
    if not success:
        raise HTTPException(status_code=404, detail="Tree node not found")


# ============================================================================
# Tree Utility Endpoints
# ============================================================================

@router.get("/node/{node_id}/ancestors", response_model=List[TreeNodeResponse])
async def get_ancestors(
    node_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Get all ancestor nodes (parent, grandparent, etc.) up to root.
    """
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
    user: User = Depends(get_current_user)
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

    return get_all_descendants(node_id)

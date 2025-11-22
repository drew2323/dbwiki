"""
CRUD operations for tree nodes.
Implements gapped positioning for efficient reordering.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.db_models import TreeNode, Page
from typing import Optional, List, Dict
import uuid


# Constants for gapped positioning
POSITION_GAP = 1024  # Default gap between positions
POSITION_START = 1024  # First position


def get_root_node(db: Session, space_id: str) -> Optional[TreeNode]:
    """Get the root sentinel node for a space"""
    return db.query(TreeNode).filter(
        TreeNode.space_id == space_id,
        TreeNode.page_id == None,
        TreeNode.parent_id == None
    ).first()


def create_root_node(db: Session, space_id: str) -> TreeNode:
    """Create root sentinel node for a space"""
    node = TreeNode(
        id=str(uuid.uuid4()),
        space_id=space_id,
        page_id=None,
        parent_id=None,
        position=0
    )
    db.add(node)
    db.commit()
    db.refresh(node)
    return node


def get_node_by_id(db: Session, node_id: str) -> Optional[TreeNode]:
    """Get tree node by ID"""
    return db.query(TreeNode).filter(TreeNode.id == node_id).first()


def get_node_by_page(db: Session, page_id: str) -> Optional[TreeNode]:
    """Get tree node for a specific page"""
    return db.query(TreeNode).filter(TreeNode.page_id == page_id).first()


def get_children(db: Session, parent_id: str, space_id: Optional[str] = None) -> List[TreeNode]:
    """Get all children of a node, ordered by position"""
    query = db.query(TreeNode).filter(TreeNode.parent_id == parent_id)
    if space_id:
        query = query.filter(TreeNode.space_id == space_id)
    return query.order_by(TreeNode.position).all()


def get_nodes_by_space(db: Session, space_id: str) -> List[TreeNode]:
    """Get all tree nodes in a space (excluding root sentinel)"""
    return db.query(TreeNode).filter(
        TreeNode.space_id == space_id,
        TreeNode.page_id != None  # Exclude root sentinel nodes
    ).order_by(TreeNode.position).all()


def get_tree(db: Session, space_id: str, parent_id: Optional[str] = None) -> List[TreeNode]:
    """Get tree structure for a space"""
    if parent_id is None:
        # Get root node first
        root = get_root_node(db, space_id)
        if not root:
            return []
        parent_id = root.id

    return get_children(db, parent_id, space_id)


def calculate_position(db: Session, parent_id: str, before_node_id: Optional[str] = None) -> int:
    """
    Calculate position for a new node using gapped positioning.

    Args:
        parent_id: Parent node ID
        before_node_id: Insert before this node (None = append at end)

    Returns:
        Position value
    """
    siblings = get_children(db, parent_id)

    if not siblings:
        return POSITION_START

    if before_node_id is None:
        # Append at end
        return siblings[-1].position + POSITION_GAP

    # Find position before the specified node
    for i, sibling in enumerate(siblings):
        if sibling.id == before_node_id:
            if i == 0:
                # Insert at beginning
                return siblings[0].position // 2 if siblings[0].position > 1 else siblings[0].position - POSITION_GAP
            else:
                # Insert between two nodes
                prev_pos = siblings[i - 1].position
                curr_pos = sibling.position
                gap = curr_pos - prev_pos

                if gap > 2:
                    return prev_pos + (gap // 2)
                else:
                    # No room - need to rebalance
                    return prev_pos + 1  # Will trigger rebalance

    # If not found, append
    return siblings[-1].position + POSITION_GAP


def rebalance_positions(db: Session, parent_id: str) -> None:
    """
    Rebalance positions when gaps become too small.
    Reassigns positions with proper gaps.
    """
    siblings = get_children(db, parent_id)
    for i, node in enumerate(siblings):
        node.position = POSITION_START + (i * POSITION_GAP)
    db.commit()


def create_node(
    db: Session,
    space_id: str,
    page_id: str,
    parent_id: Optional[str] = None,
    position: Optional[int] = None,
    before_node_id: Optional[str] = None
) -> TreeNode:
    """
    Create a new tree node for a page.

    Args:
        space_id: Space ID
        page_id: Page ID
        parent_id: Parent node ID (None = use root)
        position: Explicit position (None = auto-calculate)
        before_node_id: Insert before this node
    """
    # Use root as parent if not specified
    if parent_id is None:
        root = get_root_node(db, space_id)
        if not root:
            root = create_root_node(db, space_id)
        parent_id = root.id

    # Calculate position if not provided
    if position is None:
        position = calculate_position(db, parent_id, before_node_id)

    node = TreeNode(
        id=str(uuid.uuid4()),
        space_id=space_id,
        page_id=page_id,
        parent_id=parent_id,
        position=position
    )
    db.add(node)
    db.commit()
    db.refresh(node)

    # Check if rebalancing needed
    siblings = get_children(db, parent_id)
    if len(siblings) > 1:
        positions = [s.position for s in siblings]
        min_gap = min(abs(positions[i+1] - positions[i]) for i in range(len(positions)-1))
        if min_gap < 2:
            rebalance_positions(db, parent_id)
            db.refresh(node)

    return node


def move_node(
    db: Session,
    node_id: str,
    new_parent_id: Optional[str],
    new_position: int
) -> Optional[TreeNode]:
    """
    Move a node to a new parent and position.
    Includes circular reference check.
    """
    node = get_node_by_id(db, node_id)
    if not node:
        return None

    # Check for circular reference (can't move node under itself or its descendants)
    if new_parent_id:
        current = get_node_by_id(db, new_parent_id)
        while current:
            if current.id == node_id:
                raise ValueError("Cannot move node under itself or its descendants")
            current = get_node_by_id(db, current.parent_id) if current.parent_id else None

    # Use root if new_parent_id is None
    if new_parent_id is None:
        root = get_root_node(db, node.space_id)
        new_parent_id = root.id if root else None

    # Update node
    node.parent_id = new_parent_id
    node.position = new_position

    db.commit()
    db.refresh(node)

    # Rebalance new parent's children if needed
    if new_parent_id:
        siblings = get_children(db, new_parent_id)
        if len(siblings) > 1:
            positions = [s.position for s in siblings]
            if len(positions) > 1:
                min_gap = min(abs(positions[i+1] - positions[i]) for i in range(len(positions)-1))
                if min_gap < 2:
                    rebalance_positions(db, new_parent_id)
                    db.refresh(node)

    return node


def delete_node(db: Session, node_id: str, delete_descendants: bool = True) -> bool:
    """
    Delete a tree node.

    Args:
        node_id: Node ID to delete
        delete_descendants: If True, cascade to children (default). If False, reparent children.
    """
    node = get_node_by_id(db, node_id)
    if not node:
        return False

    if not delete_descendants:
        # Reparent children to this node's parent
        children = get_children(db, node_id)
        for child in children:
            child.parent_id = node.parent_id
        db.commit()

    # Delete node (cascade will handle descendants if delete_descendants=True)
    db.delete(node)
    db.commit()
    return True


def get_ancestors(db: Session, node_id: str) -> List[TreeNode]:
    """Get all ancestors of a node (bottom-up)"""
    ancestors = []
    current = get_node_by_id(db, node_id)

    while current and current.parent_id:
        parent = get_node_by_id(db, current.parent_id)
        if parent and parent.page_id:  # Exclude root sentinel
            ancestors.append(parent)
        current = parent

    return ancestors


def get_breadcrumb(db: Session, page_id: str) -> List[Dict[str, str]]:
    """Get breadcrumb trail for a page"""
    node = get_node_by_page(db, page_id)
    if not node:
        return []

    ancestors = get_ancestors(db, node.id)
    breadcrumb = []

    for ancestor in reversed(ancestors):
        if ancestor.page_id:
            page = db.query(Page).filter(Page.id == ancestor.page_id).first()
            if page:
                breadcrumb.append({
                    'id': page.id,
                    'title': page.title,
                    'slug': page.slug
                })

    # Add current page
    page = db.query(Page).filter(Page.id == page_id).first()
    if page:
        breadcrumb.append({
            'id': page.id,
            'title': page.title,
            'slug': page.slug
        })

    return breadcrumb

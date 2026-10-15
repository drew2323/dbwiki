"""
Built-in page templates (Tiptap JSON) used when creating a page.
"""
from copy import deepcopy
from typing import Any, Dict, List, Optional


def _text(t: str) -> Dict[str, Any]:
    return {"type": "text", "text": t}


def _h(level: int, t: str) -> Dict[str, Any]:
    return {"type": "heading", "attrs": {"level": level}, "content": [_text(t)]}


def _p(t: str = "") -> Dict[str, Any]:
    return {"type": "paragraph", "content": [_text(t)]} if t else {"type": "paragraph"}


def _bullets(items: List[str]) -> Dict[str, Any]:
    return {
        "type": "bulletList",
        "content": [{"type": "listItem", "content": [_p(i)]} for i in items],
    }


def _doc(*nodes: Dict[str, Any]) -> Dict[str, Any]:
    return {"type": "doc", "content": list(nodes)}


def _plain(node: Any) -> str:
    """Flatten Tiptap JSON to text for search indexing."""
    parts: List[str] = []

    def walk(n: Any) -> None:
        if isinstance(n, dict):
            if n.get("type") == "text":
                parts.append(n.get("text", ""))
            for c in n.get("content", []) or []:
                walk(c)
        elif isinstance(n, list):
            for c in n:
                walk(c)

    walk(node)
    return " ".join(p for p in parts if p).strip()


TEMPLATES: Dict[str, Dict[str, Any]] = {
    "blank": {
        "name": "Blank page",
        "description": "Start from an empty page",
        "icon": "pi pi-file",
        "content": None,
    },
    "meeting-notes": {
        "name": "Meeting notes",
        "description": "Agenda, discussion and action items",
        "icon": "pi pi-users",
        "content": _doc(
            _h(2, "Attendees"), _bullets(["Name"]),
            _h(2, "Agenda"), _bullets(["Topic"]),
            _h(2, "Discussion"), _p(),
            _h(2, "Action items"), _bullets(["Owner - task - due date"]),
        ),
    },
    "how-to": {
        "name": "How-to guide",
        "description": "Step by step instructions",
        "icon": "pi pi-list-check",
        "content": _doc(
            _h(2, "Overview"), _p("What does this guide help you do?"),
            _h(2, "Prerequisites"), _bullets(["Requirement"]),
            _h(2, "Steps"),
            {"type": "orderedList", "content": [
                {"type": "listItem", "content": [_p("First step")]},
            ]},
            _h(2, "Troubleshooting"), _p(),
        ),
    },
    "decision-record": {
        "name": "Decision record",
        "description": "Context, options and the decision taken",
        "icon": "pi pi-check-square",
        "content": _doc(
            _h(2, "Context"), _p("What is the problem or situation?"),
            _h(2, "Options considered"), _bullets(["Option A", "Option B"]),
            _h(2, "Decision"), _p(),
            _h(2, "Consequences"), _p(),
        ),
    },
    "research-note": {
        "name": "Research note",
        "description": "Hypothesis, method, results and next steps",
        "icon": "pi pi-chart-line",
        "content": _doc(
            _h(2, "Hypothesis"), _p(),
            _h(2, "Method"), _p(),
            _h(2, "Results"), _p(),
            _h(2, "Conclusions and next steps"), _bullets(["Next step"]),
        ),
    },
}


def list_templates() -> List[Dict[str, str]]:
    return [
        {"id": tid, "name": t["name"], "description": t["description"], "icon": t["icon"]}
        for tid, t in TEMPLATES.items()
    ]


def get_template_content(template_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """Return (a copy of) the template's Tiptap JSON, or None for blank/unknown."""
    t = TEMPLATES.get(template_id or "blank")
    if not t or t["content"] is None:
        return None
    return deepcopy(t["content"])


def template_exists(template_id: str) -> bool:
    return template_id in TEMPLATES


def tiptap_plain_text(content: Any) -> str:
    return _plain(content)

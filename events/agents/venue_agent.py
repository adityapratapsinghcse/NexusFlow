import json
from datetime import datetime
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from decouple import config


# ── 1. STATE ─────────────────────────────────────────────────────
# Everything the agent carries between steps.
class VenueState(TypedDict):
    event_name:        str
    event_description: str
    expected_crowd:    int
    start_dt:          str
    end_dt:            str
    is_night_event:    bool
    all_venues:        List[dict]
    free_venues:       List[dict]
    warnings:          List[str]
    selected_venue_id: Optional[int]
    ai_reason:         str


# ── 2. NODES ─────────────────────────────────────────────────────
# Each node is one step the agent executes.
# Nodes only import Django models inside themselves — safe for Django ORM.

def node_fetch_venues(state: VenueState) -> VenueState:
    """Agent step 1: Fetch all venues big enough for the crowd."""
    from events.models import Venue
    venues = list(
        Venue.objects.filter(
            capacity__gte=state['expected_crowd'],
            is_active=True
        ).values('id', 'name', 'capacity', 'location')
    )
    state['all_venues'] = venues
    return state


def node_check_clashes(state: VenueState) -> VenueState:
    """Agent step 2: Remove venues with time clashes."""
    from events.models import Event
    from django.utils import timezone
    start = datetime.fromisoformat(state['start_dt'])
    end = datetime.fromisoformat(state['end_dt'])

    if timezone.is_naive(start):
        start = timezone.make_aware(start)

    if timezone.is_naive(end):
        end = timezone.make_aware(end)

    free = []
    for v in state['all_venues']:
        clash = Event.objects.filter(
            venue_id=v['id'],
            start_datetime__lt=end,
            end_datetime__gt=start
        ).exists()
        if not clash:
            free.append(v)

    state['free_venues'] = free

    if not free:
        state['warnings'].append("No venues available for this time slot.")

    return state


def node_apply_night_policy(state: VenueState) -> VenueState:
    """Agent step 3 (conditional): Only runs for night events.
    Adds HOD warning and removes outdoor venues."""
    state['warnings'].append(
        "Night event: HOD approval required before publishing passes."
    )
    state['free_venues'] = [
        v for v in state['free_venues']
        if 'outdoor' not in v.get('location', '').lower()
    ]
    if not state['free_venues']:
        state['warnings'].append("No indoor venues free for this night slot.")
    return state


def node_ai_pick_venue(state: VenueState) -> VenueState:
    """Agent step 4: LLM reasons over options and picks the best one."""
    if not state['free_venues']:
        state['selected_venue_id'] = None
        state['ai_reason'] = "No venues available after clash and policy checks."
        return state

    llm = ChatGroq(
        model="llama-3.1-8b-instant",
        api_key= config("GROQ_API_KEY"),
        temperature=0
    )

    venue_list = "\n".join([
        f"ID:{v['id']} | {v['name']} | Capacity:{v['capacity']} | {v['location']}"
        for v in state['free_venues']
    ])

    prompt = f"""You are a venue scheduling assistant for a college events platform.

Event: {state['event_name']}
Description: {state['event_description'][:200]}
Expected crowd: {state['expected_crowd']} students
Night event: {state['is_night_event']}
Active warnings: {state['warnings']}

Available venues (already checked for time clashes):
{venue_list}

Pick the BEST venue. Rules:
- Prefer the smallest venue that fits the crowd (efficient use of space)
- Avoid oversized venues unless necessary
- For night events, prefer covered/indoor locations

Respond with ONLY valid JSON, no markdown, no explanation:
{{"venue_id": , "reason": ""}}"""

    try:
        response = llm.invoke(prompt).content.strip()
        parsed   = json.loads(response)
        state['selected_venue_id'] = int(parsed['venue_id'])
        state['ai_reason']         = parsed.get('reason', 'Selected by AI agent.')
    except Exception as e:
        state['selected_venue_id'] = state['free_venues'][0]['id']
        state['ai_reason']         = f"AI fallback: picked first available venue. ({e})"

    return state


# ── 3. CONDITIONAL EDGE ──────────────────────────────────────────
def route_night_policy(state: VenueState) -> str:
    """After clash check: if night event and venues exist, apply policy. Else skip to AI."""
    if state['is_night_event'] and state['free_venues']:
        return "apply_night_policy"
    return "ai_pick"


# ── 4. BUILD THE GRAPH ───────────────────────────────────────────
def build_venue_agent():
    g = StateGraph(VenueState)

    g.add_node("fetch_venues",      node_fetch_venues)
    g.add_node("check_clashes",     node_check_clashes)
    g.add_node("apply_night_policy", node_apply_night_policy)
    g.add_node("ai_pick",           node_ai_pick_venue)

    g.set_entry_point("fetch_venues")
    g.add_edge("fetch_venues", "check_clashes")
    g.add_conditional_edges("check_clashes", route_night_policy, {
        "apply_night_policy": "apply_night_policy",
        "ai_pick":            "ai_pick",
    })
    g.add_edge("apply_night_policy", "ai_pick")
    g.add_edge("ai_pick", END)

    return g.compile()


# ── 5. PUBLIC API ────────────────────────────────────────────────
_agent = None

def run_venue_agent(event_name, event_description, expected_crowd,
                    start_dt_iso, end_dt_iso, is_night_event):
    """
    Call this from schedule_event() view.
    Returns dict: {venue_id, reason, warnings}
    """
    global _agent
    if _agent is None:
        _agent = build_venue_agent()

    result = _agent.invoke({
        "event_name":        event_name,
        "event_description": event_description,
        "expected_crowd":    expected_crowd,
        "start_dt":          start_dt_iso,
        "end_dt":            end_dt_iso,
        "is_night_event":    is_night_event,
        "all_venues":        [],
        "free_venues":       [],
        "warnings":          [],
        "selected_venue_id": None,
        "ai_reason":         "",
    })

    return {
        "venue_id": result["selected_venue_id"],
        "reason":   result["ai_reason"],
        "warnings": result["warnings"],
    }
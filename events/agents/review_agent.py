import json
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from django.conf import settings


class ReviewState(TypedDict):
    event_id:          int
    event_title:       str
    event_description: str
    expected_crowd:    int
    venue_capacity:    int
    is_night_event:    bool
    date_str:          str
    organizer_name:    str
    days_until_event:  int
    duplicate_found:   bool
    risk_flags:        List[str]
    ai_summary:        str
    suggested_action:  str


def node_check_rules(state: ReviewState) -> ReviewState:
    """Step 1: Apply deterministic rule checks — no AI needed here."""
    flags = []

    if state['expected_crowd'] > state['venue_capacity']:
        flags.append(f"Crowd ({state['expected_crowd']}) exceeds venue capacity ({state['venue_capacity']}).")

    if state['expected_crowd'] > state['venue_capacity'] * 0.9:
        flags.append("Crowd is above 90% of venue capacity — safety concern.")

    if state['is_night_event']:
        flags.append("Night event — verify HOD approval and security arrangements.")

    if state['days_until_event'] < 3:
        flags.append(f"Short notice: only {state['days_until_event']} day(s) until event.")

    if state['duplicate_found']:
        flags.append("Another event with a similar title exists this week.")

    state['risk_flags'] = flags
    return state


def node_check_duplicate(state: ReviewState) -> ReviewState:
    """Step 2: Check for duplicate/similar events in the same week."""
    from events.models import Event
    from django.utils import timezone
    from datetime import timedelta
    from django.utils.dateparse import parse_date

    event_date = parse_date(state['date_str'])
    if event_date:
        window_start = event_date - timedelta(days=3)
        window_end   = event_date + timedelta(days=3)
        similar = Event.objects.filter(
            date__range=(window_start, window_end),
            status__in=['PENDING', 'APPROVED']
        ).exclude(id=state['event_id'])

        title_words = set(state['event_title'].lower().split())
        for ev in similar:
            ev_words = set(ev.title.lower().split())
            if len(title_words & ev_words) >= 2:
                state['duplicate_found'] = True
                break

    return state


def node_ai_risk_summary(state: ReviewState) -> ReviewState:
    """Step 3: LLM generates a concise risk summary for the admin."""
    llm = ChatGroq(
        model="llama3-8b-8192",
        api_key=settings.GROQ_API_KEY,
        temperature=0
    )

    flags_text = "\n".join(f"- {f}" for f in state['risk_flags']) or "No rule violations found."

    prompt = f"""You are an event review assistant for a college admin panel.

Event: {state['event_title']}
Organizer: {state['organizer_name']}
Venue: {state['venue_name']} (capacity {state['venue_capacity']})
Expected crowd: {state['expected_crowd']}
Date: {state['date_str']} ({state['days_until_event']} days away)
Night event: {state['is_night_event']}

Rule check findings:
{flags_text}

Write a 2-sentence risk summary for the admin.
Then recommend: APPROVE, APPROVE WITH CAUTION, or REJECT.

Respond ONLY with valid JSON:
{{"summary": "<2 sentences>", "recommendation": "APPROVE|APPROVE WITH CAUTION|REJECT"}}"""

    try:
        response = llm.invoke(prompt).content.strip()
        parsed   = json.loads(response)
        state['ai_summary']        = parsed.get('summary', '')
        state['suggested_action']  = parsed.get('recommendation', 'APPROVE WITH CAUTION')
    except Exception:
        state['ai_summary']       = "AI review unavailable. Check rule flags manually."
        state['suggested_action'] = "APPROVE WITH CAUTION"

    return state


def build_review_agent():
    g = StateGraph(ReviewState)

    g.add_node("check_duplicate", node_check_duplicate)
    g.add_node("check_rules",     node_check_rules)
    g.add_node("ai_summary",      node_ai_risk_summary)

    g.set_entry_point("check_duplicate")
    g.add_edge("check_duplicate", "check_rules")
    g.add_edge("check_rules",     "ai_summary")
    g.add_edge("ai_summary",      END)

    return g.compile()


_review_agent = None

def run_review_agent(event):
    """
    Call this from action_event() view for each pending event.
    Returns dict: {summary, recommendation, risk_flags}
    """
    from django.utils import timezone

    global _review_agent
    if _review_agent is None:
        _review_agent = build_review_agent()

    days_until = (event.date - timezone.now().date()).days

    result = _review_agent.invoke({
        "event_id":          event.id,
        "event_title":       event.title,
        "event_description": event.description,
        "expected_crowd":    event.expected_crowd,
        "venue_capacity":    event.venue.capacity if event.venue else 9999,
        "is_night_event":    event.night_event_warning,
        "date_str":          str(event.date),
        "organizer_name":    event.organizer.get_full_name(),
        "days_until_event":  max(days_until, 0),
        "duplicate_found":   False,
        "risk_flags":        [],
        "ai_summary":        "",
        "suggested_action":  "",
    })

    return {
        "summary":        result["ai_summary"],
        "recommendation": result["suggested_action"],
        "risk_flags":     result["risk_flags"],
    }
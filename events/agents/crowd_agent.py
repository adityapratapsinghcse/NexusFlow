from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from django.conf import settings


# ---------------- STATE ----------------
class CrowdState(TypedDict):

    event_title: str
    event_description: str

    predicted_crowd: int
    confidence: str
    reason: str


# ---------------- NODE ----------------
def node_analyze_history(state: CrowdState):

    from events.models import Event, EventRegistration
    from django.db.models import Count, Avg
    
    title = state['event_title'].lower()

    # Historical analytics
    past_events = Event.objects.filter(
        status='APPROVED'
    )

    total_events = past_events.count()

    if total_events == 0:

        state['predicted_crowd'] = 50
        state['confidence'] = "LOW"
        state['reason'] = "No historical event data available."

        return state

    # Average registrations
    avg_registrations = EventRegistration.objects.values(
        'event'
    ).annotate(
        total=Count('id')
    ).aggregate(
        avg=Avg('total')
    )['avg']

    avg_registrations = int(avg_registrations or 50)

    # Keyword boosts
    high_keywords = [
        'hackathon',
        'concert',
        'dance',
        'dj',
        'coding',
        'fest'
    ]

    predicted = avg_registrations

    for word in high_keywords:

        if word in title:
            predicted += 75

    predicted = max(predicted, 30)

    llm = ChatGroq(
        model="llama3-8b-8192",
        api_key=settings.GROQ_API_KEY,
        temperature=0
    )

    prompt = f"""
    Event Title:
    {state['event_title']}

    Description:
    {state['event_description']}

    Historical Average Crowd:
    {avg_registrations}

    Predicted Crowd:
    {predicted}

    Explain prediction briefly.
    Also give confidence:
    LOW, MEDIUM, or HIGH.

    Respond ONLY JSON:
    {{
        "reason": "",
        "confidence": ""
    }}
    """

    try:

        import json

        response = llm.invoke(prompt).content.strip()

        parsed = json.loads(response)

        state['predicted_crowd'] = predicted
        state['reason'] = parsed.get('reason', '')
        state['confidence'] = parsed.get('confidence', 'MEDIUM')

    except Exception:

        state['predicted_crowd'] = predicted
        state['reason'] = "Prediction generated using historical event registrations."
        state['confidence'] = "MEDIUM"

    return state


# ---------------- GRAPH ----------------
def build_crowd_agent():

    g = StateGraph(CrowdState)

    g.add_node(
        "analyze_history",
        node_analyze_history
    )

    g.set_entry_point("analyze_history")

    g.add_edge("analyze_history", END)

    return g.compile()


_agent = None


# ---------------- PUBLIC API ----------------
def run_crowd_agent(
    event_title,
    event_description
):

    global _agent

    if _agent is None:
        _agent = build_crowd_agent()

    result = _agent.invoke({

        "event_title": event_title,
        "event_description": event_description,

        "predicted_crowd": 0,
        "confidence": "",
        "reason": "",
    })

    return result

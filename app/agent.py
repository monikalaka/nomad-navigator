# ruff: noqa
import datetime
import json
import re
from typing import Any, AsyncGenerator

import sys
from app.config import config
from google.adk.agents import LlmAgent
from google.adk.apps import App, ResumabilityConfig
from google.adk.events.event import Event
from google.adk.events.request_input import RequestInput
from google.adk.agents.context import Context
from google.adk.tools import AgentTool
from google.adk.workflow import Workflow, START, node, Edge
from google.genai import types
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

# ---------------------------------------------------------
# Local MCP Server Config & Toolset
# ---------------------------------------------------------

python_executable = sys.executable

mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=python_executable,
            args=["-m", "app.mcp_server"],
        ),
    ),
)

# ---------------------------------------------------------
# Specialized Sub-Agents
# ---------------------------------------------------------

itinerary_planner = LlmAgent(
    name="itinerary_planner",
    model=config.model,
    instruction="""You are a professional travel itinerary planner.
Given a traveler's destination, duration, and interests, create a detailed day-by-day itinerary.
For each day, suggest distinct morning, afternoon, and evening activities, and local culinary options.
Use your get_attractions and get_weather_forecast tools to research the destination.""",
    description="Generates detailed day-by-day travel itineraries.",
    tools=[mcp_toolset],
)

logistics_coordinator = LlmAgent(
    name="logistics_coordinator",
    model=config.model,
    instruction="""You are an expert travel logistics advisor.
Given a travel destination or itinerary, provide advice on transportation options (public transit, walking, taxi), estimated transit costs, packing recommendations based on climate, and crucial local customs or safety tips.
Use your calculate_transit_time and get_local_tips tools to verify logistics.""",
    description="Provides transportation, weather, packing, and local logistics advice.",
    tools=[mcp_toolset],
)

# ---------------------------------------------------------
# Orchestrator Agent
# ---------------------------------------------------------

travel_orchestrator = LlmAgent(
    name="travel_orchestrator",
    model=config.model,
    instruction="""You are the lead travel concierge of Nomad Navigator.
Your role is to orchestrate the creation of a seamless, premium travel plan.
You must use your tools:
1. Call itinerary_planner to create a day-by-day travel plan.
2. Call logistics_coordinator to get transportation and local tips for that travel plan.
Then, synthesize their responses into a single cohesive, highly polished travel guide.
Do not output raw tool responses; present a unified, well-structured guide.""",
    tools=[AgentTool(itinerary_planner), AgentTool(logistics_coordinator)],
)

# ---------------------------------------------------------
# Security & Safety Logic
# ---------------------------------------------------------

def scrub_pii(text: str) -> str:
    # Email
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[REDACTED_EMAIL]', text)
    # Phone
    text = re.sub(r'\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}', '[REDACTED_PHONE]', text)
    # Passport
    text = re.sub(r'\b[A-Z]{1,2}\d{7,8}\b', '[REDACTED_PASSPORT]', text)
    return text

@node
def security_checkpoint(ctx: Context, node_input: types.Content) -> Event:
    text = ""
    if hasattr(node_input, "parts") and node_input.parts:
        text = "".join([p.text for p in node_input.parts if p.text])
    elif isinstance(node_input, str):
        text = node_input
    
    # PII Check
    scrubbed_text = scrub_pii(text)
    pii_detected = (scrubbed_text != text)
    
    # Prompt Injection Check
    injection_keywords = ["ignore previous instructions", "system prompt", "override instructions", "jailbreak", "dan mode"]
    injection_detected = any(kw in text.lower() for kw in injection_keywords)
    
    # Sanctioned / dangerous destinations check
    dangerous_destinations = ["north korea", "syria", "iran", "yemen", "somalia", "afghanistan"]
    destination_violation = any(dest in text.lower() for dest in dangerous_destinations)
    
    severity = "INFO"
    decision = "safe"
    
    if injection_detected:
        severity = "CRITICAL"
        decision = "SECURITY_EVENT"
    elif destination_violation:
        severity = "WARNING"
        decision = "SECURITY_EVENT"
        
    audit_log = {
        "timestamp": datetime.datetime.now().isoformat(),
        "event": "security_checkpoint",
        "pii_detected": pii_detected,
        "injection_detected": injection_detected,
        "destination_violation": destination_violation,
        "severity": severity,
        "decision": decision
    }
    
    # Print structured JSON audit log
    print(f"AUDIT_LOG: {json.dumps(audit_log)}")
    
    # Store in context state
    ctx.state["scrubbed_input"] = scrubbed_text
    ctx.state["security_check_passed"] = (decision == "safe")
    
    if decision == "SECURITY_EVENT":
        return Event(output="Security Check Failed", route="SECURITY_EVENT", state={"security_failed": True})
    else:
        return Event(output=scrubbed_text, route="safe")

@node
def security_alert(ctx: Context, node_input: str) -> Event:
    alert_msg = "⚠️ Security Event Triggered: Your request was flagged and blocked by safety filters."
    yield Event(content=types.Content(role="model", parts=[types.Part.from_text(text=alert_msg)]))
    yield Event(output=alert_msg)

# ---------------------------------------------------------
# Human-in-the-Loop Node
# ---------------------------------------------------------

@node(rerun_on_resume=True)
async def human_review(ctx: Context, node_input: Any) -> AsyncGenerator[Event, None]:
    if ctx.resume_inputs and "approve_trip" in ctx.resume_inputs:
        user_response = ctx.resume_inputs["approve_trip"]
        if "approve" in user_response.lower() or "yes" in user_response.lower():
            yield Event(output=node_input, state={"approved": True})
        else:
            yield Event(output="Trip planning was cancelled by user.", state={"approved": False})
    else:
        msg = "✋ **Nomad Navigator Approval Gate**:\n\nPlease review the travel plan. Reply with **'approve'** to finalize and finalize your itinerary, or **'cancel'** to abort."
        yield RequestInput(
            interrupt_id="approve_trip",
            message=msg
        )

# ---------------------------------------------------------
# Final Output Node
# ---------------------------------------------------------

@node
def final_output(ctx: Context, node_input: Any) -> Event:
    if ctx.state.get("approved") is False:
        msg = "❌ Trip planning was cancelled."
        yield Event(content=types.Content(role="model", parts=[types.Part.from_text(text=msg)]))
        yield Event(output=msg)
        return
        
    guide_text = ""
    if hasattr(node_input, "parts") and node_input.parts:
        guide_text = "".join([p.text for p in node_input.parts if p.text])
    elif isinstance(node_input, str):
        guide_text = node_input
        
    prefix = "🎉 **Your Premium Nomad Navigator Travel Guide is ready!**\n\n"
    full_display = prefix + guide_text
    
    yield Event(content=types.Content(role="model", parts=[types.Part.from_text(text=full_display)]))
    yield Event(output=guide_text)

# ---------------------------------------------------------
# Workflow Definitions & Routing (Graph)
# ---------------------------------------------------------

root_agent = Workflow(
    name="nomad_navigator_workflow",
    edges=[
        Edge(from_node=START, to_node=security_checkpoint),
        Edge(from_node=security_checkpoint, to_node=travel_orchestrator, route="safe"),
        Edge(from_node=security_checkpoint, to_node=security_alert, route="SECURITY_EVENT"),
        Edge(from_node=travel_orchestrator, to_node=human_review),
        Edge(from_node=human_review, to_node=final_output),
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
    resumability_config=ResumabilityConfig(is_resumable=True)
)

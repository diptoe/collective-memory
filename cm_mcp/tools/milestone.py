"""
Milestone Tools

MCP tools for recording milestones during work sessions - progress tracking with metrics.
"""

import mcp.types as types
from typing import Any
from datetime import datetime, timezone

from .utils import _make_request


# ============================================================
# TOOL DEFINITIONS
# ============================================================

TOOL_DEFINITIONS = [
    types.Tool(
        name="update_milestone",
        description="""Update metrics on the current active milestone (status="started").

USE THIS WHEN: You want to track running metrics during an active milestone before completing it.

IMPORTANT: This tool updates metrics on the CURRENT milestone (the one with status="started").
It does NOT change the milestone status. Use `record_milestone` with status="completed" to finish.

This allows you to:
- Track progress incrementally (files touched, lines changed) as you work
- Update metrics periodically without waiting until completion
- Provide real-time visibility into work progress

AUTO-CAPTURE METRICS (incremental or cumulative):
- files_touched: Number of files touched so far
- lines_added: Lines of code added so far
- lines_removed: Lines of code removed so far
- commits_made: Number of commits made so far

SELF-ASSESSMENT METRICS (1-5 scale, can be updated as work progresses):
- complexity_rating: 1=trivial, 5=very complex

EXAMPLES:
- {"files_touched": 5, "lines_added": 120, "lines_removed": 30}
- {"files_touched": 8, "lines_added": 250} → Update totals as work continues
- {"complexity_rating": 4} → This is turning out to be more complex than expected

RETURNS: Updated milestone with current metrics.""",
        inputSchema={
            "type": "object",
            "properties": {
                "milestone_key": {"type": "string", "description": "Optional: Specific milestone to update (defaults to current active milestone)"},
                # Auto-capture metrics
                "files_touched": {"type": "integer", "description": "Number of files touched so far"},
                "lines_added": {"type": "integer", "description": "Lines of code added so far"},
                "lines_removed": {"type": "integer", "description": "Lines of code removed so far"},
                "commits_made": {"type": "integer", "description": "Number of commits made so far"},
                # Self-assessment
                "complexity_rating": {"type": "integer", "description": "1=trivial, 5=very complex", "minimum": 1, "maximum": 5}
            }
        }
    ),
    types.Tool(
        name="record_milestone",
        description="""Record a milestone during a work session.

USE THIS WHEN: You complete or start a significant task, hit a blocker, or want to track progress.

WHEN TO RECORD MILESTONES:
- Starting a major task: status="started" with goal describing what you aim to achieve
- Completing a task: status="completed" with outcome and summary of the work
- Hitting a blocker: status="blocked" with details about what's blocking progress

WHAT IT DOES:
- For status="started": Creates a NEW 'Milestone' entity and tracks it as the current active milestone
- For status="completed"/"blocked": UPDATES the existing active milestone (if one exists), otherwise creates new
- Updates the session's activity timestamp (prevents auto-close)
- Records optional metrics (auto-capture and self-assessment)
- Updates agent's current milestone state

IMPORTANT: When completing work, this tool automatically finds and updates your active "started"
milestone rather than creating a duplicate. You don't need to track the milestone key yourself.

NARRATIVE FIELDS (use markdown):
- goal: What this milestone aims to achieve (set on "started")
- outcome: The concrete result of the work (set on "completed")
- summary: Narrative of how you collaborated with the user, key decisions, and exceptional metrics

AUTO-CAPTURE METRICS (optional):
- files_touched: Number of files touched during this milestone
- lines_added: Lines of code added
- lines_removed: Lines of code removed
- commits_made: Number of commits made

SELF-ASSESSMENT METRICS (1-5 scale, optional):
- human_guidance_level: 1=fully autonomous, 5=heavy guidance needed
- model_understanding: 1=low understanding, 5=high understanding
- model_accuracy: 1=many errors, 5=very accurate
- collaboration_rating: 1=poor collaboration, 5=excellent
- complexity_rating: 1=trivial task, 5=very complex task

EXAMPLES:
- {"name": "Implementing authentication", "status": "started", "goal": "Add JWT-based auth with refresh tokens"}
- {"name": "Auth complete", "status": "completed", "outcome": "Added `/auth/login` and `/auth/refresh` endpoints", "summary": "User requested JWT auth. I proposed...", "lines_added": 150}
- {"name": "API blocked", "status": "blocked", "goal": "Integrate payment API", "summary": "Waiting for API credentials from user"}

RETURNS: Created Milestone entity details with metrics recorded.""",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "REQUIRED: Name/description of the milestone"},
                "status": {"type": "string", "description": "Milestone status: 'started', 'completed', or 'blocked' (default: 'completed')", "enum": ["started", "completed", "blocked"], "default": "completed"},
                # Narrative fields
                "goal": {"type": "string", "description": "What this milestone aims to achieve (markdown supported)"},
                "outcome": {"type": "string", "description": "The concrete result of the work (markdown supported)"},
                "summary": {"type": "string", "description": "Narrative of collaboration, key decisions, exceptional metrics (markdown supported)"},
                "properties": {"type": "object", "description": "Optional: Additional properties (e.g., blocker reason, commit SHA)"},
                "session_key": {"type": "string", "description": "Optional: Specific session (defaults to active session)"},
                # Auto-capture metrics
                "files_touched": {"type": "integer", "description": "Number of files touched during this milestone"},
                "lines_added": {"type": "integer", "description": "Lines of code added"},
                "lines_removed": {"type": "integer", "description": "Lines of code removed"},
                "commits_made": {"type": "integer", "description": "Number of commits made"},
                # Self-assessment metrics (1-5 scale)
                "human_guidance_level": {"type": "integer", "description": "1=fully autonomous, 5=heavy guidance", "minimum": 1, "maximum": 5},
                "model_understanding": {"type": "integer", "description": "1=low understanding, 5=high understanding", "minimum": 1, "maximum": 5},
                "model_accuracy": {"type": "integer", "description": "1=many errors, 5=very accurate", "minimum": 1, "maximum": 5},
                "collaboration_rating": {"type": "integer", "description": "1=poor, 5=excellent collaboration", "minimum": 1, "maximum": 5},
                "complexity_rating": {"type": "integer", "description": "1=trivial, 5=very complex", "minimum": 1, "maximum": 5}
            },
            "required": ["name"]
        }
    ),
]


# ============================================================
# TOOL IMPLEMENTATIONS
# ============================================================

async def update_milestone(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Update metrics on the current active milestone (status="started").

    Args:
        milestone_key: Optional - specific milestone to update (defaults to current active milestone)
        files_touched: Optional - number of files touched so far
        lines_added: Optional - lines of code added so far
        lines_removed: Optional - lines of code removed so far
        commits_made: Optional - number of commits made so far
        complexity_rating: Optional - 1=trivial, 5=very complex
    """
    milestone_key = arguments.get("milestone_key")

    # Collect metrics from arguments
    files_touched = arguments.get("files_touched")
    lines_added = arguments.get("lines_added")
    lines_removed = arguments.get("lines_removed")
    commits_made = arguments.get("commits_made")
    complexity_rating = arguments.get("complexity_rating")

    # Check if any metrics provided
    has_metrics = any(v is not None for v in [files_touched, lines_added, lines_removed, commits_made, complexity_rating])
    if not has_metrics:
        return [types.TextContent(type="text", text="Error: Provide at least one metric to update.")]

    # Get agent_id from session state or fall back to config
    agent_id = session_state.get("agent_id") or getattr(config, "agent_id", None)

    try:
        # If no milestone_key provided, get the current milestone from session_state
        if not milestone_key:
            current_milestone = session_state.get("current_milestone")
            if current_milestone and current_milestone.get("key"):
                milestone_key = current_milestone.get("key")
            else:
                # Try to find it from the agent's current milestone via API
                if agent_id:
                    try:
                        agent_result = await _make_request(config, "GET", f"/agents/{agent_id}", agent_id=agent_id)
                        if agent_result.get("success"):
                            agent_data = agent_result.get("data", {}).get("agent", {})
                            milestone_key = agent_data.get("current_milestone_key")
                    except Exception:
                        pass

        if not milestone_key:
            return [types.TextContent(type="text", text="No active milestone found. Start a milestone first with `record_milestone` (status='started').")]

        # Build metrics batch - these will REPLACE existing values for the same metric type
        metrics = []

        if files_touched is not None:
            metrics.append({"metric_type": "milestone_files_touched", "value": files_touched})
        if lines_added is not None:
            metrics.append({"metric_type": "milestone_lines_added", "value": lines_added})
        if lines_removed is not None:
            metrics.append({"metric_type": "milestone_lines_removed", "value": lines_removed})
        if commits_made is not None:
            metrics.append({"metric_type": "milestone_commits_made", "value": commits_made})
        if complexity_rating is not None:
            metrics.append({"metric_type": "milestone_complexity_rating", "value": complexity_rating})

        # Record metrics via batch API (this creates new records - for running totals, just use latest)
        metrics_result = await _make_request(
            config, "POST", "/metrics/batch",
            json={"entity_key": milestone_key, "metrics": metrics},
            agent_id=agent_id
        )

        if metrics_result.get("success"):
            output = "## Milestone Metrics Updated\n\n"
            output += f"**Milestone:** `{milestone_key}`\n"
            output += "\n**Updated Metrics:**\n"

            if files_touched is not None:
                output += f"- Files touched: {files_touched}\n"
            if lines_added is not None:
                output += f"- Lines added: +{lines_added}\n"
            if lines_removed is not None:
                output += f"- Lines removed: -{lines_removed}\n"
            if commits_made is not None:
                output += f"- Commits made: {commits_made}\n"
            if complexity_rating is not None:
                output += f"- Complexity rating: {complexity_rating}/5\n"

            output += "\nThese metrics are now visible in the milestone display. "
            output += "Continue updating as work progresses, then use `record_milestone` with status='completed' when done."

            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(type="text", text=f"Error: {metrics_result.get('msg', 'Failed to update metrics')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error updating milestone metrics: {str(e)}")]


async def record_milestone(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """
    Record a milestone during a work session.

    Creates a 'Milestone' entity linked to the current work session.
    Also updates the session's activity timestamp and records metrics.

    Args:
        name: Required - name/description of the milestone
        status: Optional - milestone status: 'started', 'completed', or 'blocked' (default: 'completed')
        properties: Optional - additional properties (e.g., blocker reason, commit SHA)
        session_key: Optional - specific session (defaults to active session)
        # Narrative fields (markdown supported)
        goal: Optional - what this milestone aims to achieve
        outcome: Optional - the concrete result of the work
        summary: Optional - narrative of collaboration, key decisions, exceptional metrics
        # Auto-capture metrics
        files_touched: Optional - number of files touched
        lines_added: Optional - lines of code added
        lines_removed: Optional - lines of code removed
        commits_made: Optional - number of commits made
        # Self-assessment metrics (1-5 scale)
        human_guidance_level: Optional - 1=autonomous, 5=heavy guidance
        model_understanding: Optional - 1=low, 5=high
        model_accuracy: Optional - 1=low, 5=high
        collaboration_rating: Optional - 1=poor, 5=excellent
        complexity_rating: Optional - 1=trivial, 5=very complex
    """
    name = arguments.get("name")
    status = arguments.get("status", "completed")
    properties = arguments.get("properties", {})
    session_key = arguments.get("session_key")

    # Narrative fields (markdown supported)
    goal = arguments.get("goal")
    outcome = arguments.get("outcome")
    summary = arguments.get("summary")

    # Auto-capture metrics
    files_touched = arguments.get("files_touched")
    lines_added = arguments.get("lines_added")
    lines_removed = arguments.get("lines_removed")
    commits_made = arguments.get("commits_made")

    # Self-assessment metrics (1-5 scale)
    human_guidance_level = arguments.get("human_guidance_level")
    model_understanding = arguments.get("model_understanding")
    model_accuracy = arguments.get("model_accuracy")
    collaboration_rating = arguments.get("collaboration_rating")
    complexity_rating = arguments.get("complexity_rating")

    if not name:
        return [types.TextContent(type="text", text="Error: `name` is required for the milestone.")]

    # Validate status
    valid_statuses = ["started", "completed", "blocked"]
    if status not in valid_statuses:
        return [types.TextContent(type="text", text=f"Error: `status` must be one of: {', '.join(valid_statuses)}")]

    # Get agent_id from session state or fall back to config
    agent_id = session_state.get("agent_id") or getattr(config, "agent_id", None)

    try:
        # If no session_key provided, get the active session first
        active_session = None  # Initialize for scope lookup later
        if not session_key:
            active_result = await _make_request(config, "GET", "/work-sessions/active", agent_id=agent_id)
            if active_result.get("success"):
                active_session = active_result.get("data", {}).get("session")
                if active_session:
                    session_key = active_session.get("session_key")
                else:
                    return [types.TextContent(type="text", text="No active session. Start a session first with `start_session`.")]
            else:
                return [types.TextContent(type="text", text=f"Error finding active session: {active_result.get('msg')}")]

        # Update session activity
        await _make_request(config, "POST", f"/work-sessions/{session_key}/activity", agent_id=agent_id)

        # Get scope from the active session (need to fetch it if we don't have it)
        scope_type = None
        scope_key = None
        if active_session:
            # Use team scope if session has a team, otherwise domain scope
            if active_session.get("team_key"):
                scope_type = "team"
                scope_key = active_session.get("team_key")
            elif active_session.get("domain_key"):
                scope_type = "domain"
                scope_key = active_session.get("domain_key")

        # If we didn't have active_session details, fetch the session
        if not scope_type and session_key:
            try:
                session_result = await _make_request(config, "GET", f"/work-sessions/{session_key}", agent_id=agent_id)
                if session_result.get("success"):
                    session_data = session_result.get("data", {}).get("session", {})
                    if session_data.get("team_key"):
                        scope_type = "team"
                        scope_key = session_data.get("team_key")
                    elif session_data.get("domain_key"):
                        scope_type = "domain"
                        scope_key = session_data.get("domain_key")
            except Exception:
                pass  # Fall back to no scope

        # Create the Milestone entity with proper scope and work_session_key
        # Build properties with narrative fields
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        milestone_properties = {
            **properties,
            "status": status,
        }

        # Add agent_id for tracking (uses agent_id not agent_key for flexibility)
        if agent_id:
            milestone_properties["agent_id"] = agent_id

        # Add narrative fields if provided (markdown supported)
        if goal:
            milestone_properties["goal"] = goal
        if outcome:
            milestone_properties["outcome"] = outcome
        if summary:
            milestone_properties["summary"] = summary

        # Time tracking in properties
        if status == "started":
            # Record start time - will be used for duration calculation
            milestone_properties["started_at"] = now_iso
        elif status in ("completed", "blocked"):
            # Record completion time
            milestone_properties["completed_at"] = now_iso

            # Try to get started_at from agent's current milestone for duration calculation
            current_milestone_started_at = session_state.get("current_milestone_started_at")
            if current_milestone_started_at:
                milestone_properties["started_at"] = current_milestone_started_at
                try:
                    started_dt = datetime.fromisoformat(current_milestone_started_at.replace('Z', '+00:00'))
                    duration_seconds = int((now - started_dt).total_seconds())
                    milestone_properties["duration_seconds"] = duration_seconds
                except Exception:
                    pass  # If parsing fails, skip duration
            else:
                # No tracked start time - this milestone was recorded directly as completed
                # We'll set started_at to now (0 duration) - the UI can show this was instant
                # Or if there's a prior milestone, we could use that, but for simplicity:
                milestone_properties["started_at"] = now_iso
                milestone_properties["duration_seconds"] = 0

        # Check if we should update an existing milestone instead of creating new
        existing_milestone_key = None
        if status in ("completed", "blocked"):
            # First check session_state for current milestone
            current_milestone = session_state.get("current_milestone")
            if current_milestone and current_milestone.get("key"):
                existing_milestone_key = current_milestone.get("key")
            else:
                # Try to get from agent's current milestone via API
                if agent_id:
                    try:
                        agent_result = await _make_request(config, "GET", f"/agents/{agent_id}", agent_id=agent_id)
                        if agent_result.get("success"):
                            agent_data = agent_result.get("data", {}).get("agent", {})
                            existing_milestone_key = agent_data.get("current_milestone_key")
                    except Exception:
                        pass

        # If completing/blocking and we have an existing milestone, UPDATE it
        if existing_milestone_key and status in ("completed", "blocked"):
            # Update the existing milestone entity
            update_body = {
                "name": name,  # Allow name update on completion
                "properties": milestone_properties,
            }

            result = await _make_request(config, "PUT", f"/entities/{existing_milestone_key}", json=update_body, agent_id=agent_id)

            # If update succeeded, use the existing key
            if result.get("success"):
                result["data"] = result.get("data", {})
                result["data"]["entity"] = result["data"].get("entity", {})
                result["data"]["entity"]["entity_key"] = existing_milestone_key
        else:
            # Create new milestone entity (for "started" or when no existing milestone)
            entity_body = {
                "name": name,
                "entity_type": "Milestone",
                "work_session_key": session_key,  # Top-level field, not in properties
                "properties": milestone_properties,
            }

            # Add scope if determined
            if scope_type and scope_key:
                entity_body["scope_type"] = scope_type
                entity_body["scope_key"] = scope_key

            result = await _make_request(config, "POST", "/entities", json=entity_body, agent_id=agent_id)

        if result.get("success"):
            entity = result.get("data", {}).get("entity", {})
            entity_key = entity.get("entity_key")

            # Handle milestone state tracking in session_state
            metrics_recorded = 0
            if status == "started":
                # Store current tool count for later calculation
                session_state["milestone_start_tool_count"] = session_state.get("tool_call_count", 0)

                # Store current milestone in session_state for update_milestone
                session_state["current_milestone"] = {
                    "key": entity_key,
                    "name": name,
                    "status": status,
                    "started_at": now_iso
                }

                # Store started_at for duration calculation when milestone completes
                session_state["current_milestone_started_at"] = now_iso

                # Update agent's current milestone via API
                if agent_id:
                    try:
                        await _make_request(
                            config, "PUT", f"/agents/{agent_id}/milestone",
                            json={
                                "milestone_key": entity_key,
                                "milestone_name": name,
                                "milestone_status": status
                            },
                            agent_id=agent_id
                        )
                    except Exception:
                        pass  # Non-critical

            elif status in ("completed", "blocked"):
                # Calculate tool calls during this milestone
                start_count = session_state.get("milestone_start_tool_count", 0)
                current_count = session_state.get("tool_call_count", 0)
                tool_calls_made = current_count - start_count

                # Build metrics batch
                metrics = []

                # Tool calls (auto-calculated)
                if tool_calls_made > 0:
                    metrics.append({"metric_type": "milestone_tool_calls", "value": tool_calls_made})

                # Auto-capture metrics from arguments
                if files_touched is not None:
                    metrics.append({"metric_type": "milestone_files_touched", "value": files_touched})
                if lines_added is not None:
                    metrics.append({"metric_type": "milestone_lines_added", "value": lines_added})
                if lines_removed is not None:
                    metrics.append({"metric_type": "milestone_lines_removed", "value": lines_removed})
                if commits_made is not None:
                    metrics.append({"metric_type": "milestone_commits_made", "value": commits_made})

                # Self-assessment metrics (1-5 scale)
                if human_guidance_level is not None:
                    metrics.append({"metric_type": "milestone_human_guidance", "value": human_guidance_level})
                if model_understanding is not None:
                    metrics.append({"metric_type": "milestone_model_understanding", "value": model_understanding})
                if model_accuracy is not None:
                    metrics.append({"metric_type": "milestone_model_accuracy", "value": model_accuracy})
                if collaboration_rating is not None:
                    metrics.append({"metric_type": "milestone_collaboration_rating", "value": collaboration_rating})
                if complexity_rating is not None:
                    metrics.append({"metric_type": "milestone_complexity_rating", "value": complexity_rating})

                # Record metrics via batch API
                if metrics and entity_key:
                    try:
                        metrics_result = await _make_request(
                            config, "POST", "/metrics/batch",
                            json={"entity_key": entity_key, "metrics": metrics},
                            agent_id=agent_id
                        )
                        if metrics_result.get("success"):
                            metrics_recorded = len(metrics)
                    except Exception:
                        pass  # Non-critical

                # Clear agent's current milestone
                if agent_id:
                    try:
                        await _make_request(
                            config, "PUT", f"/agents/{agent_id}/milestone",
                            json={
                                "milestone_key": None,
                                "milestone_name": None,
                                "milestone_status": None
                            },
                            agent_id=agent_id
                        )
                    except Exception:
                        pass  # Non-critical

                # Clear current milestone from session_state
                session_state["current_milestone"] = None
                session_state["current_milestone_started_at"] = None

                # Reset milestone start count
                session_state["milestone_start_tool_count"] = 0

            # Status emoji for visual feedback
            status_emoji = {"started": "🚀", "completed": "✅", "blocked": "🚫"}.get(status, "📍")
            action_word = "Updated" if existing_milestone_key else "Recorded"

            output = f"## {status_emoji} Milestone {action_word}\n\n"
            output += f"**Name:** {entity.get('name')}\n"
            output += f"**Status:** {status}\n"
            output += f"**Entity Key:** `{entity_key}`\n"
            if existing_milestone_key:
                output += f"**Action:** Updated existing started milestone\n"
            output += f"**Session:** `{session_key}`\n"

            # Show narrative fields if provided
            if goal:
                output += f"\n**Goal:** {goal[:100]}{'...' if len(goal) > 100 else ''}\n"
            if outcome:
                output += f"\n**Outcome:** {outcome[:100]}{'...' if len(outcome) > 100 else ''}\n"
            if summary:
                output += f"\n**Summary:** _{summary[:80]}{'...' if len(summary) > 80 else ''}_\n"

            if properties:
                output += f"**Properties:** {properties}\n"

            if metrics_recorded > 0:
                output += f"**Metrics Recorded:** {metrics_recorded}\n"

            output += "\nSession activity timestamp updated."

            return [types.TextContent(type="text", text=output)]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.get('msg', 'Failed to create milestone')}")]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error recording milestone: {str(e)}")]


# Legacy alias for backward compatibility
async def record_interaction(
    arguments: dict,
    config: Any,
    session_state: dict,
) -> list[types.TextContent]:
    """Legacy alias for record_milestone. Use record_milestone instead."""
    return await record_milestone(arguments, config, session_state)


# ============================================================
# TOOL HANDLERS MAPPING
# ============================================================

TOOL_HANDLERS = {
    "update_milestone": update_milestone,
    "record_milestone": record_milestone,
    # Legacy alias
    "record_interaction": record_interaction,
}

"""
Collective Memory Platform - Checkpoint Service

Agent state checkpoint and restore operations.
"""
from typing import Optional
from datetime import datetime, timezone

from api.models import Agent, db
from api.models.agent_checkpoint import AgentCheckpoint


class CheckpointService:
    """
    Service for managing agent checkpoints.

    Provides methods for saving and restoring agent state.
    """

    def __init__(self):
        self.auto_checkpoint_interval = 10  # Number of actions before auto-checkpoint

    def create_checkpoint(
        self,
        agent_key: str,
        checkpoint_type: str = 'manual',
        name: Optional[str] = None,
        description: Optional[str] = None,
        include_conversations: bool = True,
    ) -> Optional[AgentCheckpoint]:
        """
        Create a checkpoint for an agent.

        Args:
            agent_key: The agent's key
            checkpoint_type: Type of checkpoint (manual, auto, error, milestone)
            name: Optional name for the checkpoint
            description: Optional description
            include_conversations: Whether to include conversation keys

        Returns:
            The created checkpoint or None if agent not found
        """
        agent = Agent.get_by_key(agent_key)
        if not agent:
            return None

        # Build state data from agent
        state_data = self._capture_agent_state(agent)

        # Get associated conversation keys if requested
        conversation_keys = []
        if include_conversations:
            conversation_keys = self._get_agent_conversations(agent_key)

        # Create extra data
        extra_data = {
            'captured_at': datetime.now(timezone.utc).isoformat(),
            'agent_version': agent.status.get('version', '1.0') if agent.status else '1.0',
            'is_active': agent.is_active,
        }

        checkpoint = AgentCheckpoint.create_checkpoint(
            agent_key=agent_key,
            checkpoint_type=checkpoint_type,
            name=name,
            description=description,
            state_data=state_data,
            conversation_keys=conversation_keys,
            extra_data=extra_data,
        )

        return checkpoint

    def restore_checkpoint(
        self,
        agent_key: str,
        checkpoint_key: str,
        restore_status: bool = True,
    ) -> bool:
        """
        Restore an agent to a checkpoint state.

        Args:
            agent_key: The agent's key
            checkpoint_key: The checkpoint to restore from
            restore_status: Whether to restore the status field

        Returns:
            True if successful, False otherwise
        """
        agent = Agent.get_by_key(agent_key)
        if not agent:
            return False

        checkpoint = AgentCheckpoint.get_by_key(checkpoint_key)
        if not checkpoint or checkpoint.agent_key != agent_key:
            return False

        # Restore agent state
        state_data = checkpoint.state_data

        if restore_status and 'status' in state_data:
            agent.status = state_data['status']

        if 'capabilities' in state_data:
            agent.capabilities = state_data['capabilities']

        # Add restoration metadata to status
        if agent.status is None:
            agent.status = {}
        agent.status['restored_from'] = checkpoint_key
        agent.status['restored_at'] = datetime.now(timezone.utc).isoformat()

        agent.save()

        return True

    def get_checkpoints(
        self,
        agent_key: str,
        limit: int = 10,
        checkpoint_type: Optional[str] = None,
    ) -> list[AgentCheckpoint]:
        """
        Get checkpoints for an agent.

        Args:
            agent_key: The agent's key
            limit: Maximum number of checkpoints to return
            checkpoint_type: Optional type filter

        Returns:
            List of checkpoints
        """
        return AgentCheckpoint.get_by_agent(
            agent_key=agent_key,
            limit=limit,
            checkpoint_type=checkpoint_type,
        )

    def get_latest_checkpoint(self, agent_key: str) -> Optional[AgentCheckpoint]:
        """Get the most recent checkpoint for an agent."""
        return AgentCheckpoint.get_latest(agent_key)

    def create_error_checkpoint(
        self,
        agent_key: str,
        error_message: str,
        error_context: Optional[dict] = None,
    ) -> Optional[AgentCheckpoint]:
        """
        Create an error checkpoint when an agent encounters a problem.

        Args:
            agent_key: The agent's key
            error_message: Description of the error
            error_context: Additional error context

        Returns:
            The created checkpoint
        """
        return self.create_checkpoint(
            agent_key=agent_key,
            checkpoint_type='error',
            name=f"Error: {error_message[:50]}",
            description=f"Error checkpoint: {error_message}\n\nContext: {error_context}",
        )

    def cleanup_old_checkpoints(self, agent_key: str, keep_count: int = 20) -> int:
        """
        Remove old checkpoints for an agent.

        Args:
            agent_key: The agent's key
            keep_count: Number of recent checkpoints to keep

        Returns:
            Number of deleted checkpoints
        """
        return AgentCheckpoint.cleanup_old_checkpoints(agent_key, keep_count)

    def _capture_agent_state(self, agent: Agent) -> dict:
        """Capture the current state of an agent."""
        return {
            'agent_id': agent.agent_id,
            'role': agent.role,
            'capabilities': agent.capabilities,
            'status': agent.status,
            'last_heartbeat': agent.last_heartbeat.isoformat() if agent.last_heartbeat else None,
        }

    def _get_agent_conversations(self, agent_key: str) -> list[str]:
        """Get conversation keys associated with an agent."""
        # Import here to avoid circular imports
        from api.models import Conversation

        # Get conversations where the agent is a participant (via persona or direct link)
        # For now, we'll return an empty list as agents don't directly own conversations
        # This can be extended based on how agents interact with conversations
        return []


# Singleton instance
checkpoint_service = CheckpointService()

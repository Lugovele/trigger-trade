"""Persistence boundary for audit trail and recovery state."""

from .execution_store import ExecutionRecord, ExecutionStore

__all__ = ["ExecutionRecord", "ExecutionStore"]

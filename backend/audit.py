"""
Audit logging for Phronesis LEX.
Tracks all significant actions for accountability.
"""
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from db.connection import db


class AuditAction:
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    ANALYZE = "analyze"
    LOGIN = "login"
    EXPORT = "export"


class AuditEntry(BaseModel):
    id: str
    timestamp: str
    user: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    success: bool = True
    error: Optional[str] = None


async def log_audit(
    user: str,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    resource_name: Optional[str] = None,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
    success: bool = True,
    error: Optional[str] = None
) -> str:
    """
    Log an audit entry.

    Args:
        user: Username performing the action
        action: Action type (create, read, update, delete, analyze)
        resource_type: Type of resource (case, document, claim, etc.)
        resource_id: ID of the resource
        resource_name: Human-readable name of the resource
        description: Additional description
        ip_address: Client IP address
        success: Whether the action succeeded
        error: Error message if failed

    Returns:
        Audit entry ID
    """
    entry_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()

    await db.insert("audit_logs", {
        "id": entry_id,
        "timestamp": timestamp,
        "user": user,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "resource_name": resource_name,
        "description": description,
        "ip_address": ip_address,
        "success": success,
        "error": error
    })

    return entry_id


async def get_audit_logs(
    user: Optional[str] = None,
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100
) -> list:
    """Get audit logs with optional filtering."""
    query = "SELECT * FROM audit_logs WHERE 1=1"
    params = []

    if user:
        query += " AND user = ?"
        params.append(user)

    if resource_type:
        query += " AND resource_type = ?"
        params.append(resource_type)

    if action:
        query += " AND action = ?"
        params.append(action)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    return await db.fetch_all(query, tuple(params))


# SQL to create the audit_logs table
AUDIT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    user TEXT NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    resource_name TEXT,
    description TEXT,
    ip_address TEXT,
    success INTEGER DEFAULT 1,
    error TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs(resource_type, resource_id);
"""

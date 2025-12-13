"""
Audit logging service for tracking security-sensitive operations.

All Council Member actions, user creations, permission changes,
and security events are logged for compliance and security auditing.
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Any, Dict
from uuid import UUID
import logging

from app.db.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """
    Service for creating and managing audit logs.

    SECURITY REQUIREMENTS:
    - All privileged operations must be audited
    - Logs must be immutable (no updates/deletes)
    - Logs must capture who, what, when, and context
    - Never log passwords or sensitive credentials
    """

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def log_event(
        db: Session,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None
    ):
        """
        Logs a system event to the audit_logs table.
        Legacy static method for backward compatibility.
        """
        audit_entry = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            payload=payload
        )
        db.add(audit_entry)
        db.commit()

    def log_action(
        self,
        action: str,
        entity_type: str,
        user_id: Optional[UUID] = None,
        entity_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Create an audit log entry.

        Args:
            action: Action performed (e.g., "COUNCIL_MEMBER_CREATE", "USER_PROMOTE")
            entity_type: Type of entity affected (e.g., "user", "company", "setting")
            user_id: UUID of user performing the action
            entity_id: ID of the entity affected
            payload: Additional context (sanitized, no passwords)

        Returns:
            Created AuditLog object
        """
        # Sanitize payload - ensure no sensitive data
        safe_payload = self._sanitize_payload(payload or {})

        audit_log = AuditLog(
            timestamp=datetime.utcnow(),
            user_id=str(user_id) if user_id else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=safe_payload
        )

        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)

        logger.info(
            f"AUDIT: {action} | Entity: {entity_type}:{entity_id} | "
            f"User: {user_id} | Timestamp: {audit_log.timestamp}"
        )

        return audit_log

    def log_council_member_create(
        self,
        creator_id: UUID,
        new_member_id: UUID,
        new_member_email: str
    ) -> AuditLog:
        """
        Log creation of a new Council Member.

        Args:
            creator_id: UUID of existing Council Member who created the new member
            new_member_id: UUID of the newly created Council Member
            new_member_email: Email of the new Council Member

        Returns:
            Created AuditLog object
        """
        return self.log_action(
            action="COUNCIL_MEMBER_CREATE",
            entity_type="user",
            user_id=creator_id,
            entity_id=str(new_member_id),
            payload={
                "email": new_member_email,
                "role": "COUNCIL_MEMBER",
                "is_superuser": True,
                "force_password_reset": True
            }
        )

    def log_user_promote(
        self,
        promoter_id: UUID,
        promoted_user_id: UUID,
        promoted_user_email: str
    ) -> AuditLog:
        """Log promotion of user to superuser."""
        return self.log_action(
            action="USER_PROMOTE_SUPERUSER",
            entity_type="user",
            user_id=promoter_id,
            entity_id=str(promoted_user_id),
            payload={"email": promoted_user_email}
        )

    def log_user_demote(
        self,
        demoter_id: UUID,
        demoted_user_id: UUID,
        demoted_user_email: str
    ) -> AuditLog:
        """Log demotion of user from superuser."""
        return self.log_action(
            action="USER_DEMOTE_SUPERUSER",
            entity_type="user",
            user_id=demoter_id,
            entity_id=str(demoted_user_id),
            payload={"email": demoted_user_email}
        )

    def log_password_change(
        self,
        user_id: UUID,
        user_email: str,
        was_forced: bool = False
    ) -> AuditLog:
        """
        Log password change event.

        Args:
            user_id: UUID of user changing password
            user_email: Email of user
            was_forced: Whether this was a forced password reset

        Returns:
            Created AuditLog object
        """
        return self.log_action(
            action="PASSWORD_CHANGE" if not was_forced else "FORCED_PASSWORD_RESET",
            entity_type="user",
            user_id=user_id,
            entity_id=str(user_id),
            payload={
                "email": user_email,
                "forced_reset": was_forced
            }
        )

    def log_failed_login(
        self,
        email: str,
        reason: str,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """
        Log failed login attempt.

        Args:
            email: Email of attempted login
            reason: Reason for failure (e.g., "invalid_password", "user_not_found")
            ip_address: IP address of request (if available)

        Returns:
            Created AuditLog object
        """
        return self.log_action(
            action="LOGIN_FAILED",
            entity_type="authentication",
            user_id=None,
            entity_id=email,
            payload={
                "email": email,
                "reason": reason,
                "ip_address": ip_address
            }
        )

    def log_successful_login(
        self,
        user_id: UUID,
        user_email: str,
        requires_password_reset: bool = False,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """
        Log successful login.

        Args:
            user_id: UUID of user
            user_email: Email of user
            requires_password_reset: Whether user must reset password
            ip_address: IP address of request (if available)

        Returns:
            Created AuditLog object
        """
        return self.log_action(
            action="LOGIN_SUCCESS",
            entity_type="authentication",
            user_id=user_id,
            entity_id=str(user_id),
            payload={
                "email": user_email,
                "requires_password_reset": requires_password_reset,
                "ip_address": ip_address
            }
        )

    def _sanitize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove sensitive data from payload before logging.

        Args:
            payload: Raw payload dictionary

        Returns:
            Sanitized payload safe for logging
        """
        # List of keys that should never be logged
        sensitive_keys = {
            'password', 'hashed_password', 'token', 'secret', 'api_key',
            'credential', 'private_key', 'access_token', 'refresh_token'
        }

        sanitized = {}
        for key, value in payload.items():
            # Skip sensitive keys
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            # Recursively sanitize nested dicts
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_payload(value)
            else:
                sanitized[key] = value

        return sanitized

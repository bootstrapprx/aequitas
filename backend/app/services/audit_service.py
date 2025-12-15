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

    def log_account_lock(
        self,
        user_id: UUID,
        account_id: UUID,
        account_code: str,
        account_name: str,
        company_id: UUID,
        locked_reason: str
    ) -> AuditLog:
        """
        Log account locking event.

        Args:
            user_id: UUID of user locking the account
            account_id: UUID of locked account
            account_code: Code of locked account
            account_name: Name of locked account
            company_id: Company ID
            locked_reason: Reason for lock (FirstTransaction, PeriodClose, Manual)

        Returns:
            Created AuditLog object
        """
        return self.log_action(
            action="ACCOUNT_LOCKED",
            entity_type="company_account",
            user_id=user_id,
            entity_id=str(account_id),
            payload={
                "account_code": account_code,
                "account_name": account_name,
                "company_id": str(company_id),
                "locked_reason": locked_reason,
                "locked_fields": ["name", "type", "code", "account_type", "normal_balance", "parent_id", "mapped_master_account_id"]
            }
        )

    def log_account_unlock(
        self,
        user_id: UUID,
        account_id: UUID,
        account_code: str,
        account_name: str,
        company_id: UUID,
        unlock_reason: Optional[str] = None
    ) -> AuditLog:
        """
        Log account unlocking event (CRITICAL SECURITY OPERATION).

        Args:
            user_id: UUID of superuser unlocking the account
            account_id: UUID of unlocked account
            account_code: Code of unlocked account
            account_name: Name of unlocked account
            company_id: Company ID
            unlock_reason: Reason for unlock (from request)

        Returns:
            Created AuditLog object
        """
        return self.log_action(
            action="ACCOUNT_UNLOCKED",
            entity_type="company_account",
            user_id=user_id,
            entity_id=str(account_id),
            payload={
                "account_code": account_code,
                "account_name": account_name,
                "company_id": str(company_id),
                "unlock_reason": unlock_reason,
                "security_level": "CRITICAL",
                "requires_superuser": True
            }
        )

    def log_fiscal_period_close(
        self,
        user_id: UUID,
        period_id: UUID,
        period_name: str,
        company_id: UUID,
        start_date: str,
        end_date: str
    ) -> AuditLog:
        """
        Log fiscal period close event.

        Args:
            user_id: UUID of user closing the period
            period_id: UUID of closed period
            period_name: Name of period
            company_id: Company ID
            start_date: Period start date (ISO format)
            end_date: Period end date (ISO format)

        Returns:
            Created AuditLog object
        """
        return self.log_action(
            action="FISCAL_PERIOD_CLOSED",
            entity_type="fiscal_period",
            user_id=user_id,
            entity_id=str(period_id),
            payload={
                "period_name": period_name,
                "company_id": str(company_id),
                "start_date": start_date,
                "end_date": end_date,
                "gaap_impact": "Period is now read-only, no journal entries can be posted",
                "reversible": "Only via superuser REOPEN operation"
            }
        )

    def log_fiscal_period_reopen(
        self,
        user_id: UUID,
        period_id: UUID,
        period_name: str,
        company_id: UUID,
        start_date: str,
        end_date: str,
        reopen_reason: Optional[str] = None
    ) -> AuditLog:
        """
        Log fiscal period reopen event (CRITICAL SECURITY OPERATION).

        Args:
            user_id: UUID of superuser reopening the period
            period_id: UUID of reopened period
            period_name: Name of period
            company_id: Company ID
            start_date: Period start date (ISO format)
            end_date: Period end date (ISO format)
            reopen_reason: Reason for reopen (optional)

        Returns:
            Created AuditLog object
        """
        return self.log_action(
            action="FISCAL_PERIOD_REOPENED",
            entity_type="fiscal_period",
            user_id=user_id,
            entity_id=str(period_id),
            payload={
                "period_name": period_name,
                "company_id": str(company_id),
                "start_date": start_date,
                "end_date": end_date,
                "reopen_reason": reopen_reason,
                "security_level": "CRITICAL",
                "requires_superuser": True,
                "gaap_impact": "Period is now writable, journal entries can be modified"
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

"""
Enhanced logging utility for company APIs with CloudWatch metrics support.

This module provides structured logging with:
- Event types and log levels (INFO, ERROR, DEBUG)
- User ID tracking from request headers
- CloudWatch custom metrics for errors
- Detailed error context and stack traces
"""

import logging
import traceback
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Initialize CloudWatch client
try:
    cloudwatch_client = boto3.client("cloudwatch")
except Exception:
    cloudwatch_client = None  # Graceful degradation if CloudWatch is not available


class EventType(str, Enum):
    """Event types for categorizing log entries"""

    # API Request/Response Events
    API_REQUEST = "API_REQUEST"
    API_RESPONSE = "API_RESPONSE"
    API_ERROR = "API_ERROR"

    # Database Events
    DB_QUERY = "DB_QUERY"
    DB_ERROR = "DB_ERROR"

    # Business Logic Events
    VALIDATION_ERROR = "VALIDATION_ERROR"
    BUSINESS_LOGIC_ERROR = "BUSINESS_LOGIC_ERROR"

    # CloudWatch Events
    CLOUDWATCH_METRIC_SUCCESS = "CLOUDWATCH_METRIC_SUCCESS"
    CLOUDWATCH_METRIC_ERROR = "CLOUDWATCH_METRIC_ERROR"

    # Company API Events - GET Operations
    GET_ALL_COMPANIES_START = "GET_ALL_COMPANIES_START"
    GET_ALL_COMPANIES_SUCCESS = "GET_ALL_COMPANIES_SUCCESS"
    GET_ALL_COMPANIES_ERROR = "GET_ALL_COMPANIES_ERROR"

    GET_COMPANY_DETAILS_START = "GET_COMPANY_DETAILS_START"
    GET_COMPANY_DETAILS_SUCCESS = "GET_COMPANY_DETAILS_SUCCESS"
    GET_COMPANY_DETAILS_ERROR = "GET_COMPANY_DETAILS_ERROR"

    GET_COMPANY_FUNDING_START = "GET_COMPANY_FUNDING_START"
    GET_COMPANY_FUNDING_SUCCESS = "GET_COMPANY_FUNDING_SUCCESS"
    GET_COMPANY_FUNDING_ERROR = "GET_COMPANY_FUNDING_ERROR"

    GET_COMPANY_TEAM_START = "GET_COMPANY_TEAM_START"
    GET_COMPANY_TEAM_SUCCESS = "GET_COMPANY_TEAM_SUCCESS"
    GET_COMPANY_TEAM_ERROR = "GET_COMPANY_TEAM_ERROR"

    GET_COMPANY_RELATIONSHIPS_START = "GET_COMPANY_RELATIONSHIPS_START"
    GET_COMPANY_RELATIONSHIPS_SUCCESS = "GET_COMPANY_RELATIONSHIPS_SUCCESS"
    GET_COMPANY_RELATIONSHIPS_ERROR = "GET_COMPANY_RELATIONSHIPS_ERROR"

    GET_OFFICE_LOCATIONS_START = "GET_OFFICE_LOCATIONS_START"
    GET_OFFICE_LOCATIONS_SUCCESS = "GET_OFFICE_LOCATIONS_SUCCESS"
    GET_OFFICE_LOCATIONS_ERROR = "GET_OFFICE_LOCATIONS_ERROR"

    GET_COMPANY_OFFERINGS_START = "GET_COMPANY_OFFERINGS_START"
    GET_COMPANY_OFFERINGS_SUCCESS = "GET_COMPANY_OFFERINGS_SUCCESS"
    GET_COMPANY_OFFERINGS_ERROR = "GET_COMPANY_OFFERINGS_ERROR"

    GET_MARKET_POSITION_START = "GET_MARKET_POSITION_START"
    GET_MARKET_POSITION_SUCCESS = "GET_MARKET_POSITION_SUCCESS"
    GET_MARKET_POSITION_ERROR = "GET_MARKET_POSITION_ERROR"

    GET_DIGITAL_PRESENCE_START = "GET_DIGITAL_PRESENCE_START"
    GET_DIGITAL_PRESENCE_SUCCESS = "GET_DIGITAL_PRESENCE_SUCCESS"
    GET_DIGITAL_PRESENCE_ERROR = "GET_DIGITAL_PRESENCE_ERROR"

    GET_COMPANY_NEWS_START = "GET_COMPANY_NEWS_START"
    GET_COMPANY_NEWS_SUCCESS = "GET_COMPANY_NEWS_SUCCESS"
    GET_COMPANY_NEWS_ERROR = "GET_COMPANY_NEWS_ERROR"

    GET_SOCIAL_IMPACT_START = "GET_SOCIAL_IMPACT_START"
    GET_SOCIAL_IMPACT_SUCCESS = "GET_SOCIAL_IMPACT_SUCCESS"
    GET_SOCIAL_IMPACT_ERROR = "GET_SOCIAL_IMPACT_ERROR"

    GET_COMPANY_SIGNALS_START = "GET_COMPANY_SIGNALS_START"
    GET_COMPANY_SIGNALS_SUCCESS = "GET_COMPANY_SIGNALS_SUCCESS"
    GET_COMPANY_SIGNALS_ERROR = "GET_COMPANY_SIGNALS_ERROR"

    # Watchlist Events
    ADD_TO_WATCHLIST_START = "ADD_TO_WATCHLIST_START"
    ADD_TO_WATCHLIST_SUCCESS = "ADD_TO_WATCHLIST_SUCCESS"
    ADD_TO_WATCHLIST_ERROR = "ADD_TO_WATCHLIST_ERROR"

    REMOVE_FROM_WATCHLIST_START = "REMOVE_FROM_WATCHLIST_START"
    REMOVE_FROM_WATCHLIST_SUCCESS = "REMOVE_FROM_WATCHLIST_SUCCESS"
    REMOVE_FROM_WATCHLIST_ERROR = "REMOVE_FROM_WATCHLIST_ERROR"

    GET_WATCHLIST_START = "GET_WATCHLIST_START"
    GET_WATCHLIST_SUCCESS = "GET_WATCHLIST_SUCCESS"
    GET_WATCHLIST_ERROR = "GET_WATCHLIST_ERROR"

    # Specific Error Events
    COMPANY_NOT_FOUND = "COMPANY_NOT_FOUND"
    COMPANY_ALREADY_IN_WATCHLIST = "COMPANY_ALREADY_IN_WATCHLIST"
    WATCHLIST_ENTRY_NOT_FOUND = "WATCHLIST_ENTRY_NOT_FOUND"
    INVALID_PAGINATION_PARAMS = "INVALID_PAGINATION_PARAMS"
    INVALID_PRIORITY = "INVALID_PRIORITY"


class LogLevel(str, Enum):
    """Log levels"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class HubLogger:
    """Enhanced logger with CloudWatch metrics support for company APIs"""

# TODO: change the name of namespace in prod
    def __init__(self, name: str = "company-api", namespace: str = "DevHubEverestek"):
        """
        Initialize enhanced logger

        Args:
            name: Logger name
            namespace: CloudWatch namespace for custom metrics
        """
        self.logger = logging.getLogger(name)
        self.namespace = namespace
        self.cloudwatch_enabled = cloudwatch_client is not None

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.utcnow().isoformat() + "Z"

    def _build_log_context(
        self,
        message: str,
        event_type: EventType,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build structured log context

        Args:
            message: Log message
            event_type: Type of event
            user_id: User ID from request headers
            company_id: Company ID if applicable
            additional_context: Additional context data

        Returns:
            Dictionary with structured log data
        """
        context = {
            "timestamp": self._get_timestamp(),
            "event_type": event_type.value,
            "message": message,
        }

        

        if user_id:
            context["user_id"] = user_id

        if company_id:
            context["company_id"] = company_id

        if additional_context:
            context.update(additional_context)

        return context

    def _format_log_message(self, context: Dict[str, Any]) -> str:
        """Format log message with context"""
        parts = [f"{context['timestamp']} | {context['event_type']} | {context['message']} "]

        if "user_id" in context:
            parts.append(f"user_id={context['user_id']}")

        if "company_id" in context:
            parts.append(f"company_id={context['company_id']}")

        # Add other context as key=value pairs
        excluded_keys = {"timestamp", "event_type", "message", "user_id", "company_id"}
        for key, value in context.items():
            if key not in excluded_keys:
                parts.append(f"{key}={value}")

        return " | ".join(parts)

    def _push_cloudwatch_metric(
        self, metric_name: str, value: float = 1.0, dimensions: Optional[Dict[str, str]] = None
    ):
        """
        Push custom metric to CloudWatch

        Args:
            metric_name: Name of the metric
            value: Metric value (default: 1.0 for count)
            dimensions: Metric dimensions (e.g., event_type, user_id)
        """
        if not self.cloudwatch_enabled:
            self.logger.warning(f"Cloudwatch is not enabled, kindly check")
            return

        try:
            metric_data = {
                "MetricName": metric_name,
                "Value": value,
                "Unit": "Count",
                "Timestamp": datetime.now(timezone.utc)
            }

            if dimensions:
                metric_data["Dimensions"] = [
                    {"Name": key, "Value": str(value)} for key, value in dimensions.items()
                ]

            cloudwatch_client.put_metric_data(
                Namespace=self.namespace, MetricData=[metric_data]
            )

            self.logger.debug(
                f"CloudWatch metric pushed: {metric_name}",
                extra={
                    "event_type": EventType.CLOUDWATCH_METRIC_SUCCESS.value,
                    "metric_name": metric_name,
                },
            )

        except (BotoCoreError, ClientError) as e:
            # Don't fail the application if CloudWatch metrics fail
            self.logger.warning(
                f"Failed to push CloudWatch metric: {str(e)}",
                extra={
                    "event_type": EventType.CLOUDWATCH_METRIC_ERROR.value,
                    "metric_name": metric_name,
                    "error": str(e),
                },
            )

    def info(
        self,
        message: str,
        event_type: EventType,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Log info message

        Args:
            message: Log message
            event_type: Event type
            user_id: User ID from request
            company_id: Company ID if applicable
            **kwargs: Additional context
        """
        context = self._build_log_context(message, event_type, user_id, company_id, kwargs)
        log_msg = self._format_log_message(context)
        self.logger.info(log_msg, extra=context)

    def debug(
        self,
        message: str,
        event_type: EventType,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Log debug message

        Args:
            message: Log message
            event_type: Event type
            user_id: User ID from request
            company_id: Company ID if applicable
            **kwargs: Additional context
        """
        context = self._build_log_context(message, event_type, user_id, company_id, kwargs)
        log_msg = self._format_log_message(context)
        self.logger.debug(log_msg, extra=context)

    def warning(
        self,
        message: str,
        event_type: EventType,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None,
        **kwargs,
    ):
        """
        Log warning message

        Args:
            message: Log message
            event_type: Event type
            user_id: User ID from request
            company_id: Company ID if applicable
            **kwargs: Additional context
        """
        context = self._build_log_context(message, event_type, user_id, company_id, kwargs)
        log_msg = self._format_log_message(context)
        self.logger.warning(log_msg, extra=context)

    def error(
        self,
        message: str,
        event_type: EventType,
        error: Optional[Exception] = None,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None,
        push_metric: bool = True,
        **kwargs,
    ):
        """
        Log error message and optionally push CloudWatch metric

        Args:
            message: Log message
            event_type: Event type
            error: Exception object if available
            user_id: User ID from request
            company_id: Company ID if applicable
            push_metric: Whether to push error metric to CloudWatch
            **kwargs: Additional context
        """
        # Add error details to context
        error_context = kwargs.copy()
        if error:
            error_context["error_type"] = type(error).__name__
            error_context["error_message"] = str(error)
            # TODO: if we don't require stack trace in the logs we can comment it
            error_context["stack_trace"] = traceback.format_exc()

        context = self._build_log_context(message, event_type, user_id, company_id, error_context)
        log_msg = self._format_log_message(context)
        self.logger.error(log_msg, extra=context, exc_info=error is not None)

        # Push CloudWatch metric for errors
        if push_metric:
            metric_dimensions = {"EventType": event_type.value}
            if user_id:
                metric_dimensions["UserID"] = user_id

            self._push_cloudwatch_metric(
                metric_name="APIError", value=1.0, dimensions=metric_dimensions
            )

    def critical(
        self,
        message: str,
        event_type: EventType,
        error: Optional[Exception] = None,
        user_id: Optional[str] = None,
        company_id: Optional[str] = None,
        push_metric: bool = True,
        **kwargs,
    ):
        """
        Log critical error message and push CloudWatch metric

        Args:
            message: Log message
            event_type: Event type
            error: Exception object if available
            user_id: User ID from request
            company_id: Company ID if applicable
            push_metric: Whether to push error metric to CloudWatch
            **kwargs: Additional context
        """
        # Add error details to context
        error_context = kwargs.copy()
        if error:
            error_context["error_type"] = type(error).__name__
            error_context["error_message"] = str(error)
            error_context["stack_trace"] = traceback.format_exc()

        context = self._build_log_context(message, event_type, user_id, company_id, error_context)
        log_msg = self._format_log_message(context)
        self.logger.critical(log_msg, extra=context, exc_info=error is not None)

        # Push CloudWatch metric for critical errors
        if push_metric:
            metric_dimensions = {"EventType": event_type.value, "Severity": "Critical"}
            if user_id:
                metric_dimensions["UserID"] = user_id

            self._push_cloudwatch_metric(
                metric_name="CriticalError", value=1.0, dimensions=metric_dimensions
            )


# Singleton instance
hub_logger = HubLogger()



from sqlalchemy import event
from src.dao.db import SessionLocal
from src.core.config import get_app_settings
from src.dao.models.passenger import Passenger, ShipCallManifest
import logging
import threading
from src.service.converter import Converter
from src.middlewares.tracing import authorization_var, trace_id_var
from src.middlewares.middleware import header_var
import httpx


settings = get_app_settings()
converter = Converter()


def create_audit_record(audit_record_json: dict, authorization: any):
    """
    Create an audit record by making an HTTP POST request to a specified audit service URL
    using the Authorization header from the provided HTTP request.

    Args:
        audit_record_json (dict): A JSON dictionary representing the audit record data.
        request (Request): An HTTP request object containing headers, including the Authorization header.

    Raises:
        httpx.RequestError: If an error occurs while making the HTTP request.

    Notes:
        This function constructs an HTTP POST request with the provided audit record JSON
        and extracts the Authorization header from the given HTTP request to set it in
        the headers of the new request. It sends the request to the audit service URL
        and handles the response status code appropriately.

    Example:
        To create an audit record, you can call this function as follows:
        create_audit_record(audit_record_json, request)
    """

    try:
        audit_record_url = (
            f"{settings.AUDIT_SERVICE_URL}{settings.CREATE_AUDIT_RECORD_URL}"
        )

        headers = {"Authorization": authorization}
        response = httpx.post(audit_record_url, json=audit_record_json, headers=headers)

        if response.status_code == 201:
            audit_record = response.json()
            logging.info(f"Audit record created: {audit_record}")
        elif response.status_code == 400:
            error_message = response.json()
            logging.error(f"Error: {error_message}")
        else:
            logging.info(f"Unexpected status code: {response.status_code}")

    except httpx.RequestError as e:
        logging.error(f"Error: {e}")


def audit_log(mapper, connection, target):
    correlation_id = trace_id_var.get()
    session = SessionLocal.object_session(target)
    if session is None:
        return

    if target.id is None or session.query(target.__class__).get(target.id) is None:
        operation = "INSERT"
    else:
        operation = "UPDATE"

    before_change = {}
    after_change = {}
    for attr in target.__mapper__.column_attrs:
        attr_name = attr.key
        old_value = getattr(target, "_sa_instance_state").committed_state.get(attr_name)
        new_value = getattr(target, attr_name)
        before_change[attr_name] = str(old_value)
        after_change[attr_name] = str(new_value)

    audit_record_json = converter.create_audit_record_json(
        correlation_id,
        settings.JAMBAXI_ID,
        after_change,
        {} if operation == "INSERT" else before_change,
        target.__class__.__name__,
        operation,
        header_var.get(),
    )

    print("OPERATION TYPE", operation, "\n")
    authorization = authorization_var.get()
    # FIRE AND FORGET
    thread = threading.Thread(
        target=create_audit_record, args=(audit_record_json, authorization)
    )
    thread.start()
    # create_audit_record(audit_record_json)


def audit_delete(mapper, connection, target):
    session = SessionLocal.object_session(target)
    correlation_id = trace_id_var.get()
    if session is None:
        return

    changes = {
        attr.key: str(getattr(target, attr.key))
        for attr in target.__mapper__.column_attrs
    }

    audit_record_json = converter.create_audit_record_json(
        correlation_id,
        settings.JAMBAXI_ID,
        {},
        changes,
        target.__class__.__name__,
        "DELETE",
        header_var.get(),
    )
    authorization = authorization_var.get()

    # FIRE AND FORGET
    thread = threading.Thread(
        target=create_audit_record, args=(audit_record_json, authorization)
    )
    thread.start()


def event_listner():
    if (
        settings.CREATE_AUDIT_RECORD_FLAG == "1"
        or settings.CREATE_AUDIT_RECORD_FLAG == 1
    ):
        print("--------------LISTENDING TO AUDIT--------------")
        event.listen(Passenger, "before_insert", audit_log)
        event.listen(Passenger, "before_update", audit_log)
        event.listen(Passenger, "before_delete", audit_delete)

        event.listen(ShipCallManifest, "before_insert", audit_log)
        event.listen(ShipCallManifest, "before_update", audit_log)
        event.listen(ShipCallManifest, "before_delete", audit_delete)

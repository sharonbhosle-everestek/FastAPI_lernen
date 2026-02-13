"""This module includes middlewares"""

import ast
from fastapi import Request, HTTPException, Depends
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from src.core.config import get_app_settings
from starlette.responses import StreamingResponse
import logging
from starlette.concurrency import iterate_in_threadpool
from fastapi import FastAPI, Request, Response
from src.middlewares.tracing import (
    Tracing,
    logger,
    trace_id_var,
    authorization_var,
    parent_span_id_var,
    tracer,
)
import json
import uuid
import time
from contextvars import ContextVar
from src.utils.send_email import send_multiple_email
from opentelemetry.trace import SpanContext, TraceFlags
from opentelemetry.trace.propagation import set_span_in_context
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
from opentelemetry.trace import NonRecordingSpan
from src.core.config import AppSettings
from typing import Dict, List, Optional
import secrets
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.types import Receive, Send, Scope

settings = get_app_settings()
header_var = ContextVar("header_var", default="")
x_system_user_id = ContextVar("x_system_user_id", default="")


class LogRequestResponseMiddleware(BaseHTTPMiddleware):
    """Middleware for logging"""

    async def set_body(self, request: Request, body: bytes):
        """Helper Function

        Args:
            request (Request): _description_
            body (bytes): _description_
        """

        async def receive():
            return {"type": "http.request", "body": body}

        request._receive = receive

    async def get_body(self, request: Request) -> bytes:
        body = await request.body()
        await self.set_body(request, body)
        return body

    async def dispatch(self, request: Request, call_next):
        """Dispatcher class for logging

        Args:
            request (Request): the request object
            call_next (_type_): function

        Returns:
            _type_: Response type, streaming or non-streaming
        """
        try:
            start_time = time.time()
            with tracer.start_as_current_span(request.url.path) as span:
                trace_id = span.get_span_context().trace_id
                shared_trace_id = format(trace_id, "032x")
                # shared_trace_id = f"{shared_trace_id[:8]}-{shared_trace_id[8:]}"
                trace_id_var.set(shared_trace_id)

            try:
                # Setting the authorization if exist
                header_var.set(
                    {
                        key: val
                        for key, val in request.headers.items()
                        if key != "authorization"
                    }
                )
                authorization_var.set(request.headers["authorization"])
            except Exception as e:
                print("Exception ----------->", e)

            try:
                x_system_user_id.set(request.headers["x_system_user_id"])
            except:
                pass

            # Log the API endpoint
            endpoint = request.url.path

            # Setting the request payload
            await self.set_body(request, await request.body())
            request_body = await self.get_body(request)
            logger.info(f"API endpoint: {endpoint}, TraceID: {shared_trace_id}\n")
            logger.info(
                f"Request payload: {request_body.decode('utf-8', errors='ignore')}, TraceID: {shared_trace_id}\n"
            )

            # Process the request and get the response
            response = await call_next(request)

            # Log the response body and status code
            response_text = ""
            if isinstance(response, StreamingResponse):
                # Log the body in chunks for streaming responses
                response_body = [chunk async for chunk in response.body_iterator]
                response.body_iterator = iterate_in_threadpool(iter(response_body))
                if response_body:
                    response_text = response_body[0].decode("utf-8")
            else:
                # Log the entire response body for non-streaming responses
                response_body = await response.body()
                response_text = response_body.decode("utf-8")
            response.headers["Trace-ID"] = str(trace_id)
            response_status_code = response.status_code
            logger.info(
                f"Response payload: {response_text}, TraceID: {shared_trace_id}\n"
            )
            logger.info(
                f"Response status code: {response_status_code}, TraceID: {shared_trace_id}\n"
            )
            end_time = time.time()
            time_spent = end_time - start_time
            t = Tracing()
            span_id = str(uuid.uuid4())
            parent_span_id_var.set(span_id)
            extra = {
                "SERVICE_NAME": "PASSENGERS-SERVICE",
                "TRACE_ID": shared_trace_id,
                "HTTP_ENDPOINT": endpoint,
                "DURATION": time_spent,
                "METHOD": request.method,
                "STATUS_CODE": response_status_code,
            }
            logger.info(f"API INFO: {extra}")
            t.audit(
                trace_id,
                span_id,
                "",
                endpoint,
                start_time,
                end_time,
                request_body.decode("utf-8", errors="ignore"),
                response_text,
                response_status_code,
                time_spent,
                "",
            )

            with tracer.start_as_current_span(request.url.path) as span:
                # Add request-level attributes
                span.set_attribute("http.method", request.method)
                span.set_attribute("http.path", str(request.url.path))

                span.set_attribute("http.status_code", response_status_code)
                span.set_attribute(
                    "input_args", request_body.decode("utf-8", errors="ignore")
                )
                span.set_attribute("output_args", response_text)
                logger.info(
                    f"Custom trace_id {trace_id} {span.get_span_context().trace_id} {request.url.path}"
                )

                self.send_error_email(endpoint, response_status_code, trace_id)

            return response
        except Exception as e:
            print("Exception ------>", e)
            end_time = time.time()
            time_spent = end_time - start_time
            t = Tracing()
            span_id = str(uuid.uuid4())
            parent_span_id_var.set(span_id)
            t.audit(
                trace_id,
                span_id,
                "",
                endpoint,
                start_time,
                end_time,
                str(request_body.decode("utf-8", errors="ignore")),
                "",
                "500",
                time_spent,
                str(e),
            )
            raise e

    def send_error_email(self, endpoint, response_status_code, trace_id):
        if response_status_code >= 500:
            trace_id = f"1-{format(trace_id, '032x')}"
            trace_id = f"{trace_id[:10]}-{trace_id[10:]}"
            log_link = f"https://console.aws.amazon.com/cloudwatch/home?region={settings.REGION}#xray:traces/{trace_id}"
            logger.info(
                f"Mailing error log, with the status code: {response_status_code}\tEndpoint: {endpoint}\t{log_link}"
            )
            send_multiple_email(
                email=ast.literal_eval(settings.ERROR_EMAILS),
                subject=f"JMBAXI Error code {response_status_code} in {endpoint}",
                message=f"Trace link: {log_link}",
            )


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            # Call the next middleware or route handler
            response = await call_next(request)

            # After the response is received, create the audit record
            if response.status_code == 200:
                # Assuming a successful response is the appropriate condition
                await self.create_audit_record(request)

            return response

        except HTTPException as e:
            # Handle HTTPExceptions if needed
            return e

    async def create_audit_record(self, request: Request):
        # Your existing create_audit_record function
        audit_record_json = {"example_key": "example_value"}  # Replace with your data
        await create_audit_record(audit_record_json, request)


class CSPMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling Content Security Policy (CSP) and other security headers.
    Provides specialized CSP configurations for API endpoints, Swagger UI, and ReDoc documentation.

    Features:
    - Configurable CSP directives for different endpoints
    - Dynamic nonce generation for enhanced security
    - Custom ReDoc template with improved styling
    - Additional security headers (HSTS, X-Frame-Options, etc.)
    """

    def __init__(self, app, settings: "AppSettings"):
        super().__init__(app)
        self.report_only = settings.CSP_REPORT_ONLY
        self.static_nonce = settings.CSP_STATIC_NONCE
        self.api_prefix = settings.API_PREFIX

        # CSP directives for API
        self.csp_directives = {
            "default-src": ["'none'"],
        }

        # CSP directives for Swagger UI
        self.swagger_csp_directives = {
            "default-src": ["'none'"],
            "script-src": ["'self'", "https://cdn.jsdelivr.net"],
            "style-src": ["'self'", "https://cdn.jsdelivr.net"],
            "img-src": [
                "'self'",
                "https://fastapi.tiangolo.com",
                "https://cdn.jsdelivr.net",
                "data:",
            ],
            "font-src": ["'self'", "https://cdn.jsdelivr.net"],
            "connect-src": ["'self'"],
        }

        # CSP directives for ReDoc with additional security measures
        self.redoc_csp_directives = {
            "default-src": ["'self'"],
            "script-src-elem": [
                "'self'",
                "https://cdn.jsdelivr.net",
                "https://unpkg.com",
            ],
            "style-src-elem": [
                "'self'",
                "https://cdn.jsdelivr.net",
                "https://fonts.googleapis.com",
            ],
            "style-src": [
                "'self'",
                "https://cdn.jsdelivr.net",
                "https://fonts.googleapis.com",
            ],
            "script-src": ["'self'", "https://cdn.jsdelivr.net", "https://unpgk.com"],
            "img-src": [
                "'self'",
                "https://fastapi.tiangolo.com",
                "https://cdn.jsdelivr.net",
                "data:",
            ],
            "font-src": [
                "'self'",
                "https://cdn.jsdelivr.net",
                "https://fonts.gstatic.com",
                "https://fonts.googleapis.com",
            ],
            "connect-src": ["'self'"],
            "base-uri": ["'self'"],
            "object-src": ["'none'"],
            "frame-ancestors": ["'none'"],
            "form-action": ["'self'"],
            "manifest-src": ["'self'"],
            "media-src": ["'self'"],
            "worker-src": ["blob:"],
            "frame-src": ["'self'"],
        }

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Handle the ASGI application call and manage disconnected clients gracefully.
        """
        request = Request(scope, receive, send)
        try:
            await super().__call__(scope, receive, send)
        except RuntimeError as exc:
            if str(exc) == "No response returned." and await request.is_disconnected():
                logger.info("Client disconnected, request handling stopped")
                return
            logger.error(f"Runtime error in middleware: {exc}")
            raise
        except Exception as exc:
            logger.error(f"Unexpected error in middleware: {exc}")
            raise

    def is_valid_docs_path(self, path: str) -> bool:
        """Validate if the documentation path belongs to the API prefix."""
        if not path.endswith(("/docs", "/redoc", "/openapi.json")):
            return False

        return path.startswith(self.api_prefix)

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Main dispatch method that handles request processing and applies security headers.
        This is where we handle most errors since it's the main entry point for requests.
        """
        try:
            request.state.nonce = self.static_nonce

            # Handle documentation endpoints with proper path validation
            path = request.url.path
            if any(
                path.endswith(suffix) for suffix in ("/docs", "/redoc", "/openapi.json")
            ):
                if not self.is_valid_docs_path(path):
                    return JSONResponse(
                        status_code=404, content={"detail": "Not Found"}
                    )

                if path.endswith("/docs"):
                    doc_response = await self.handle_docs(request, self.static_nonce)
                    if doc_response:
                        return doc_response
                elif path.endswith("/redoc"):
                    doc_response = await self.handle_redoc(request, self.static_nonce)
                    if doc_response:
                        return doc_response

            # Process the regular request
            response = await call_next(request)

            # Apply security headers
            final_directives = self.get_csp_directives(request)
            csp_header = self.build_csp_header(final_directives, self.static_nonce)

            header_name = (
                "Content-Security-Policy-Report-Only"
                if self.report_only
                else "Content-Security-Policy"
            )
            response.headers[header_name] = csp_header

            # Add security headers
            response.headers.update(
                {
                    "X-Content-Type-Options": "nosniff",
                    "X-Frame-Options": "DENY",
                    "X-XSS-Protection": "1; mode=block",
                    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                    "Referrer-Policy": "same-origin",
                }
            )

            return response

        except Exception as exc:
            logger.error(f"Error processing request: {exc}", exc_info=True)
            raise

    def inject_nonce_into_styled_components(self, nonce: str) -> str:
        """script to automatically inject nonce into dynamically created style elements."""
        return f"""
        <script nonce='{nonce}'>
            const originalCreateStyleElement = document.createElement.bind(document);
            document.createElement = function(tagName) {{
                if (tagName === 'style') {{
                    const element = originalCreateStyleElement(tagName);
                    element.setAttribute('nonce', '{nonce}');
                    return element;
                }}
                return originalCreateStyleElement(tagName);
            }};
        </script>
        """

    def get_redoc_html(self, openapi_url: str, title: str, nonce: str) -> str:
        """customized ReDoc HTML template with enhanced styling and security features."""
        redoc_config = {
            "scrollYOffset": 50,
            "hideDownloadButton": True,
            "theme": {
                "typography": {
                    "fontFamily": "Roboto, sans-serif",
                    "fontSize": "16px",
                    "lineHeight": "1.5",
                    "fontWeightRegular": "400",
                    "fontWeightBold": "700",
                    "fontWeightLight": "300",
                    "headings": {
                        "fontFamily": "Montserrat, sans-serif",
                        "fontWeight": "400",
                    },
                }
            },
        }

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <meta charset="utf-8"/>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            {self.inject_nonce_into_styled_components(nonce)}
            <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" nonce="{nonce}">
        </head>
        <body>
            <div id="redoc-container"></div>
            <script nonce="{nonce}" src="https://cdn.jsdelivr.net/npm/redoc@latest/bundles/redoc.standalone.js"></script>
            <script nonce="{nonce}">
                Redoc.init(
                    "{openapi_url}",
                    {json.dumps(redoc_config)},
                    document.getElementById("redoc-container")
                );
            </script>
        </body>
        </html>
        """

    def get_csp_directives(self, request: Request) -> Dict[str, List[str]]:
        """Select the appropriate CSP directives based on the request path."""
        # Check if this is a ReDoc-related request (including its OpenAPI JSON request)
        if request.url.path.endswith("/redoc") or (
            request.url.path.endswith("/openapi.json")
            and request.headers.get("referer", "").endswith("/redoc")
        ):
            return self.redoc_csp_directives
        # Check if this is a Swagger-related request
        elif request.url.path.endswith("/docs") or (
            request.url.path.endswith("/openapi.json")
            and request.headers.get("referer", "").endswith("/docs")
        ):
            return self.swagger_csp_directives
        return self.csp_directives

    def build_csp_header(
        self, directives: Dict[str, List[str]], nonce: Optional[str] = None
    ) -> str:
        """Build the CSP header string from directives, optionally including nonce values."""
        policy_parts = []
        for directive, sources in directives.items():
            if sources:
                if nonce and directive in [
                    "script-src",
                    "style-src",
                    "script-src-elem",
                    "style-src-elem",
                ]:
                    sources = list(sources)
                    sources.append(f"'nonce-{nonce}'")
                policy_parts.append(f"{directive} {' '.join(sources)}")

        return "; ".join(policy_parts)

    async def handle_docs(self, request: Request, nonce: str) -> Optional[Response]:
        """Handle Swagger UI documentation requests with proper nonce injection."""
        if request.url.path.endswith("/docs"):
            html = get_swagger_ui_html(
                openapi_url=request.app.openapi_url,
                title=request.app.title + " - Swagger UI",
            ).body.decode()

            html = html.replace("<script>", f'<script nonce="{nonce}">')
            html = html.replace("<style>", f'<style nonce="{nonce}">')

            return HTMLResponse(html)
        return None

    async def handle_redoc(self, request: Request, nonce: str) -> Optional[Response]:
        """Handle ReDoc documentation requests with custom styling and security features."""
        if request.url.path.endswith("/redoc"):
            html = self.get_redoc_html(
                openapi_url=request.app.openapi_url,
                title=request.app.title + " - ReDoc",
                nonce=nonce,
            )
            return HTMLResponse(html)
        return None

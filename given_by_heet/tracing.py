import os.path
import csv
import time
import uuid
import json
import asyncio
from functools import wraps
from contextvars import ContextVar
import logging
from src.core.config import get_app_settings
from datetime import datetime

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry import trace
from opentelemetry.trace import SpanKind
from opentelemetry.trace import SpanContext, TraceFlags
from opentelemetry.trace.propagation import set_span_in_context
from opentelemetry.trace import NonRecordingSpan
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from requests.exceptions import ReadTimeout
from opentelemetry.sdk.trace.export import SpanExportResult

settings = get_app_settings()
resource = Resource.create({"service.name": "passenger_service"})

trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("root")


class GracefulOTLPSpanExporter(OTLPSpanExporter):
    def export(self, spans):
        try:
            return super().export(spans)
        except (ReadTimeout, ConnectionError, TimeoutError):
            logger.error(
                f"Error Occured in connecting the ip : {settings.CONTAINER_IP} for the {spans}"
            )
            return SpanExportResult.FAILURE
        except Exception as e:
            # Let other exceptions pass through (or optionally handle them too)
            logger.error(f"Exception : {e}")
            raise e


if settings.CONTAINER_IP == "localhost":
    # Fallback to ConsoleSpanExporter if OTLPSpanExporter is not available
    logger.info("Using ConsoleSpanExporter as a fallback")
    span_exporter = ConsoleSpanExporter(out=open(os.devnull, "w"))
else:
    for ip in settings.CONTAINER_IP.split(","):
        try:
            logger.info(f"Trying IP for telemetry: {ip}")
            span_exporter = GracefulOTLPSpanExporter(
                endpoint=f"http://{ip}:4316/v1/traces"
            )
            break
        except:
            pass

span_processor = BatchSpanProcessor(span_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Define a context variable for trace_id
trace_id_var = ContextVar("trace_id_var", default=uuid.uuid4())
authorization_var = ContextVar("authorization_var", default="")
parent_span_id_var = ContextVar("parent_span_id", default="")


class Tracing:
    def __init__(self, log_folder: str = "logs/logs.csv") -> None:
        if log_folder:
            self.log_folder = log_folder
        else:
            self.log_folder = "logs/logs.csv"

        # if not os.path.isfile(self.log_folder):
        #     self._create_log_file()

    def _create_log_file(self):
        trace_data_header = "trace_id,span_id,name,start_time,end_time,input_args,output_args,status,duration,exception"
        with open(self.log_folder, "w") as file:
            file.write(trace_data_header)
            file.write("\n")

    def audit(
        self,
        trace_id: str,
        span_id: str,
        parent_span_id: str,
        name: str,
        start_time: float,
        end_time: float,
        input_args: any,
        output_args: any,
        status: any,
        duration: float,
        exception: any,
    ) -> bool:
        try:
            trace_data = {
                "trace_id": f"{trace_id}",
                "span_id": span_id,
                "parent_span_id": parent_span_id,
                "name": name,
                "start_time": start_time,
                "end_time": end_time,
                "input_args": input_args,
                "output_args": output_args,
                "status": status,
                "duration": duration,
                "exception": exception,
            }

            with tracer.start_as_current_span(name) as span:
                span.add_event(
                    f"{name} started",
                    {"timestamp": datetime.fromtimestamp(start_time).isoformat()},
                )
                # Add duration to the span
                span.add_event(
                    f"{name} completed",
                    {
                        "timestamp": datetime.fromtimestamp(end_time).isoformat(),
                        "duration_in_seconds": duration,
                        "input_args": str(input_args),
                        "output_args": str(output_args),
                    },
                )

            logger.info(f"{trace_data}\n")

            # TODO: Make this into a Service
            # with open(self.log_folder, 'a') as f_object:
            #     writer_object = csv.writer(f_object)
            #     writer_object.writerow(line.values())
            return True
        except Exception as e:
            print("Exception ----------->", e)
            return False


def trace_decorator(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        t = Tracing()
        start_time = time.time()
        trace_id = trace_id_var.get()
        parent_span_id = parent_span_id_var.get()
        try:
            result = await func(*args, **kwargs)
            end_time = time.time()
            time_spent = end_time - start_time
            span_id = str(uuid.uuid4())
            parent_span_id_var.set(span_id)
            t.audit(
                trace_id,
                span_id,
                parent_span_id,
                f"{func.__module__}.{func.__name__}",
                start_time,
                end_time,
                {"args": args, "kwargs": kwargs},
                result,
                "success",
                time_spent,
                "",
            )
            del t
            return result
        except Exception as e:
            end_time = time.time()
            time_spent = end_time - start_time
            span_id = str(uuid.uuid4())
            parent_span_id_var.set(span_id)
            t.audit(
                trace_id,
                span_id,
                parent_span_id,
                f"{func.__module__}.{func.__name__}",
                start_time,
                end_time,
                {"args": args, "kwargs": kwargs},
                "",
                "error",
                time_spent,
                str(e),
            )
            del t
            raise e

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        t = Tracing()
        start_time = time.time()
        trace_id = trace_id_var.get()
        parent_span_id = parent_span_id_var.get()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            time_spent = end_time - start_time
            span_id = str(uuid.uuid4())
            parent_span_id_var.set(span_id)
            t.audit(
                trace_id,
                span_id,
                parent_span_id,
                f"{func.__module__}.{func.__name__}",
                start_time,
                end_time,
                {"args": args, "kwargs": kwargs},
                result,
                "success",
                time_spent,
                "",
            )
            del t
            return result
        except Exception as e:
            end_time = time.time()
            time_spent = end_time - start_time
            span_id = str(uuid.uuid4())
            parent_span_id_var.set(span_id)
            t.audit(
                trace_id,
                span_id,
                parent_span_id,
                f"{func.__module__}.{func.__name__}",
                start_time,
                end_time,
                {"args": args, "kwargs": kwargs},
                "",
                "error",
                time_spent,
                str(e),
            )
            del t
            raise e

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

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
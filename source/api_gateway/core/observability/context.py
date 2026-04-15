from contextvars import ContextVar

# ------- Request-scoped observability context -------

request_id_ctx: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None
)

trace_id_ctx: ContextVar[str | None] = ContextVar(
    "trace_id",
    default=None
)

service_name_ctx: ContextVar[str | None] = ContextVar(
    "service_name",
    default=None
)


def set_request_context(
    request_id: str,
    trace_id: str | None = None,
    service_name: str | None = None,
):
    request_id_ctx.set(request_id)
    trace_id_ctx.set(trace_id)
    service_name_ctx.set(service_name)


def get_request_id() -> str | None:
    return request_id_ctx.get()


def get_trace_id() -> str | None:
    return trace_id_ctx.get()


def get_service_name() -> str | None:
    return service_name_ctx.get()
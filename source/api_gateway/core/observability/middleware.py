import uuid
from starlette.middleware.base import BaseHTTPMiddleware

from source.api_gateway.core.observability.context import set_request_context


class ObservabilityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, service_name: str = "api_gateway"):
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())

        trace_id = (
            request.headers.get("X-Trace-ID")
            or str(uuid.uuid4())
        )

        set_request_context(
            request_id=request_id,
            trace_id=trace_id,
            service_name=self.service_name,
        )

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id

        return response
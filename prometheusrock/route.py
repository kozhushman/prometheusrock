import os

from prometheus_client import (
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY,
    multiprocess,
    CollectorRegistry
)
from starlette import status
from starlette.requests import Request
from starlette.responses import Response


def metrics_route(request: Request):
    """
    Endpoint for Prometheus metrics_route. Code taken from prometheus_client examples.

    Examples:
        app.add_middleware(PrometheusMiddleware, {params})

        app.add_route("/metrics_route", metrics_route)

    """
    registry = REGISTRY
    if 'prometheus_multiproc_dir' in os.environ:
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)

    data = generate_latest(registry)
    response_headers = {
        'Content-type': CONTENT_TYPE_LATEST,
        'Content-Length': str(len(data))
    }
    return Response(data, status_code=status.HTTP_200_OK, headers=response_headers)

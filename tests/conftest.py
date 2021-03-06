import asyncio

import pytest
from prometheus_client import REGISTRY
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from prometheusrock import PrometheusMiddleware, MetricsStorage, metrics_route


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop()

    yield loop


def clear_registry():
    """ Clearing registry fore next tests"""
    for collector in list(REGISTRY._collector_to_names):
        REGISTRY.unregister(collector)

    MetricsStorage.clear()


async def append_routes(app):
    app.add_route("/metrics_route", metrics_route)

    @app.route('/200', methods=['GET'])
    async def ok(request):
        return JSONResponse(status_code=200)

    @app.route('/custom/{test}', methods=['GET'])
    async def ok(request):
        return JSONResponse(status_code=200)

    @app.route('/400', methods=['GET'])
    async def bad_request(request):
        return JSONResponse(status_code=400)

    @app.route('/500', methods=['GET'])
    async def server_error(request):
        raise HTTPException(status_code=500)

    @app.route('/long_request', methods=['GET'])
    async def server_error(request):
        while True:
            pass


@pytest.fixture(scope="class")
@pytest.mark.asyncio
async def app_with_middleware():
    app_with_middleware = Starlette()
    app_with_middleware.add_middleware(PrometheusMiddleware, app_name='TestApp')

    await append_routes(app_with_middleware)

    yield app_with_middleware

    clear_registry()


@pytest.fixture(scope="class")
@pytest.mark.asyncio
async def app_with_middleware_current_requests():
    app_with_middleware = Starlette()
    app_with_middleware.add_middleware(PrometheusMiddleware, app_name='TestApp')

    await append_routes(app_with_middleware)

    yield app_with_middleware

    clear_registry()


@pytest.mark.asyncio
@pytest.fixture(scope="class")
async def app_without_middleware(request):
    app_without_middleware = Starlette()
    app_without_middleware.add_middleware(
        PrometheusMiddleware,
        app_name=request.param.get('app_name'),
        additional_headers=request.param.get('additional_headers',[]),
        remove_labels=request.param.get('remove_labels',[]),
        skip_paths=request.param.get('skip_paths',[]),
        custom_base_labels=request.param.get('custom_base_labels', None),
        custom_base_headers=request.param.get('custom_base_headers', None),
        disable_default_counter=request.param.get('disable_default_counter', False),
        disable_default_histogram=request.param.get('disable_default_histogram', False),
        aggregate_paths=request.param.get('aggregate_paths', None),
    )

    await append_routes(app_without_middleware)

    yield app_without_middleware

    clear_registry()

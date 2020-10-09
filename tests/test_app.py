import pytest
from async_asgi_testclient import TestClient
from starlette.applications import Starlette

from prometheusrock import PrometheusMiddleware


class TestAppWithSimpleRequests:
    @pytest.mark.asyncio
    async def test_200(self, app_with_middleware):
        async with TestClient(application=app_with_middleware) as client:
            response = await client.get('/200')
            assert response.status_code == 200

            metrics = (await client.get('/metrics_route')).content.decode()
            assert """method="GET",path="/200",status_code="200"} 1.0""" in metrics

    @pytest.mark.asyncio
    async def test_400(self, app_with_middleware):
        async with TestClient(application=app_with_middleware) as client:
            response = await client.get('/400')
            assert response.status_code == 400

            metrics = (await client.get('/metrics_route')).content.decode()
            assert """method="GET",path="/400",status_code="400"} 1.0""" in metrics

    @pytest.mark.asyncio
    async def test_500(self, app_with_middleware):
        async with TestClient(application=app_with_middleware) as client:
            response = await client.get('/500')
            assert response.status_code == 500
            metrics = (await client.get('/metrics_route')).content.decode()
            assert """method="GET",path="/500",status_code="500"} 1.0""" in metrics


class TestMiddlewareSettings:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("app_without_middleware", [{
        "app_name": "custom_app_name",
        "additional_headers": ["content-type"],
        "remove_labels": ["method"],
        "skip_paths": ["/400"]
    }], indirect=True)
    async def test_settings(self, app_without_middleware):
        async with TestClient(application=app_without_middleware) as client:
            await client.get("/200", headers={"content-type": "json"})
            metrics = (await client.get("/metrics_route")).content.decode()
            assert "custom_app_name" in metrics
            assert "content-type" in metrics
            assert "method" not in metrics

            await client.get("/400")
            metrics = (await client.get("/metrics_route")).content.decode()
            assert "/400" not in metrics

    @pytest.mark.asyncio
    async def test_wrong_settings(self):
        with pytest.raises(ValueError):
            app_without_middleware = Starlette()
            app_without_middleware.add_middleware(PrometheusMiddleware,
                                                  **{
                                                      "remove_labels": [
                                                          "method", "path", "status_code", "headers", "app_name"
                                                      ]
                                                  })

        with pytest.raises(TypeError):
            app_without_middleware = Starlette()
            app_without_middleware.add_middleware(PrometheusMiddleware,
                                                  **{
                                                      "remove_labels": "wrong_type"
                                                  })

        with pytest.raises(TypeError):
            app_without_middleware = Starlette()
            app_without_middleware.add_middleware(PrometheusMiddleware,
                                                  **{
                                                      "additional_headers": "wrong_type"
                                                  })

        with pytest.raises(TypeError):
            app_without_middleware = Starlette()
            app_without_middleware.add_middleware(PrometheusMiddleware,
                                                  **{
                                                      "skip_paths": "wrong_type"
                                                  })

import pytest
from async_asgi_testclient import TestClient

from prometheusrock import MetricsStorage, AddMetric


async def function(middleware_proxy: MetricsStorage):
    res = 'custom_result'
    assert hasattr(middleware_proxy, 'request')
    middleware_proxy.metric.labels(res)


class TestCustomMetrics:
    @pytest.mark.asyncio
    async def test_custom_info(self, app_with_middleware):
        AddMetric(
            function=function,
            metric_name='custom_metric',
            metric_type='info',
            metric_description='custom description'
        )
        async with TestClient(application=app_with_middleware) as client:
            await client.get("/200", headers={"content-type": "json"})
            metrics = (await client.get("/metrics_route")).content.decode()
            assert "custom_metric" in metrics
            assert "custom_result" in metrics
            assert "custom description" in metrics

    @pytest.mark.asyncio
    async def test_custom_incorrect_params(self, app_with_middleware):
        with pytest.raises(TypeError):
            AddMetric(
                function=function,
                metric_name='custom_metric1',
                metric_type='',
                metric_description='custom description'
            )
        with pytest.raises(ValueError):
            AddMetric(
                function=function,
                metric_name='custom_metric2',
                metric_type='info',
                metric_description='custom description'
            )
            AddMetric(
                function=function,
                metric_name='custom_metric2',
                metric_type='info',
                metric_description='custom description'
            )

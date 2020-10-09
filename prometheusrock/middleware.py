import time
import inspect
from typing import List, Tuple

from prometheus_client import (
    Counter,
    Histogram
)
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from prometheusrock.singleton import SingletonMeta


class MetricsStorage(metaclass=SingletonMeta):
    def __init__(self, labels: List[str] = ["method", "path", "status_code", "headers", "app_name"]):
        self.labels = labels
        self.REQUEST_COUNT = Counter(
            "requests_total",
            "Total HTTP requests",
            labels,
        )

        self.REQUEST_TIME = Histogram(
            "request_processing_time",
            "HTTP request processing time in seconds",
            labels,
        )

        self.custom_metrics = []


class PrometheusMiddleware(BaseHTTPMiddleware):
    def __init__(self,
                 app: ASGIApp,
                 app_name: str = "ASGIApp",
                 additional_headers: List[str] = [],
                 remove_labels: List[str] = [],
                 skip_paths: List[str] = ['/metrics']):

        """
        Configuration class for PrometheusPilgrimage middleware.

        Args:
            app (ASGIApp): instance of App (starlette/FastAPI)
            app_name (str): desirable name. default = "ASGIApp"
            additional_headers (List[str]): headers that you want to watch. Default ones - ["user-agent", "host"]
            remove_labels (Tuple[str]): labels that you want to remove.
                Default labels - ["method", "path", "status_code", "headers", "app_name"]
            skip_paths (List[str]): if you dont want to log events on specific paths, pass them here. Default on '/metrics_route'

        """
        if not isinstance(additional_headers, list):
            raise TypeError("additional_headers must be list!")
        if not isinstance(remove_labels, list):
            raise TypeError("remove_labels must be list!")
        if not isinstance(skip_paths, list):
            raise TypeError("skip_paths must be list!")

        super().__init__(app)

        base_labels = ["method", "path", "status_code", "headers", "app_name"]
        [base_labels.remove(item) for item in remove_labels if item in base_labels]
        labels = list(set([item.lower() for item in base_labels]))
        if len(labels) == 0:
            raise ValueError("Labels cant be empty!")

        self.metrics = MetricsStorage(labels)

        self.app_name = app_name

        base_headers = ["user-agent", "host"]
        needed_headers = base_headers + additional_headers
        self.needed_headers = list(set([item.lower() for item in needed_headers]))

        self.skip_paths = skip_paths

    async def dispatch(self, request, call_next):
        if request.url.path not in self.skip_paths:
            method = request.method
            path = request.url.path
            headers = {key.lower(): value for key, value in request.headers.items() if
                       key.lower() in self.needed_headers}
            begin = time.time()

            status_code = status.HTTP_408_REQUEST_TIMEOUT

            try:
                response = await call_next(request)
                status_code = response.status_code

            except Exception as e:
                raise e

            finally:
                spent_time = time.time() - begin

                labels = {
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "headers": headers,
                    "app_name": self.app_name
                }

                final_labels = {
                    item: labels.get(item) for item in labels.keys() if
                    item in self.metrics.labels
                }
                self.metrics.REQUEST_COUNT.labels(**final_labels).inc()
                self.metrics.REQUEST_TIME.labels(**final_labels).observe(spent_time)
                for metric_key in self.metrics.custom_metrics:
                    metric_key.spent_time = spent_time
                    if inspect.iscoroutinefunction(metric_key.function):
                        await metric_key.function(metric_key)
                    else:
                        metric_key.function(metric_key)

            return response
        else:
            try:
                return await call_next(request)
            except Exception as e:
                raise e

import time
import inspect
from typing import List, Tuple

from prometheus_client import (
    Counter,
    Histogram,
    Gauge
)
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from prometheusrock.singleton import SingletonMeta


class MetricsStorage(metaclass=SingletonMeta):
    def __init__(self,
                 labels: List[str] = ["method", "path", "status_code", "headers", "app_name"],
                 disable_default_counter: bool = False,
                 disable_default_histogram: bool = False
                 ):
        self.labels = labels
        if not disable_default_counter:
            self.REQUEST_COUNT = Counter(
                "requests_total",
                "Total HTTP requests",
                labels,
            )

        if not disable_default_histogram:
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
                 skip_paths: List[str] = ['/metrics'],
                 disable_default_counter: bool = False,
                 disable_default_histogram: bool = False,
                 custom_base_labels: List[str] = None,
                 custom_base_headers: List[str] = None,
                 aggregate_paths: List[str] = None,
                 ):

        """
        Configuration class for PrometheusPilgrimage middleware.

        Args:
            app (ASGIApp): instance of App (starlette/FastAPI)
            app_name (str): desirable name. default = "ASGIApp"
            additional_headers (List[str]): headers that you want to watch. Default ones - ["user-agent", "host"]
            remove_labels (Tuple[str]): labels that you want to remove.
                Default labels - ["method", "path", "status_code", "headers", "app_name"]
            skip_paths (List[str]): if you dont want to log events on specific paths, pass them here.
                Default on '/metrics_route'
            disable_default_counter (bool): it is what it is. Flag to disable default counter
            disable_default_histogram (bool): it is what it is. Flag to disable default histogram
            custom_base_labels (List[str]): if you want change default labels to yours - pass them here
            custom_base_headers (List[str]): if you want change default headers to yours - pass them here
            aggregate_paths (List[str]): if you have endpoints like '/item/{id}', then, by default,
                your logs will quickly overflow, showing you huge amount of numbers, when, in fact,
                endpoint is one. So pass here list of regex endpoints path to handle it.
                example - ['/item/']

        """
        if not isinstance(additional_headers, list):
            raise TypeError("additional_headers must be list!")
        if not isinstance(remove_labels, list):
            raise TypeError("remove_labels must be list!")
        if not isinstance(skip_paths, list):
            raise TypeError("skip_paths must be list!")
        if not isinstance(custom_base_labels, list) and custom_base_labels is not None:
            raise TypeError("custom_base_labels must be list!")
        if not isinstance(custom_base_headers, list) and custom_base_headers is not None:
            raise TypeError("custom_base_headers must be list!")
        if not isinstance(aggregate_paths, list) and aggregate_paths is not None:
            raise TypeError("aggregate_paths must be list!")

        super().__init__(app)
        self.aggregate_paths = aggregate_paths
        if custom_base_labels:
            labels = custom_base_labels
        else:
            base_labels = ["method", "path", "status_code", "headers", "app_name"]
            [base_labels.remove(item) for item in remove_labels if item in base_labels]
            labels = list(set([item.lower() for item in base_labels]))
        if len(labels) == 0:
            raise ValueError("Labels cant be empty!")

        self.metrics = MetricsStorage(labels, disable_default_counter, disable_default_histogram)

        self.app_name = app_name
        if custom_base_headers:
            needed_headers = custom_base_headers
        else:
            base_headers = ["user-agent", "host"]
            needed_headers = base_headers + additional_headers

        self.needed_headers = list(set([item.lower() for item in needed_headers]))

        self.skip_paths = skip_paths

    async def dispatch(self, request, call_next):
        path = request.url.path
        if self.aggregate_paths:
            for aggregate_path in self.aggregate_paths:
                if request.url.path.startswith(aggregate_path):
                    path = aggregate_path
                    break

        if path not in self.skip_paths:
            method = request.method
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

                if hasattr(self.metrics, "REQUEST_COUNT"):
                    self.metrics.REQUEST_COUNT.labels(**final_labels).inc()

                if hasattr(self.metrics, "REQUEST_TIME"):
                    self.metrics.REQUEST_TIME.labels(**final_labels).observe(spent_time)

                for metric_key in self.metrics.custom_metrics:
                    metric_key.spent_time = spent_time
                    metric_key.request = request
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

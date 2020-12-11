from typing import List

from prometheus_client import (
    Counter,
    Histogram,
    Summary,
    Gauge,
    Info,
    Enum
)

from prometheusrock.middleware import MetricsStorage
from prometheusrock.singleton import SingletonMeta


class Metric:
    def __init__(self, metric: Counter, function: object, metric_type: str, spent_time: float = 0):
        """
        Storage of metric properties

        Args:
            metric (Info): one of prometheusrock metric types.
                Info type was chosen because we cant import from `prometheus_client' base class.
            function (object): function, that returns data that you want to add. It MUST return list or tuple.
                It may return dict if all keys are the same with metric.
            metric_type (str): assigned metric type
            spent_time (float): amount of time that was spent on request


        Attributes:
            request (obj): request object

        """
        self.metric = metric
        self.function = function
        self.metric_type = metric_type
        self.spent_time = spent_time
        self.request = None


class AddMetric:
    def __init__(self,
                 function: object,
                 metric_name: str = 'user_metric',
                 metric_description: str = 'description of user metric',
                 labels: List[str] = ["info"],
                 metric_type: str = ''):
        """
        Add your custom metric for Prometheus. Constructor for dynamic class

        Args:
            function (object): function, that returns data that you want to add. It MUST return list or tuple.
                It may return dict if all keys are the same with metric.
            metric_name (str): unique metric name, must be ONE-WORDED (e.g. unique_metric_name)
            metric_description (str): description of your metric
            labels (List[str]): list of labels for your metric
            metric_type (str): metric that you want to use: counter, histogram, summary, info, enum, gauge.
                More info about metric types you can find [here](https://github.com/prometheus/client_python)

        """
        params = self._ParamStorage(metric_name=metric_name,
                                    metric_description=metric_description,
                                    function=function,
                                    metric_type=metric_type,
                                    labels=labels)

        self._GetTheFlame(params)

    class _ParamStorage:
        def __init__(self, **kwargs):
            self.metric_name = kwargs.get('metric_name', '')
            self.metric_description = kwargs.get('metric_description', '')
            self.function = kwargs.get('function', '')
            self.labels = kwargs.get('labels', '')
            self.metric_type = kwargs.get('metric_type', '').lower()

    class _GetTheFlame:
        def __init__(self, params: '_ParamStorage'):
            self.params = params
            _custom_metric_builder = self.generate_metric_class()
            _custom_metric_builder(self.params)

        def generate_metric_class(self):
            return SingletonMeta(
                self.params.metric_name,
                (),
                {
                    "__init__": self._metric_constructor
                }
            )

        def _metric_constructor(self, params: '_ParamStorage'):
            types = {
                'counter': Counter,
                'histogram': Histogram,
                'summary': Summary,
                'info': Info,
                'enum': Enum,
                'gauge': Gauge
            }

            metric_pool = MetricsStorage()

            if types.get(params.metric_type.lower()):
                try:
                    metric = types[params.metric_type.lower()](
                        params.metric_name,
                        params.metric_description,
                        params.labels
                    )
                except ValueError:
                    raise ValueError(f"You already registered metric with name {params.metric_name}!")
            else:
                raise TypeError("""Invalid metric type! Choose of the following metric types:
                        1. counter
                        2. histogram
                        3. gauge
                        4. summary
                        5. info
                        6. enum
                        """)

            metric_pool.custom_metrics.append(
                Metric(
                    metric=metric,
                    function=params.function,
                    metric_type=params.metric_type.lower()
                )
            )

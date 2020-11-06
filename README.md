# PrometheusRock
![Python package](https://github.com/kozhushman/prometheusrock/workflows/Python%20package/badge.svg?branch=main)
![CodeQL](https://github.com/kozhushman/prometheusrock/workflows/CodeQL/badge.svg?branch=main)

Prometheus middleware for Starlette and FastAPI

This middleware collects couple of basic metrics and allow you to add your own ones.

**Basic metrics**:
* Counter: requests_total
* Histogram: request_processing_time


Basic labels for them:
* method
* path
* status_code
* User-Agent and Host headers 
* application name

Example:  
```sh
request_processing_time_sum{app_name="test_app",headers="{'host': '127.0.0.1:8020', 'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0'}",path="/test",status_code="200"} 0.00036406517028808594
```

Metrics include labels for the HTTP method, the path, and the response status code.

Set for path `/metrics` handler `metrics_route` and your metrics will be exposed on that url for Prometheus further use.

## Usage

### 1. I don't want anything custom, just give me the basics!
If you don't want nothing extra, this is for you. Grab the code and run to paste it!

For **starlette** and **FastAPI** init part pretty similar.

1. First:
    ```
    pip install prometheusrock
    ```
2. Second:

    Choose your fighter!
    If you're using starlette:
    ```python
    from starlette.applications import Starlette
   ```
   And if you're using FastAPI:
   ```python
    from fastapi import FastAPI
   ```
   Moving further:
   ```python
    from prometheusrock import PrometheusMiddleware, metrics_route
    
    app = # Starlette() or FastAPI()
    app.add_middleware(PrometheusMiddleware)
    app.add_route("/metrics", metrics_route)
    ...
    ```
    
    And that's it! Now go on `/metrics` and see your logs!
    
### 2. Custom you say? Let me see...but just a little!
If you want to configure basic metrics let me show you how!

When you declare middleware, you can pass following args:
* `app_name` - the name you want to show in metrics as the name of your app. Default - "ASGIApp",
* `additional_headers` - if you want to track additional headers (aside of default ones - `user-agent` and `host`)
you can pass `list` (that's important!) with names of that headers. They all cast to lowercase, so casing doesn't matters.
* `remove_labels` - by default basic metrics labels are following: `method`, `path`, `status_code`, `headers`, `app_name`.
If you don't wanna some of them - pass `list` with their names here. And their gone!
* `skip_paths` - sometimes you don't wanna log some of the endpoint. 
(Fore example you don't wanna log accesses to `/metrics` in your metrics).
If you want to exclude this paths from metric - pass here `list` with their urls.
By default this middleware ignores `/metrics` route, 
so if you initially moved your metric route to some other url - pass it here.
If you want to log all routes (even the default `/metrics` - pass an empty list!)
* `disable_default_counter` - if you want to disable default Counter metric - pass `True` value to this optional param.
* `disable_default_histogram` - if you want to disable default Histogram metric - pass `True` value to this optional param.


But a picture is worth a thousand words, right? Let's see some code!
For example, we want our middleware to have a following settings:
we want a name `this_is_my_app`, we want to track header `accept-encoding`, we don't wanna label `path` (if you have one endpoint for example),
and we don't want url `/_healthcheck` to be tracked.
```python
app.add_middleware(
    PrometheusMiddleware,
    app_name='this_is_my_app',
    additional_headers=['accept-encoding'],
    remove_labels=['path'],
    skip_paths=['/_healthcheck']
)
```

And after that, our metric will look something like that:
```sh
requests_total{app_name="this_is_my_app",headers="{'host': '127.0.0.1:8000', 'user-agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0', 'accept-encoding': 'gzip, deflate'}",method="GET",status_code="200"} 1.0
```

## Let's go deeper! Add your own custom metric!

And the star of the evening - custom metrics!
So, lets suppose you want to check how many are rows in your Database after each request. Let's explore this:

First, we do all the same things - we initiate the app, we add PrometheusMiddleware.
And the next steps are:
1. We must decide what type of metric we want - [choose one from here](https://github.com/prometheus/client_python). Basically, you will need pass one of the types - `info, gauge, counter, histogram, summary, enum`.
2. We declare the function that will act like our metric logic:
    ```python
   # async here isn't necessary, you can use ordinary function
    async def query(middleware_proxy):
        res = await db.execute_query(
            "SELECT COUNT(*) as count from MyTable"
        )
        middleware_proxy.metric.labels(**res)
    ```
   Function **MUST** accept this argument. Obviously you can name it however you want,
   as long is it still there. If you want to know what's inside - 
   `from prometheusrock import Metric`. I strongly recommend to pass it as typehinting:
   ```python
   from prometheusrock import Metric
   ...
   async def query(middleware_proxy: Metric):
    ```
   Metric have 3 attributes:
   * metric - instance of `prometheus_client` metric object.
   * metric_type - string with type.
   * spent_time - time, that was spent on request. You may need it if you, for example, implementing Histogram metric.
   
   And now **IMPORTANT** remark - you *must* correctly invoke metric! 
   So if you, for example, chose `Counter` metric, in your custom function you must do `middleware_proxy.metric.labels(**res).inc()`,
   or if you chose Histogram - `middleware_proxy.metric.labels(**res).observe(middleware_proxy.spent_time)` and so on,
   according to [this docs](https://github.com/prometheus/client_python).
   Value that you're passing there - `res` (or however you called it) must be a sequence of the parameters, 
   that you set as lables for your metric. For example, if your metric have labels `count` and `id`, `res` must be
   a dictionary `{"count": count, "id": id}` or list with right positioning - `[count, id]`.
   
3. And finally we tell our middleware about our custom metric:
    ```python
    from prometheusrock import AddMetric, PrometheusMiddleware
    ...
    
    app.add_middleware(PrometheusMiddleware)
    ...
    
   # async here isn't necessary, you can use ordinary function
    async def query(middleware_proxy):
        res = await db.execute_query(
            "SELECT COUNT(*) as count from MyTable"
        )
        middleware_proxy.metric.labels(**res)
   
    AddMetric(
        function=query,  
        metric_name='my_precious', 
        metric_type='info',  
        labels=['row_count']
    )
    ```
    AddMetric accept following params:
    * function - function that will work as your metric logic
    * metric_name - unique metric name, must be ONE-WORDED (e.g. unique_metric_name). Default - "user_metric".
    * metric_description- description of your metric. Default- "description of user metric".
    * labels - list of lables that you want your metric to contain. Default - ["info"].
    * metric_type - one of `prometheus_client` metric types - described in paragraph 1.
    
## Links and dependencies

Dependencies:
[Starlette](https://github.com/encode/starlette), 
[client_python](https://github.com/prometheus/client_python)

Additional links:
[FastAPI](https://github.com/tiangolo/fastapi)


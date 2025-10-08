# Logger

Xyra provides built-in logging functionality to help you monitor your application's behavior and performance.

## Startup Logging

When the server starts, Xyra automatically logs important startup information:

```
INFO - xyra - Started server process [12345]
INFO - xyra - Waiting for application startup.
INFO - xyra - Application startup complete.
INFO - xyra - Xyra server running on http://localhost:8000
INFO - xyra - API docs available at http://localhost:8000/docs
INFO - xyra - Listening on port 8000
```

## Request Logging

For each HTTP request, Xyra logs the method, URL, status code, and response time:

```
INFO - xyra - GET http://localhost:8000/ 200 5ms
INFO - xyra - POST http://localhost:8000/api/users 201 45ms
INFO - xyra - GET http://localhost:8000/api/users/1 404 12ms
```

## Controlling Logging

### Enable Full Logging

To enable startup and request logging:

```python
from xyra import App

app = App()

app.listen(8000, logger=True)
```

### Disable Request Logging (Default)

By default, only startup messages are shown and request logs are hidden:

```python
app.listen(8000)
# or explicitly
app.listen(8000, logger=False)
```

This will display startup information but not log individual requests.

## Custom Logging

You can also use the built-in logger in your application code:

```python
from xyra.logger import get_logger

logger = get_logger("my_app")
logger.info("Custom log message")
```

## Log Levels

Xyra uses Python's standard logging levels:
- DEBUG
- INFO (default for startup and requests)
- WARNING
- ERROR
- CRITICAL

## Configuration

Logging is automatically configured when the server starts. For custom configuration, you can modify the logging setup in your application.
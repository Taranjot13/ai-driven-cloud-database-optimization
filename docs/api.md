# API documentation

The backend API is implemented with FastAPI and is mounted under `/api`.

## Health

- `GET /api/health`

Returns the application health state and service name.

## Dashboard

- `GET /api/dashboard`

Returns a consolidated structure with performance summary, anomaly count, prediction, optimization summary, resource data, cost data, and learning status.

## Performance

- `GET /api/performance`
- `GET /api/performance/summary`
- `GET /api/slow-queries`

These endpoints expose query-level metrics and summary statistics for latency and slow query detection.

## Anomalies

- `GET /api/anomalies`

Returns the anomaly status for recent workload observations using the Isolation Forest result.

## Predictions

- `GET /api/predictions`

Returns the prediction status, historical averages, maximum observed latencies, and the estimated next execution time when enough data is available.

## Optimization

- `GET /api/optimization/history`
- `GET /api/optimization/summary`
- `POST /api/optimization/analyze`
- `POST /api/optimization/execute`

The analyze endpoint produces a preview decision. The execute endpoint requires `confirmed: true` and checks that the preview is still valid before running a safe action.

## Resources and cost

- `GET /api/resources`
- `GET /api/costs`

These endpoints provide operational status and cloud-agnostic reference cost metrics. They are read-only and are not treated as live billing data.

## System status

- `GET /api/system/status`

Returns database connectivity and a list of implemented system modules.

## Safety behavior

- Read-only pages remain safe by default.
- Optimization changes require explicit user confirmation.
- The system validates the requested action before executing it.
- The optimization result is not silently applied when the action is not executable or the preview has become stale.

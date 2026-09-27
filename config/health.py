"""Health check for ECS / the load balancer.

Why a middleware and not a normal view?
AWS health checks call the container by its private IP (e.g. http://10.0.1.25:8000/health/).
That IP is not in ALLOWED_HOSTS, so a normal view would answer 400 and ECS would kill the task.
This middleware sits FIRST and answers before Django checks the host.
"""
from django.db import connection
from django.http import JsonResponse


class HealthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/health/":                    # liveness: is the process up?
            return JsonResponse({"status": "ok"})
        if request.path == "/health/db/":                 # readiness: can we reach the database (RDS)?
            try:
                with connection.cursor() as cursor:
                    # Phase 6 helper: how many connections are open to this database right now
                    # (RDS is private, so this saves you from needing psql access)
                    cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()")
                    open_connections = cursor.fetchone()[0]
                return JsonResponse({"status": "ok", "db": "ok", "db_connections": open_connections})
            except Exception as exc:                      # show why, so you can debug security groups / SSL
                return JsonResponse({"status": "error", "db": str(exc)[:200]}, status=503)
        return self.get_response(request)                 # every other URL: normal Django

"""Tests for the ECS health check (config/health.py)."""
from django.test import SimpleTestCase, TestCase


class HealthCheckTests(TestCase):
    def test_health_works_even_for_an_unknown_host(self):
        # ECS/ALB call the container by its private IP, which is NOT in ALLOWED_HOSTS
        res = self.client.get("/health/", HTTP_HOST="10.0.1.25:8000")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"status": "ok"})

    def test_db_health_runs_a_query(self):
        res = self.client.get("/health/db/", HTTP_HOST="10.0.1.25:8000")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["db"], "ok")
        self.assertGreaterEqual(res.json()["db_connections"], 1)   # at least our own connection


class AllowedHostsStillProtectedTests(SimpleTestCase):
    def test_other_urls_still_reject_unknown_hosts(self):
        # the health bypass must NOT switch off host checking for the real API
        res = self.client.get("/api/v1/products/", HTTP_HOST="evil.example.com")
        self.assertEqual(res.status_code, 400)

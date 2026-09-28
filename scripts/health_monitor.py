#!/usr/bin/env python3
"""
Standard El-Joumla ERP — Deployment Health Monitor
Monitors the application after deployment and triggers rollback if unhealthy.

Usage:
    python scripts/health_monitor.py --url=http://localhost:8000/api/v1/health --duration=300
    python scripts/health_monitor.py --url=https://erp.example.com/api/v1/health --rollback-cmd="bash scripts/deploy.sh production rollback"
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from typing import Optional

import urllib.request
import urllib.error

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("health-monitor")


class HealthMonitor:
    """Monitors application health and triggers rollback on failure."""

    def __init__(
        self,
        url: str,
        duration: int = 300,
        interval: int = 10,
        error_threshold: int = 3,
        latency_threshold: float = 5.0,
        rollback_cmd: Optional[str] = None,
        webhook_url: Optional[str] = None,
    ):
        self.url = url
        self.duration = duration
        self.interval = interval
        self.error_threshold = error_threshold
        self.latency_threshold = latency_threshold
        self.rollback_cmd = rollback_cmd
        self.webhook_url = webhook_url

        self.consecutive_errors = 0
        self.total_checks = 0
        self.total_errors = 0
        self.start_time = time.time()

    def check_health(self) -> dict:
        """Perform a single health check."""
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "url": self.url,
            "status": "unknown",
            "latency_ms": 0,
            "error": None,
        }

        try:
            start = time.time()
            req = urllib.request.Request(self.url, method="GET")
            req.add_header("Accept", "application/json")

            with urllib.request.urlopen(req, timeout=10) as resp:
                latency = (time.time() - start) * 1000
                body = resp.read().decode("utf-8")

                result["status"] = "healthy"
                result["latency_ms"] = round(latency, 1)
                result["response_code"] = resp.status

                try:
                    data = json.loads(body)
                    result["version"] = data.get("version", "unknown")
                except json.JSONDecodeError:
                    pass

        except urllib.error.HTTPError as e:
            latency = (time.time() - start) * 1000
            result["status"] = "unhealthy"
            result["latency_ms"] = round(latency, 1)
            result["response_code"] = e.code
            result["error"] = f"HTTP {e.code}"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        return result

    def should_rollback(self, result: dict) -> bool:
        """Determine if rollback should be triggered."""
        if result["status"] in ("unhealthy", "error"):
            self.consecutive_errors += 1
            self.total_errors += 1
            if self.consecutive_errors >= self.error_threshold:
                return True
        else:
            self.consecutive_errors = 0
            if result["latency_ms"] > self.latency_threshold * 1000:
                logger.warning(
                    "⚠️  High latency: %.0fms (threshold: %.0fms)",
                    result["latency_ms"],
                    self.latency_threshold * 1000,
                )

        return False

    def trigger_rollback(self):
        """Execute rollback command."""
        logger.error("🔙 TRIGGERING ROLLBACK — %d consecutive errors", self.consecutive_errors)

        if self.webhook_url:
            self._send_webhook("rollback_triggered")

        if self.rollback_cmd:
            try:
                result = subprocess.run(
                    self.rollback_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                logger.info("Rollback command exit code: %d", result.returncode)
                if result.stdout:
                    logger.info("Rollback stdout: %s", result.stdout[:500])
                if result.returncode == 0:
                    logger.info("✅ Rollback completed successfully")
                else:
                    logger.error("❌ Rollback failed: %s", result.stderr[:500])
            except Exception as e:
                logger.error("❌ Rollback command failed: %s", e)
        else:
            logger.warning("No rollback command configured")

    def _send_webhook(self, event: str):
        """Send notification webhook."""
        if not self.webhook_url:
            return
        payload = json.dumps({
            "event": event,
            "url": self.url,
            "consecutive_errors": self.consecutive_errors,
            "total_errors": self.total_errors,
            "timestamp": datetime.utcnow().isoformat(),
        }).encode()
        try:
            req = urllib.request.Request(
                self.webhook_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=10)
        except Exception as e:
            logger.warning("Webhook failed: %s", e)

    def run(self) -> int:
        """Run the health monitoring loop."""
        logger.info(
            "🔍 Health Monitor started: %s (duration=%ds, interval=%ds, threshold=%d)",
            self.url, self.duration, self.interval, self.error_threshold,
        )

        while True:
            elapsed = time.time() - self.start_time
            if elapsed >= self.duration:
                logger.info(
                    "✅ Monitoring complete: %d checks, %d errors (%.1f%% error rate)",
                    self.total_checks,
                    self.total_errors,
                    (self.total_errors / max(self.total_checks, 1)) * 100,
                )
                return 0

            result = self.check_health()
            self.total_checks += 1

            # Log result
            status_icon = "✅" if result["status"] == "healthy" else "❌"
            logger.info(
                "%s [%d/%d] %s — %s (%.0fms)",
                status_icon,
                self.total_checks,
                self.consecutive_errors,
                result["status"],
                result.get("error", "OK"),
                result["latency_ms"],
            )

            # Check for rollback
            if self.should_rollback(result):
                self.trigger_rollback()
                return 1

            time.sleep(self.interval)


def main():
    parser = argparse.ArgumentParser(description="ERP Deployment Health Monitor")
    parser.add_argument("--url", required=True, help="Health check endpoint URL")
    parser.add_argument("--duration", type=int, default=300, help="Monitoring duration in seconds")
    parser.add_argument("--interval", type=int, default=10, help="Check interval in seconds")
    parser.add_argument("--error-threshold", type=int, default=3, help="Consecutive errors before rollback")
    parser.add_argument("--latency-threshold", type=float, default=5.0, help="Latency threshold in seconds")
    parser.add_argument("--rollback-cmd", default=None, help="Command to execute on rollback")
    parser.add_argument("--webhook-url", default=None, help="Webhook URL for notifications")
    args = parser.parse_args()

    monitor = HealthMonitor(
        url=args.url,
        duration=args.duration,
        interval=args.interval,
        error_threshold=args.error_threshold,
        latency_threshold=args.latency_threshold,
        rollback_cmd=args.rollback_cmd,
        webhook_url=args.webhook_url,
    )

    sys.exit(monitor.run())


if __name__ == "__main__":
    main()

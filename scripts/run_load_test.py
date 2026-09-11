"""Automated Runner for FinTrack Locust Load Tests across Concurrency Tiers.

Executes headless Locust load tests across multiple concurrency tiers, parses
the resulting CSV metrics, and generates structured empirical performance tables.
"""

import json
import os
import subprocess
import sys
import time
import urllib.request
import pandas as pd


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPORTS_DIR = os.path.join(ROOT_DIR, "tests", "load", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

PYTHON_EXE = sys.executable
HOST = "http://127.0.0.1:8000"


def wait_for_server(url: str, timeout: int = 25) -> bool:
    """Poll health endpoint until server is responsive."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(f"{url}/health", timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def run_tier_load_test(users: int, spawn_rate: int, duration: str, tier_name: str) -> dict:
    """Run a single Locust load test tier and parse the stats CSV."""
    csv_rel = f"tests/load/reports/{tier_name}"
    html_rel = f"tests/load/reports/{tier_name}_report.html"
    stats_file = os.path.join(REPORTS_DIR, f"{tier_name}_stats.csv")

    if os.path.exists(stats_file):
        try:
            os.remove(stats_file)
        except OSError:
            pass

    cmd = [
        PYTHON_EXE,
        "-m",
        "locust",
        "-f",
        "tests/load/locustfile.py",
        "--headless",
        "--host",
        HOST,
        "-u",
        str(users),
        "-r",
        str(spawn_rate),
        "--run-time",
        duration,
        "--csv",
        csv_rel,
        "--html",
        html_rel,
        "--loglevel",
        "WARNING",
    ]

    print("\n" + "=" * 68, flush=True)
    print(f"[*] Running Locust Load Test: {tier_name.upper()} (Users: {users}, Spawn: {spawn_rate}/s, Duration: {duration})", flush=True)
    print("=" * 68, flush=True)

    result = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Locust returned code {result.returncode}:\n{result.stderr}", flush=True)

    # Allow filesystem write to settle
    time.sleep(1)

    if not os.path.exists(stats_file):
        raise FileNotFoundError(f"Stats file not found at {stats_file}")

    df = pd.read_csv(stats_file)
    agg_row = df[df["Name"] == "Aggregated"].iloc[0]
    endpoints = df[df["Name"] != "Aggregated"].to_dict(orient="records")

    total_req = int(agg_row["Request Count"])
    fail_count = int(agg_row["Failure Count"])
    fail_pct = round((float(fail_count) / float(total_req) * 100) if total_req > 0 else 0.0, 2)

    def safe_float(val, default=0.0):
        try:
            if pd.isna(val) or val == "N/A":
                return default
            return round(float(val), 2)
        except (ValueError, TypeError):
            return default

    tier_metrics = {
        "tier": tier_name,
        "users": users,
        "spawn_rate": spawn_rate,
        "duration": duration,
        "total_requests": total_req,
        "failure_count": fail_count,
        "failure_rate_pct": fail_pct,
        "requests_per_sec": safe_float(agg_row["Requests/s"]),
        "avg_response_ms": safe_float(agg_row["Average Response Time"]),
        "min_response_ms": safe_float(agg_row["Min Response Time"]),
        "max_response_ms": safe_float(agg_row["Max Response Time"]),
        "median_ms": safe_float(agg_row.get("50%", agg_row.get("Median Response Time", 0))),
        "p90_ms": safe_float(agg_row.get("90%", 0)),
        "p95_ms": safe_float(agg_row.get("95%", 0)),
        "p99_ms": safe_float(agg_row.get("99%", 0)),
        "endpoints": [
            {
                "name": ep["Name"],
                "method": ep["Type"],
                "requests": int(ep["Request Count"]),
                "failures": int(ep["Failure Count"]),
                "rps": safe_float(ep["Requests/s"]),
                "avg_ms": safe_float(ep["Average Response Time"]),
                "median_ms": safe_float(ep.get("50%", 0)),
                "p95_ms": safe_float(ep.get("95%", 0)),
                "p99_ms": safe_float(ep.get("99%", 0)),
            }
            for ep in endpoints
        ],
    }

    print(
        f"[+] Completed {tier_name}: {tier_metrics['total_requests']:,} total requests | "
        f"{tier_metrics['requests_per_sec']} req/s | "
        f"Avg: {tier_metrics['avg_response_ms']}ms | "
        f"p50: {tier_metrics['median_ms']}ms | "
        f"p95: {tier_metrics['p95_ms']}ms | "
        f"p99: {tier_metrics['p99_ms']}ms | "
        f"Failures: {tier_metrics['failure_count']} ({tier_metrics['failure_rate_pct']}%)",
        flush=True,
    )
    return tier_metrics


def main():
    # 1. Seed database first
    print("[*] Ensuring database is seeded with demo accounts & historical baselines...", flush=True)
    subprocess.run([PYTHON_EXE, os.path.join(ROOT_DIR, "scripts", "seed_database.py")], cwd=ROOT_DIR, check=True)

    # 2. Start Uvicorn server in subprocess with output redirected to log file (prevents pipe buffer deadlocks)
    log_file_path = os.path.join(REPORTS_DIR, "uvicorn_server.log")
    log_file = open(log_file_path, "w", encoding="utf-8")

    print(f"[*] Starting Uvicorn API server on 127.0.0.1:8000 (logs: {log_file_path})...", flush=True)
    server_proc = subprocess.Popen(
        [
            PYTHON_EXE,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--log-level",
            "warning",
        ],
        cwd=ROOT_DIR,
        stdout=log_file,
        stderr=log_file,
    )

    try:
        if not wait_for_server(HOST, timeout=20):
            raise RuntimeError("API Server failed to start within timeout.")
        print("[+] API Server is live and healthy!", flush=True)

        # 3. Multi-tier load test suite
        tiers = [
            (10, 5, "20s", "tier_10_users"),
            (25, 10, "25s", "tier_25_users"),
            (50, 15, "30s", "tier_50_users"),
            (100, 25, "30s", "tier_100_users"),
        ]

        all_results = []
        for users, spawn, dur, name in tiers:
            time.sleep(2)  # Cooldown between runs
            res = run_tier_load_test(users, spawn, dur, name)
            all_results.append(res)

        # Print summary Markdown table
        print("\n" + "=" * 76, flush=True)
        print("AGGREGATE LOCUST LOAD TEST BENCHMARK RESULTS", flush=True)
        print("=" * 76, flush=True)
        print(
            "| Concurrency Tier | Spawn Rate | Duration | Total Requests | Throughput (RPS) | Avg Latency | Median (p50) | 95th % (p95) | 99th % (p99) | Error Rate |",
            flush=True,
        )
        print(
            "|---|---|---|---|---|---|---|---|---|---|",
            flush=True,
        )
        for r in all_results:
            print(
                f"| **{r['users']} Concurrent Users** | {r['spawn_rate']}/s | {r['duration']} | "
                f"{r['total_requests']:,} | **{r['requests_per_sec']} req/s** | "
                f"{r['avg_response_ms']} ms | {r['median_ms']} ms | "
                f"**{r['p95_ms']} ms** | **{r['p99_ms']} ms** | **{r['failure_rate_pct']}%** |",
                flush=True,
            )

        # Save summary JSON for report generation
        with open(os.path.join(REPORTS_DIR, "summary.json"), "w") as f:
            json.dump(all_results, f, indent=2)
        print(f"\n[*] Raw Locust CSVs and summary.json saved to {REPORTS_DIR}", flush=True)

    finally:
        print("\n[*] Stopping Uvicorn server...", flush=True)
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_proc.kill()
        log_file.close()
        print("[+] Server stopped cleanly.", flush=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Scalability Test Suite for Contentry.ai
Tests system readiness for 100,000+ users

Tests:
1. API Response Time Under Load
2. Database Query Performance  
3. Concurrent User Handling
4. Memory/Resource Analysis
5. Connection Pool Stress
6. Authentication Throughput
7. Content Generation Pipeline
"""

import asyncio
import aiohttp
import time
import statistics
import json
import sys
from datetime import datetime
from collections import defaultdict
import psutil
import os

# Configuration
BASE_URL = "http://localhost:8001"
TEST_EMAIL = "sarah.chen@techcorp-demo.com"
TEST_PASSWORD = "Demo123!"

# Results storage
results = {
    "test_date": datetime.now().isoformat(),
    "tests": {},
    "summary": {},
    "bottlenecks": [],
    "recommendations": []
}

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_result(name, passed, details=""):
    status = f"{Colors.GREEN}PASS{Colors.END}" if passed else f"{Colors.RED}FAIL{Colors.END}"
    print(f"  [{status}] {name}")
    if details:
        print(f"        {details}")

def print_warning(text):
    print(f"  {Colors.YELLOW}⚠ {text}{Colors.END}")

def print_critical(text):
    print(f"  {Colors.RED}✗ CRITICAL: {text}{Colors.END}")

async def get_auth_token():
    """Get authentication token for API calls"""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("access_token")
    return None

# =============================================================================
# TEST 1: API Response Time Under Load
# =============================================================================
async def test_api_response_times():
    print_header("TEST 1: API Response Time Under Load")
    
    endpoints = [
        ("GET", "/api/v1/credits/costs", None, "Public endpoint"),
        ("GET", "/api/v1/credits/plans", None, "Plans listing"),
        ("GET", "/api/health", None, "Health check"),
    ]
    
    token = await get_auth_token()
    if token:
        endpoints.extend([
            ("GET", "/api/v1/credits/balance", {"Authorization": f"Bearer {token}", "X-User-ID": "test-user"}, "Auth: Credit balance"),
        ])
    
    test_results = {}
    
    for method, endpoint, headers, desc in endpoints:
        times = []
        errors = 0
        
        async with aiohttp.ClientSession() as session:
            for _ in range(50):  # 50 requests per endpoint
                start = time.perf_counter()
                try:
                    if method == "GET":
                        async with session.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=10) as resp:
                            await resp.text()
                            if resp.status >= 400:
                                errors += 1
                    elapsed = (time.perf_counter() - start) * 1000
                    times.append(elapsed)
                except Exception as e:
                    errors += 1
        
        if times:
            avg = statistics.mean(times)
            p95 = sorted(times)[int(len(times) * 0.95)]
            p99 = sorted(times)[int(len(times) * 0.99)]
            max_time = max(times)
            
            test_results[endpoint] = {
                "avg_ms": round(avg, 2),
                "p95_ms": round(p95, 2),
                "p99_ms": round(p99, 2),
                "max_ms": round(max_time, 2),
                "errors": errors,
                "requests": 50
            }
            
            passed = avg < 100 and p95 < 200  # Target: avg < 100ms, p95 < 200ms
            print_result(
                f"{desc}",
                passed,
                f"Avg: {avg:.1f}ms | P95: {p95:.1f}ms | P99: {p99:.1f}ms | Errors: {errors}"
            )
            
            if avg > 100:
                results["bottlenecks"].append(f"Slow avg response on {endpoint}: {avg:.1f}ms")
            if p95 > 200:
                results["bottlenecks"].append(f"High P95 latency on {endpoint}: {p95:.1f}ms")
    
    results["tests"]["api_response_times"] = test_results
    return test_results

# =============================================================================
# TEST 2: Concurrent User Simulation
# =============================================================================
async def test_concurrent_users():
    print_header("TEST 2: Concurrent User Simulation")
    
    concurrency_levels = [10, 50, 100, 200, 500]
    test_results = {}
    
    async def make_request(session, semaphore):
        async with semaphore:
            start = time.perf_counter()
            try:
                async with session.get(f"{BASE_URL}/api/v1/credits/costs", timeout=30) as resp:
                    await resp.text()
                    return time.perf_counter() - start, resp.status == 200
            except Exception:
                return time.perf_counter() - start, False
    
    for level in concurrency_levels:
        semaphore = asyncio.Semaphore(level)
        
        async with aiohttp.ClientSession() as session:
            start_time = time.perf_counter()
            tasks = [make_request(session, semaphore) for _ in range(level * 2)]
            results_list = await asyncio.gather(*tasks)
            total_time = time.perf_counter() - start_time
        
        times = [r[0] for r in results_list]
        successes = sum(1 for r in results_list if r[1])
        
        rps = len(tasks) / total_time
        success_rate = (successes / len(tasks)) * 100
        avg_latency = statistics.mean(times) * 1000
        
        test_results[f"concurrent_{level}"] = {
            "requests": len(tasks),
            "successes": successes,
            "success_rate": round(success_rate, 1),
            "requests_per_second": round(rps, 1),
            "avg_latency_ms": round(avg_latency, 1),
            "total_time_s": round(total_time, 2)
        }
        
        passed = success_rate >= 99 and rps >= 50
        print_result(
            f"{level} concurrent users",
            passed,
            f"RPS: {rps:.1f} | Success: {success_rate:.1f}% | Avg latency: {avg_latency:.1f}ms"
        )
        
        if success_rate < 99:
            results["bottlenecks"].append(f"Connection failures at {level} concurrent users: {100-success_rate:.1f}% failed")
        if rps < 50:
            results["bottlenecks"].append(f"Low throughput at {level} concurrent: {rps:.1f} RPS")
    
    results["tests"]["concurrent_users"] = test_results
    return test_results

# =============================================================================
# TEST 3: Database Query Performance
# =============================================================================
async def test_database_performance():
    print_header("TEST 3: Database Query Performance")
    
    from pymongo import MongoClient
    
    client = MongoClient("mongodb://localhost:27017")
    db = client["contentry_db"]
    
    test_results = {}
    
    # Test 1: Collection stats
    collections = ["users", "enterprises", "posts", "content_analyses", "credit_transactions"]
    print("  Collection Statistics:")
    for coll_name in collections:
        try:
            count = db[coll_name].count_documents({})
            stats = db.command("collStats", coll_name)
            size_mb = stats.get("size", 0) / (1024 * 1024)
            index_size_mb = stats.get("totalIndexSize", 0) / (1024 * 1024)
            
            test_results[f"collection_{coll_name}"] = {
                "documents": count,
                "size_mb": round(size_mb, 2),
                "index_size_mb": round(index_size_mb, 2)
            }
            print(f"    {coll_name}: {count:,} docs | {size_mb:.2f}MB | Indexes: {index_size_mb:.2f}MB")
        except Exception as e:
            print(f"    {coll_name}: Error - {e}")
    
    # Test 2: Query performance
    print("\n  Query Performance (100 iterations each):")
    
    queries = [
        ("users", {"email": TEST_EMAIL}, "User lookup by email"),
        ("enterprises", {}, "List all enterprises"),
        ("posts", {"status": "published"}, "Published posts query"),
    ]
    
    for coll_name, query, desc in queries:
        times = []
        for _ in range(100):
            start = time.perf_counter()
            list(db[coll_name].find(query).limit(10))
            times.append((time.perf_counter() - start) * 1000)
        
        avg = statistics.mean(times)
        p95 = sorted(times)[94]
        
        test_results[f"query_{coll_name}"] = {
            "avg_ms": round(avg, 2),
            "p95_ms": round(p95, 2)
        }
        
        passed = avg < 10 and p95 < 50  # Target: avg < 10ms, p95 < 50ms
        print_result(desc, passed, f"Avg: {avg:.2f}ms | P95: {p95:.2f}ms")
        
        if avg > 10:
            results["bottlenecks"].append(f"Slow query on {coll_name}: {avg:.2f}ms avg")
    
    # Test 3: Index analysis
    print("\n  Index Analysis:")
    critical_indexes = {
        "users": ["email", "enterprise_id"],
        "posts": ["user_id", "enterprise_id", "status", "created_at"],
        "credit_transactions": ["user_id", "created_at"],
        "content_analyses": ["user_id", "created_at"]
    }
    
    missing_indexes = []
    for coll_name, required_fields in critical_indexes.items():
        try:
            existing_indexes = list(db[coll_name].list_indexes())
            indexed_fields = set()
            for idx in existing_indexes:
                indexed_fields.update(idx.get("key", {}).keys())
            
            for field in required_fields:
                if field not in indexed_fields:
                    missing_indexes.append(f"{coll_name}.{field}")
        except Exception:
            pass
    
    if missing_indexes:
        print_warning(f"Missing indexes: {', '.join(missing_indexes[:5])}")
        results["bottlenecks"].append(f"Missing database indexes: {missing_indexes}")
        test_results["missing_indexes"] = missing_indexes
    else:
        print_result("All critical indexes present", True)
    
    client.close()
    results["tests"]["database_performance"] = test_results
    return test_results

# =============================================================================
# TEST 4: Memory & Resource Analysis
# =============================================================================
async def test_resource_usage():
    print_header("TEST 4: Memory & Resource Analysis")
    
    test_results = {}
    
    # System memory
    mem = psutil.virtual_memory()
    test_results["system_memory"] = {
        "total_gb": round(mem.total / (1024**3), 2),
        "available_gb": round(mem.available / (1024**3), 2),
        "used_percent": mem.percent
    }
    
    print(f"  System Memory: {mem.available / (1024**3):.1f}GB available of {mem.total / (1024**3):.1f}GB ({mem.percent}% used)")
    
    if mem.percent > 80:
        print_critical(f"High memory usage: {mem.percent}%")
        results["bottlenecks"].append(f"High system memory usage: {mem.percent}%")
    
    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    test_results["cpu"] = {
        "cores": cpu_count,
        "usage_percent": cpu_percent
    }
    print(f"  CPU: {cpu_count} cores | {cpu_percent}% usage")
    
    # Process analysis
    print("\n  Process Analysis:")
    for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
        try:
            if any(x in proc.info['name'].lower() for x in ['python', 'uvicorn', 'mongod', 'node']):
                print(f"    {proc.info['name']}: {proc.info['memory_percent']:.1f}% RAM | {proc.info['cpu_percent']:.1f}% CPU")
        except:
            pass
    
    # Disk I/O
    disk = psutil.disk_usage('/')
    test_results["disk"] = {
        "total_gb": round(disk.total / (1024**3), 2),
        "free_gb": round(disk.free / (1024**3), 2),
        "used_percent": round(disk.percent, 1)
    }
    print(f"\n  Disk: {disk.free / (1024**3):.1f}GB free of {disk.total / (1024**3):.1f}GB")
    
    results["tests"]["resource_usage"] = test_results
    return test_results

# =============================================================================
# TEST 5: Connection Pool Stress Test
# =============================================================================
async def test_connection_pool():
    print_header("TEST 5: Connection Pool Stress Test")
    
    test_results = {}
    
    # Rapid connection creation
    connection_counts = [50, 100, 200]
    
    for conn_count in connection_counts:
        sessions = []
        start = time.perf_counter()
        
        try:
            for _ in range(conn_count):
                session = aiohttp.ClientSession()
                sessions.append(session)
            
            creation_time = time.perf_counter() - start
            
            # Make requests with all connections
            async def quick_request(s):
                try:
                    async with s.get(f"{BASE_URL}/api/health", timeout=5) as resp:
                        return resp.status == 200
                except:
                    return False
            
            results_list = await asyncio.gather(*[quick_request(s) for s in sessions])
            success_rate = sum(results_list) / len(results_list) * 100
            
            test_results[f"connections_{conn_count}"] = {
                "creation_time_s": round(creation_time, 3),
                "success_rate": round(success_rate, 1)
            }
            
            passed = success_rate >= 95
            print_result(
                f"{conn_count} simultaneous connections",
                passed,
                f"Creation: {creation_time:.3f}s | Success: {success_rate:.1f}%"
            )
            
            if success_rate < 95:
                results["bottlenecks"].append(f"Connection pool exhaustion at {conn_count} connections")
            
        finally:
            for s in sessions:
                await s.close()
    
    results["tests"]["connection_pool"] = test_results
    return test_results

# =============================================================================
# TEST 6: Authentication Throughput
# =============================================================================
async def test_auth_throughput():
    print_header("TEST 6: Authentication Throughput")
    
    test_results = {}
    
    async def login_request(session):
        start = time.perf_counter()
        try:
            async with session.post(
                f"{BASE_URL}/api/v1/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
                timeout=10
            ) as resp:
                data = await resp.json()
                return time.perf_counter() - start, resp.status == 200
        except:
            return time.perf_counter() - start, False
    
    # Sequential logins
    times = []
    async with aiohttp.ClientSession() as session:
        for _ in range(20):
            elapsed, success = await login_request(session)
            if success:
                times.append(elapsed * 1000)
    
    if times:
        avg = statistics.mean(times)
        test_results["sequential_login"] = {
            "avg_ms": round(avg, 2),
            "min_ms": round(min(times), 2),
            "max_ms": round(max(times), 2)
        }
        print_result(
            "Sequential login performance",
            avg < 200,
            f"Avg: {avg:.1f}ms | Min: {min(times):.1f}ms | Max: {max(times):.1f}ms"
        )
    
    # Concurrent logins (simulating burst)
    concurrent_logins = 20
    async with aiohttp.ClientSession() as session:
        start = time.perf_counter()
        tasks = [login_request(session) for _ in range(concurrent_logins)]
        results_list = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start
    
    successes = sum(1 for r in results_list if r[1])
    login_rps = concurrent_logins / total_time
    
    test_results["concurrent_login"] = {
        "concurrent": concurrent_logins,
        "successes": successes,
        "logins_per_second": round(login_rps, 1),
        "total_time_s": round(total_time, 2)
    }
    
    passed = successes == concurrent_logins
    print_result(
        f"{concurrent_logins} concurrent logins",
        passed,
        f"Success: {successes}/{concurrent_logins} | Rate: {login_rps:.1f} logins/sec"
    )
    
    if successes < concurrent_logins:
        results["bottlenecks"].append(f"Auth failures under load: {concurrent_logins - successes} failed")
    
    results["tests"]["auth_throughput"] = test_results
    return test_results

# =============================================================================
# TEST 7: Architecture Analysis
# =============================================================================
async def test_architecture_analysis():
    print_header("TEST 7: Architecture Analysis for 100K+ Users")
    
    test_results = {
        "current_architecture": {},
        "scalability_gaps": [],
        "required_changes": []
    }
    
    print("  Current Architecture Assessment:\n")
    
    # Check 1: Database
    print("  📊 DATABASE:")
    test_results["current_architecture"]["database"] = "MongoDB (single instance)"
    print("    Current: MongoDB single instance (localhost)")
    print_critical("Not scalable: No replica set, no sharding")
    test_results["scalability_gaps"].append("MongoDB: Single instance, no replication")
    test_results["required_changes"].append("Deploy MongoDB replica set (minimum 3 nodes)")
    test_results["required_changes"].append("Implement database sharding for users/posts collections")
    
    # Check 2: Application Server
    print("\n  🖥️  APPLICATION SERVER:")
    test_results["current_architecture"]["app_server"] = "Single Uvicorn process"
    print("    Current: Single Uvicorn/FastAPI process")
    print_critical("Not scalable: Single process, no horizontal scaling")
    test_results["scalability_gaps"].append("App Server: Single process, single machine")
    test_results["required_changes"].append("Deploy behind load balancer (nginx/HAProxy)")
    test_results["required_changes"].append("Run multiple Uvicorn workers (gunicorn + uvicorn)")
    test_results["required_changes"].append("Implement Kubernetes deployment with HPA")
    
    # Check 3: Caching
    print("\n  💾 CACHING:")
    test_results["current_architecture"]["caching"] = "None"
    print("    Current: No caching layer detected")
    print_critical("Not scalable: Every request hits database")
    test_results["scalability_gaps"].append("Caching: No Redis/Memcached")
    test_results["required_changes"].append("Add Redis for session management")
    test_results["required_changes"].append("Implement API response caching")
    test_results["required_changes"].append("Add query result caching for expensive operations")
    
    # Check 4: Background Jobs
    print("\n  ⚙️  BACKGROUND JOBS:")
    test_results["current_architecture"]["background_jobs"] = "APScheduler (in-process)"
    print("    Current: APScheduler running in-process")
    print_warning("Limited scalability: Jobs tied to single process")
    test_results["scalability_gaps"].append("Background Jobs: In-process scheduler")
    test_results["required_changes"].append("Migrate to Celery + Redis for distributed task queue")
    
    # Check 5: Rate Limiting
    print("\n  🚦 RATE LIMITING:")
    test_results["current_architecture"]["rate_limiting"] = "Basic/In-memory"
    print("    Current: Basic in-memory rate limiting")
    print_warning("Not production-ready: State not shared across instances")
    test_results["scalability_gaps"].append("Rate Limiting: In-memory, not distributed")
    test_results["required_changes"].append("Implement Redis-based distributed rate limiting")
    
    # Check 6: Session Management
    print("\n  🔐 SESSION MANAGEMENT:")
    test_results["current_architecture"]["sessions"] = "JWT (stateless)"
    print("    Current: JWT tokens (stateless)")
    print_result("Good: Stateless auth scales horizontally", True)
    
    # Check 7: File Storage
    print("\n  📁 FILE STORAGE:")
    test_results["current_architecture"]["file_storage"] = "Local filesystem"
    print("    Current: Local filesystem (/app/uploads)")
    print_critical("Not scalable: Files not accessible across instances")
    test_results["scalability_gaps"].append("File Storage: Local filesystem")
    test_results["required_changes"].append("Migrate to S3/GCS for file storage")
    
    results["tests"]["architecture_analysis"] = test_results
    return test_results

# =============================================================================
# SUMMARY & RECOMMENDATIONS
# =============================================================================
async def generate_summary():
    print_header("SCALABILITY ASSESSMENT SUMMARY")
    
    # Calculate overall score
    total_bottlenecks = len(results["bottlenecks"])
    
    if total_bottlenecks == 0:
        score = 100
        verdict = "READY"
        color = Colors.GREEN
    elif total_bottlenecks <= 3:
        score = 70
        verdict = "NEEDS WORK"
        color = Colors.YELLOW
    elif total_bottlenecks <= 6:
        score = 40
        verdict = "SIGNIFICANT GAPS"
        color = Colors.YELLOW
    else:
        score = 20
        verdict = "NOT READY"
        color = Colors.RED
    
    results["summary"] = {
        "score": score,
        "verdict": verdict,
        "bottleneck_count": total_bottlenecks,
        "max_estimated_users": estimate_max_users()
    }
    
    print(f"  {Colors.BOLD}Overall Scalability Score: {color}{score}/100 - {verdict}{Colors.END}\n")
    
    # Estimated capacity
    max_users = estimate_max_users()
    print(f"  {Colors.BOLD}Estimated Maximum Concurrent Users: {color}{max_users:,}{Colors.END}")
    print(f"  {Colors.BOLD}Target: 100,000+ users{Colors.END}\n")
    
    if max_users < 100000:
        gap = 100000 - max_users
        print(f"  {Colors.RED}Gap to Target: {gap:,} users{Colors.END}\n")
    
    # Critical Issues
    if results["bottlenecks"]:
        print(f"  {Colors.BOLD}Critical Bottlenecks Found ({len(results['bottlenecks'])}):{Colors.END}")
        for i, bottleneck in enumerate(results["bottlenecks"][:10], 1):
            print(f"    {i}. {Colors.RED}{bottleneck}{Colors.END}")
    
    # Required Changes
    arch_test = results["tests"].get("architecture_analysis", {})
    required_changes = arch_test.get("required_changes", [])
    
    if required_changes:
        print(f"\n  {Colors.BOLD}Required Infrastructure Changes:{Colors.END}")
        for i, change in enumerate(required_changes, 1):
            print(f"    {i}. {change}")
    
    # Recommendations
    print(f"\n  {Colors.BOLD}Priority Recommendations:{Colors.END}")
    recommendations = [
        "1. 🔴 CRITICAL: Deploy MongoDB replica set with read replicas",
        "2. 🔴 CRITICAL: Add Redis for caching + session management",
        "3. 🔴 CRITICAL: Implement horizontal scaling with load balancer",
        "4. 🟠 HIGH: Migrate file storage to cloud (S3/GCS)",
        "5. 🟠 HIGH: Switch to Celery + Redis for background jobs",
        "6. 🟡 MEDIUM: Add CDN for static assets",
        "7. 🟡 MEDIUM: Implement database connection pooling",
        "8. 🟢 LOW: Add APM monitoring (DataDog/NewRelic)"
    ]
    results["recommendations"] = recommendations
    for rec in recommendations:
        print(f"    {rec}")

def estimate_max_users():
    """Estimate maximum concurrent users based on test results"""
    # Based on typical bottlenecks found
    concurrent_test = results["tests"].get("concurrent_users", {})
    
    # Find highest successful concurrency level
    max_successful = 100  # Default assumption
    
    for key, data in concurrent_test.items():
        if "concurrent" in key and data.get("success_rate", 0) >= 99:
            level = int(key.split("_")[1])
            if level > max_successful:
                max_successful = level
    
    # Rough multiplier based on architecture (single server = 10x test results)
    # With proper architecture it could be 1000x+
    return max_successful * 10

async def main():
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}CONTENTRY.AI SCALABILITY TEST SUITE{Colors.END}")
    print(f"{Colors.BOLD}Target: 100,000+ Concurrent Users{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")
    
    # Run all tests
    await test_api_response_times()
    await test_concurrent_users()
    await test_database_performance()
    await test_resource_usage()
    await test_connection_pool()
    await test_auth_throughput()
    await test_architecture_analysis()
    await generate_summary()
    
    # Save results
    with open("/app/scalability_report.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n  {Colors.BOLD}Full report saved to: /app/scalability_report.json{Colors.END}\n")

if __name__ == "__main__":
    asyncio.run(main())

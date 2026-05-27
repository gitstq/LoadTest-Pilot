#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LoadTest-Pilot 🚀
轻量级API性能测试与压力测试引擎
Lightweight API Performance & Load Testing Engine

Zero Dependencies | TUI Dashboard | Real-time Metrics
"""

import argparse
import concurrent.futures
import json
import re
import socket
import ssl
import sys
import time
import urllib.parse
from collections import deque
from datetime import datetime
from threading import Lock, Thread
from typing import Dict, List, Optional, Tuple, Any

__version__ = "1.0.0"
__author__ = "LoadTest-Pilot Team"

# ============================================================================
# ANSI Color Codes for TUI
# ============================================================================
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"

# ============================================================================
# HTTP Request Parser & Builder
# ============================================================================
class HTTPRequest:
    """Zero-dependency HTTP request builder"""
    
    def __init__(self, method: str, url: str, headers: Dict[str, str] = None, 
                 body: str = None, timeout: int = 30):
        self.method = method.upper()
        self.url = url
        self.headers = headers or {}
        self.body = body or ""
        self.timeout = timeout
        self.parsed = urllib.parse.urlparse(url)
        
    def build_request(self) -> bytes:
        """Build raw HTTP request bytes"""
        host = self.parsed.hostname
        port = self.parsed.port or (443 if self.parsed.scheme == "https" else 80)
        path = self.parsed.path or "/"
        if self.parsed.query:
            path += "?" + self.parsed.query
            
        # Default headers
        headers = {
            "Host": host,
            "User-Agent": "LoadTest-Pilot/1.0.0",
            "Accept": "*/*",
            "Connection": "close",
        }
        headers.update(self.headers)
        
        if self.body:
            headers["Content-Length"] = str(len(self.body.encode()))
            
        # Build request line
        request_lines = [f"{self.method} {path} HTTP/1.1"]
        
        # Add headers
        for key, value in headers.items():
            request_lines.append(f"{key}: {value}")
            
        request_lines.append("")
        
        if self.body:
            request_lines.append(self.body)
            
        return "\r\n".join(request_lines).encode()

# ============================================================================
# HTTP Response Parser
# ============================================================================
class HTTPResponse:
    """Zero-dependency HTTP response parser"""
    
    def __init__(self, raw_response: bytes):
        self.raw = raw_response
        self.status_code = 0
        self.headers = {}
        self.body = b""
        self.parse()
        
    def parse(self):
        """Parse HTTP response"""
        try:
            # Split headers and body
            header_end = self.raw.find(b"\r\n\r\n")
            if header_end == -1:
                header_end = self.raw.find(b"\n\n")
                
            if header_end != -1:
                headers_raw = self.raw[:header_end].decode("utf-8", errors="ignore")
                self.body = self.raw[header_end + 4:]
            else:
                headers_raw = self.raw.decode("utf-8", errors="ignore")
                
            # Parse status line
            lines = headers_raw.split("\r\n")
            if len(lines) < 1:
                lines = headers_raw.split("\n")
                
            if lines:
                status_match = re.match(r"HTTP/\d\.\d\s+(\d+)", lines[0])
                if status_match:
                    self.status_code = int(status_match.group(1))
                    
            # Parse headers
            for line in lines[1:]:
                if ":" in line:
                    key, value = line.split(":", 1)
                    self.headers[key.strip().lower()] = value.strip()
                    
        except Exception:
            pass
            
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300
        
    def get_content_length(self) -> int:
        return len(self.body)

# ============================================================================
# HTTP Client
# ============================================================================
class HTTPClient:
    """Zero-dependency HTTP client"""
    
    def __init__(self, timeout: int = 30, follow_redirects: bool = True):
        self.timeout = timeout
        self.follow_redirects = follow_redirects
        
    def request(self, req: HTTPRequest) -> Tuple[HTTPResponse, float, Optional[str]]:
        """
        Execute HTTP request
        Returns: (response, latency_seconds, error_message)
        """
        start_time = time.time()
        error = None
        response = None
        
        try:
            parsed = req.parsed
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            is_https = parsed.scheme == "https"
            
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            # Connect
            sock.connect((host, port))
            
            # Wrap with SSL if HTTPS
            if is_https:
                context = ssl.create_default_context()
                sock = context.wrap_socket(sock, server_hostname=host)
                
            # Send request
            sock.sendall(req.build_request())
            
            # Receive response
            response_data = b""
            while True:
                try:
                    chunk = sock.recv(8192)
                    if not chunk:
                        break
                    response_data += chunk
                except socket.timeout:
                    break
                    
            sock.close()
            
            response = HTTPResponse(response_data)
            
        except socket.timeout:
            error = "Timeout"
        except socket.gaierror:
            error = "DNS Error"
        except ConnectionRefusedError:
            error = "Connection Refused"
        except Exception as e:
            error = str(e)[:50]
            
        latency = time.time() - start_time
        return response, latency, error

# ============================================================================
# Statistics Collector
# ============================================================================
class StatsCollector:
    """Thread-safe statistics collector"""
    
    def __init__(self, max_latencies: int = 10000):
        self.lock = Lock()
        self.total_requests = 0
        self.success_requests = 0
        self.failed_requests = 0
        self.total_latency = 0.0
        self.latencies: deque = deque(maxlen=max_latencies)
        self.status_codes: Dict[int, int] = {}
        self.errors: Dict[str, int] = {}
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.bytes_transferred = 0
        
    def start(self):
        self.start_time = time.time()
        
    def stop(self):
        self.end_time = time.time()
        
    def record(self, latency: float, response: Optional[HTTPResponse], error: Optional[str]):
        with self.lock:
            self.total_requests += 1
            self.total_latency += latency
            self.latencies.append(latency)
            
            if error:
                self.failed_requests += 1
                self.errors[error] = self.errors.get(error, 0) + 1
            elif response and response.is_success():
                self.success_requests += 1
                self.status_codes[response.status_code] = self.status_codes.get(response.status_code, 0) + 1
                self.bytes_transferred += response.get_content_length()
            else:
                self.failed_requests += 1
                if response:
                    self.status_codes[response.status_code] = self.status_codes.get(response.status_code, 0) + 1
                    
    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            duration = (self.end_time or time.time()) - (self.start_time or time.time())
            duration = max(duration, 0.001)
            
            latencies_list = list(self.latencies)
            sorted_latencies = sorted(latencies_list) if latencies_list else []
            
            return {
                "total_requests": self.total_requests,
                "success_requests": self.success_requests,
                "failed_requests": self.failed_requests,
                "success_rate": (self.success_requests / max(self.total_requests, 1)) * 100,
                "avg_latency": self.total_latency / max(self.total_requests, 1),
                "min_latency": min(latencies_list) if latencies_list else 0,
                "max_latency": max(latencies_list) if latencies_list else 0,
                "p50_latency": sorted_latencies[len(sorted_latencies)//2] if sorted_latencies else 0,
                "p90_latency": sorted_latencies[int(len(sorted_latencies)*0.9)] if sorted_latencies else 0,
                "p95_latency": sorted_latencies[int(len(sorted_latencies)*0.95)] if sorted_latencies else 0,
                "p99_latency": sorted_latencies[int(len(sorted_latencies)*0.99)] if sorted_latencies else 0,
                "rps": self.total_requests / duration,
                "duration": duration,
                "status_codes": dict(self.status_codes),
                "errors": dict(self.errors),
                "bytes_transferred": self.bytes_transferred,
            }

# ============================================================================
# TUI Dashboard Renderer
# ============================================================================
class Dashboard:
    """Terminal UI Dashboard"""
    
    def __init__(self, stats: StatsCollector):
        self.stats = stats
        self.running = False
        self.thread: Optional[Thread] = None
        
    def start(self):
        self.running = True
        self.thread = Thread(target=self._render_loop)
        self.thread.daemon = True
        self.thread.start()
        
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
            
    def _render_loop(self):
        while self.running:
            self._clear_screen()
            self._render()
            time.sleep(0.5)
            
    def _clear_screen(self):
        print("\033[2J\033[H", end="")
        
    def _render(self):
        s = self.stats.get_stats()
        
        # Header
        print(f"{Colors.CYAN}{Colors.BOLD}╔══════════════════════════════════════════════════════════════════╗{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}║{Colors.RESET}  🚀 LoadTest-Pilot {Colors.DIM}v{__version__}{Colors.RESET}          API Performance Testing Engine  {Colors.CYAN}{Colors.BOLD}║{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}╚══════════════════════════════════════════════════════════════════╝{Colors.RESET}")
        print()
        
        # Main Metrics
        print(f"{Colors.BOLD}📊 核心指标 | Core Metrics{Colors.RESET}")
        print(f"  {Colors.BLUE}├─ 总请求数 (Total):{Colors.RESET}     {s['total_requests']:,}")
        print(f"  {Colors.GREEN}├─ 成功请求 (Success):{Colors.RESET}   {s['success_requests']:,} ({s['success_rate']:.1f}%)")
        print(f"  {Colors.RED}├─ 失败请求 (Failed):{Colors.RESET}    {s['failed_requests']:,}")
        print(f"  {Colors.YELLOW}├─ 吞吐量 (RPS):{Colors.RESET}       {s['rps']:.1f} req/s")
        print(f"  {Colors.MAGENTA}└─ 运行时长 (Duration):{Colors.RESET}  {s['duration']:.1f}s")
        print()
        
        # Latency Metrics
        print(f"{Colors.BOLD}⏱️  延迟统计 | Latency Statistics{Colors.RESET}")
        print(f"  {Colors.CYAN}├─ 平均 (Avg):{Colors.RESET}    {s['avg_latency']*1000:.1f}ms")
        print(f"  {Colors.CYAN}├─ 最小 (Min):{Colors.RESET}    {s['min_latency']*1000:.1f}ms")
        print(f"  {Colors.CYAN}├─ 最大 (Max):{Colors.RESET}    {s['max_latency']*1000:.1f}ms")
        print(f"  {Colors.GREEN}├─ P50:{Colors.RESET}           {s['p50_latency']*1000:.1f}ms")
        print(f"  {Colors.YELLOW}├─ P90:{Colors.RESET}           {s['p90_latency']*1000:.1f}ms")
        print(f"  {Colors.MAGENTA}├─ P95:{Colors.RESET}           {s['p95_latency']*1000:.1f}ms")
        print(f"  {Colors.RED}└─ P99:{Colors.RESET}           {s['p99_latency']*1000:.1f}ms")
        print()
        
        # Status Codes
        if s['status_codes']:
            print(f"{Colors.BOLD}📈 HTTP状态码 | Status Codes{Colors.RESET}")
            for code, count in sorted(s['status_codes'].items()):
                color = Colors.GREEN if 200 <= code < 300 else Colors.YELLOW if 300 <= code < 400 else Colors.RED
                print(f"  {color}├─ {code}:{Colors.RESET} {count:,}")
            print()
            
        # Errors
        if s['errors']:
            print(f"{Colors.BOLD}⚠️  错误统计 | Errors{Colors.RESET}")
            for error, count in sorted(s['errors'].items(), key=lambda x: -x[1])[:5]:
                print(f"  {Colors.RED}├─ {error}:{Colors.RESET} {count:,}")
            print()
            
        # Footer
        print(f"{Colors.DIM}按 Ctrl+C 停止测试 | Press Ctrl+C to stop{Colors.RESET}")

# ============================================================================
# Load Test Worker
# ============================================================================
class LoadTester:
    """Main load testing engine"""
    
    def __init__(self, url: str, method: str = "GET", headers: Dict[str, str] = None,
                 body: str = None, concurrency: int = 10, duration: int = 60,
                 requests: int = None, timeout: int = 30, no_dashboard: bool = False):
        self.url = url
        self.method = method
        self.headers = headers or {}
        self.body = body
        self.concurrency = concurrency
        self.duration = duration
        self.requests = requests
        self.timeout = timeout
        self.no_dashboard = no_dashboard
        
        self.client = HTTPClient(timeout=timeout)
        self.stats = StatsCollector()
        self.dashboard = Dashboard(self.stats) if not no_dashboard else None
        self.stop_event = False
        
    def _worker(self):
        """Worker thread that sends requests"""
        req = HTTPRequest(self.method, self.url, self.headers, self.body, self.timeout)
        
        while not self.stop_event:
            if self.requests and self.stats.total_requests >= self.requests:
                break
                
            response, latency, error = self.client.request(req)
            self.stats.record(latency, response, error)
            
    def run(self) -> Dict[str, Any]:
        """Run the load test"""
        print(f"\n{Colors.CYAN}{Colors.BOLD}🚀 LoadTest-Pilot Starting...{Colors.RESET}\n")
        print(f"  URL: {Colors.YELLOW}{self.url}{Colors.RESET}")
        print(f"  Method: {Colors.YELLOW}{self.method}{Colors.RESET}")
        print(f"  Concurrency: {Colors.YELLOW}{self.concurrency}{Colors.RESET}")
        print(f"  Duration: {Colors.YELLOW}{self.duration}s{Colors.RESET}")
        if self.requests:
            print(f"  Max Requests: {Colors.YELLOW}{self.requests}{Colors.RESET}")
        print()
        
        self.stats.start()
        
        if self.dashboard:
            self.dashboard.start()
            
        # Start workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            futures = [executor.submit(self._worker) for _ in range(self.concurrency)]
            
            # Wait for duration or max requests
            start = time.time()
            try:
                while time.time() - start < self.duration:
                    if self.requests and self.stats.total_requests >= self.requests:
                        break
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}⚠️  Test interrupted by user{Colors.RESET}")
                
            self.stop_event = True
            
            # Wait for workers to finish
            concurrent.futures.wait(futures, timeout=5)
            
        self.stats.stop()
        
        if self.dashboard:
            self.dashboard.stop()
            
        return self.stats.get_stats()

# ============================================================================
# Report Generator
# ============================================================================
class ReportGenerator:
    """Generate test reports in various formats"""
    
    @staticmethod
    def generate_console_report(stats: Dict[str, Any]) -> str:
        """Generate console-friendly report"""
        lines = []
        lines.append("\n" + "=" * 70)
        lines.append("📋 LOAD TEST REPORT")
        lines.append("=" * 70)
        lines.append("")
        lines.append("【测试摘要 | Test Summary】")
        lines.append(f"  总请求数: {stats['total_requests']:,}")
        lines.append(f"  成功请求: {stats['success_requests']:,} ({stats['success_rate']:.2f}%)")
        lines.append(f"  失败请求: {stats['failed_requests']:,}")
        lines.append(f"  吞吐量: {stats['rps']:.2f} req/s")
        lines.append(f"  测试时长: {stats['duration']:.2f}s")
        lines.append("")
        lines.append("【延迟统计 | Latency Statistics】")
        lines.append(f"  平均延迟: {stats['avg_latency']*1000:.2f}ms")
        lines.append(f"  最小延迟: {stats['min_latency']*1000:.2f}ms")
        lines.append(f"  最大延迟: {stats['max_latency']*1000:.2f}ms")
        lines.append(f"  P50: {stats['p50_latency']*1000:.2f}ms")
        lines.append(f"  P90: {stats['p90_latency']*1000:.2f}ms")
        lines.append(f"  P95: {stats['p95_latency']*1000:.2f}ms")
        lines.append(f"  P99: {stats['p99_latency']*1000:.2f}ms")
        lines.append("")
        
        if stats['status_codes']:
            lines.append("【HTTP状态码 | Status Codes】")
            for code, count in sorted(stats['status_codes'].items()):
                lines.append(f"  {code}: {count:,}")
            lines.append("")
            
        if stats['errors']:
            lines.append("【错误统计 | Errors】")
            for error, count in sorted(stats['errors'].items(), key=lambda x: -x[1]):
                lines.append(f"  {error}: {count:,}")
            lines.append("")
            
        lines.append("=" * 70)
        return "\n".join(lines)
        
    @staticmethod
    def generate_json_report(stats: Dict[str, Any]) -> str:
        """Generate JSON report"""
        return json.dumps(stats, indent=2, ensure_ascii=False)
        
    @staticmethod
    def generate_html_report(stats: Dict[str, Any], url: str) -> str:
        """Generate HTML report"""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LoadTest-Pilot Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f7fa; padding: 40px 20px; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; border-radius: 16px; margin-bottom: 30px; }}
        .header h1 {{ font-size: 32px; margin-bottom: 10px; }}
        .header p {{ opacity: 0.9; font-size: 16px; }}
        .card {{ background: white; border-radius: 12px; padding: 30px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        .card h2 {{ font-size: 20px; color: #333; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #667eea; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
        .metric {{ text-align: center; padding: 20px; background: #f8f9fa; border-radius: 8px; }}
        .metric-value {{ font-size: 32px; font-weight: bold; color: #667eea; }}
        .metric-label {{ font-size: 14px; color: #666; margin-top: 5px; }}
        .success {{ color: #28a745; }}
        .warning {{ color: #ffc107; }}
        .danger {{ color: #dc3545; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ font-weight: 600; color: #333; background: #f8f9fa; }}
        .footer {{ text-align: center; color: #999; margin-top: 40px; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 LoadTest-Pilot Report</h1>
            <p>API Performance Testing Results | {url}</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="card">
            <h2>📊 Test Summary</h2>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value">{stats['total_requests']:,}</div>
                    <div class="metric-label">Total Requests</div>
                </div>
                <div class="metric">
                    <div class="metric-value {'success' if stats['success_rate'] >= 95 else 'warning' if stats['success_rate'] >= 80 else 'danger'}">{stats['success_rate']:.1f}%</div>
                    <div class="metric-label">Success Rate</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{stats['rps']:.1f}</div>
                    <div class="metric-label">Requests/sec</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{stats['duration']:.1f}s</div>
                    <div class="metric-label">Duration</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>⏱️ Latency Statistics</h2>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Average</td><td>{stats['avg_latency']*1000:.2f} ms</td></tr>
                <tr><td>Minimum</td><td>{stats['min_latency']*1000:.2f} ms</td></tr>
                <tr><td>Maximum</td><td>{stats['max_latency']*1000:.2f} ms</td></tr>
                <tr><td>P50 (Median)</td><td>{stats['p50_latency']*1000:.2f} ms</td></tr>
                <tr><td>P90</td><td>{stats['p90_latency']*1000:.2f} ms</td></tr>
                <tr><td>P95</td><td>{stats['p95_latency']*1000:.2f} ms</td></tr>
                <tr><td>P99</td><td>{stats['p99_latency']*1000:.2f} ms</td></tr>
            </table>
        </div>
        
        <div class="card">
            <h2>📈 Status Codes</h2>
            <table>
                <tr><th>Status Code</th><th>Count</th></tr>
"""
        for code, count in sorted(stats['status_codes'].items()):
            html += f"                <tr><td>{code}</td><td>{count:,}</td></tr>\n"
            
        html += """            </table>
        </div>
        
        <div class="footer">
            <p>Generated by LoadTest-Pilot v1.0.0</p>
        </div>
    </div>
</body>
</html>"""
        return html

# ============================================================================
# CLI Argument Parser
# ============================================================================
def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser"""
    parser = argparse.ArgumentParser(
        prog="loadtest-pilot",
        description="🚀 LoadTest-Pilot - Lightweight API Performance & Load Testing Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic load test
  loadtest-pilot -u https://api.example.com/users
  
  # High concurrency test
  loadtest-pilot -u https://api.example.com/users -c 100 -d 60
  
  # POST request with body
  loadtest-pilot -u https://api.example.com/users -m POST -b '{"name":"test"}' -H "Content-Type: application/json"
  
  # Limited requests
  loadtest-pilot -u https://api.example.com/users -n 1000
  
  # No dashboard, output to file
  loadtest-pilot -u https://api.example.com/users --no-dashboard -o report.json
        """
    )
    
    parser.add_argument("-u", "--url", required=True, help="Target URL to test")
    parser.add_argument("-m", "--method", default="GET", help="HTTP method (default: GET)")
    parser.add_argument("-H", "--header", action="append", default=[], help="HTTP header (can be used multiple times)")
    parser.add_argument("-b", "--body", help="Request body")
    parser.add_argument("-c", "--concurrency", type=int, default=10, help="Number of concurrent connections (default: 10)")
    parser.add_argument("-d", "--duration", type=int, default=30, help="Test duration in seconds (default: 30)")
    parser.add_argument("-n", "--requests", type=int, help="Total number of requests to send")
    parser.add_argument("-t", "--timeout", type=int, default=30, help="Request timeout in seconds (default: 30)")
    parser.add_argument("--no-dashboard", action="store_true", help="Disable real-time dashboard")
    parser.add_argument("-o", "--output", help="Output file for report")
    parser.add_argument("-f", "--format", choices=["console", "json", "html"], default="console", help="Report format")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    
    return parser

def parse_headers(header_list: List[str]) -> Dict[str, str]:
    """Parse header strings into dict"""
    headers = {}
    for header in header_list:
        if ":" in header:
            key, value = header.split(":", 1)
            headers[key.strip()] = value.strip()
    return headers

# ============================================================================
# Main Entry Point
# ============================================================================
def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Parse headers
    headers = parse_headers(args.header)
    
    # Create and run load tester
    tester = LoadTester(
        url=args.url,
        method=args.method,
        headers=headers,
        body=args.body,
        concurrency=args.concurrency,
        duration=args.duration,
        requests=args.requests,
        timeout=args.timeout,
        no_dashboard=args.no_dashboard
    )
    
    try:
        stats = tester.run()
        
        # Generate report
        if args.format == "json":
            report = ReportGenerator.generate_json_report(stats)
        elif args.format == "html":
            report = ReportGenerator.generate_html_report(stats, args.url)
        else:
            report = ReportGenerator.generate_console_report(stats)
            
        # Output report
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"\n{Colors.GREEN}✅ Report saved to: {args.output}{Colors.RESET}")
        else:
            print(report)
            
        # Exit code based on success rate
        sys.exit(0 if stats['success_rate'] >= 95 else 1)
        
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error: {e}{Colors.RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()

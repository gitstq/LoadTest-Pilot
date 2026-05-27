<div align="center">

# 🚀 LoadTest-Pilot

**轻量级API性能测试与压力测试引擎 | Lightweight API Performance & Load Testing Engine**

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero-orange.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Cross--Platform-purple.svg)]()

[English](#english) | [简体中文](#简体中文) | [繁體中文](#繁體中文)

</div>

---

<a name="简体中文"></a>
## 🎉 项目介绍

**LoadTest-Pilot** 是一款专为开发者和测试工程师打造的轻量级API性能测试与压力测试工具。它采用纯Python标准库实现，零外部依赖，开箱即用，让您能够快速评估API的性能表现和承载能力。

### 💡 灵感来源

在微服务和云原生架构日益普及的今天，API性能测试变得至关重要。然而，现有的工具如k6、Artillery、JMeter等虽然功能强大，但往往需要复杂的配置和依赖安装。LoadTest-Pilot 应运而生，旨在提供一个**零依赖、轻量级、易上手**的API压力测试解决方案。

### ✨ 核心特性

- 🎯 **零依赖设计** - 纯Python标准库实现，无需安装任何第三方包
- 📊 **实时TUI仪表板** - 美观的终端界面，实时展示测试指标
- ⚡ **高性能并发** - 基于线程池实现高并发请求
- 📈 **丰富指标** - RPS、延迟百分位(P50/P90/P95/P99)、成功率、状态码分布
- 🎨 **多格式报告** - 支持Console/JSON/HTML三种报告格式
- 🔧 **灵活配置** - 支持自定义并发数、测试时长、请求数、超时时间
- 🌐 **全协议支持** - 支持HTTP/HTTPS，自动处理SSL/TLS
- 📝 **自定义请求** - 支持自定义HTTP方法、请求头、请求体

---

## 🚀 快速开始

### 环境要求

- Python 3.7+
- 操作系统: Linux / macOS / Windows

### 安装

#### 方式一：直接下载使用

```bash
# 克隆仓库
git clone https://github.com/gitstq/LoadTest-Pilot.git
cd LoadTest-Pilot

# 直接运行
python loadtest_pilot.py --help
```

#### 方式二：通过pip安装

```bash
pip install .

# 或直接从GitHub安装
pip install git+https://github.com/gitstq/LoadTest-Pilot.git
```

### 基础用法

```bash
# 基础负载测试（默认10并发，30秒）
loadtest-pilot -u https://api.example.com/users

# 高并发压力测试（100并发，持续60秒）
loadtest-pilot -u https://api.example.com/users -c 100 -d 60

# POST请求测试
loadtest-pilot -u https://api.example.com/users \
  -m POST \
  -H "Content-Type: application/json" \
  -b '{"name":"test","email":"test@example.com"}'

# 限定请求总数
loadtest-pilot -u https://api.example.com/users -n 10000 -c 50

# 生成HTML报告
loadtest-pilot -u https://api.example.com/users -f html -o report.html

# 无仪表板模式（适合CI/CD）
loadtest-pilot -u https://api.example.com/users --no-dashboard -f json
```

---

## 📖 详细使用指南

### 命令行参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--url` | `-u` | 目标URL（必填） | - |
| `--method` | `-m` | HTTP方法 | GET |
| `--header` | `-H` | HTTP请求头（可多次使用） | - |
| `--body` | `-b` | 请求体 | - |
| `--concurrency` | `-c` | 并发连接数 | 10 |
| `--duration` | `-d` | 测试时长（秒） | 30 |
| `--requests` | `-n` | 总请求数限制 | 无限制 |
| `--timeout` | `-t` | 请求超时（秒） | 30 |
| `--no-dashboard` | - | 禁用实时仪表板 | false |
| `--output` | `-o` | 报告输出文件 | - |
| `--format` | `-f` | 报告格式(console/json/html) | console |
| `--version` | `-v` | 显示版本 | - |

### 高级用法示例

#### 1. 带认证的API测试

```bash
loadtest-pilot -u https://api.example.com/protected \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-API-Key: your-api-key" \
  -c 20 -d 60
```

#### 2. 表单提交测试

```bash
loadtest-pilot -u https://api.example.com/login \
  -m POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -b "username=test&password=test123" \
  -c 50 -d 120
```

#### 3. CI/CD集成

```bash
# 在CI管道中运行测试，失败时返回非零退出码
loadtest-pilot -u https://api.example.com/health \
  --no-dashboard \
  -f json \
  -o test-result.json \
  -c 10 \
  -d 10

# 检查成功率是否达标
if [ $? -ne 0 ]; then
  echo "性能测试未通过！成功率低于95%"
  exit 1
fi
```

#### 4. 批量测试脚本

```bash
#!/bin/bash

ENDPOINTS=(
  "https://api.example.com/users"
  "https://api.example.com/products"
  "https://api.example.com/orders"
)

for endpoint in "${ENDPOINTS[@]}"; do
  echo "Testing: $endpoint"
  loadtest-pilot -u "$endpoint" -c 20 -d 30 -f html -o "report-$(basename $endpoint).html"
done
```

---

## 💡 设计思路与迭代规划

### 技术选型

- **纯Python标准库**：socket、ssl、threading、argparse等，零外部依赖
- **线程池并发**：concurrent.futures.ThreadPoolExecutor实现高效并发
- **零依赖HTTP客户端**：基于socket实现原生HTTP/HTTPS请求
- **ANSI转义码**：实现美观的终端TUI界面

### 核心指标说明

| 指标 | 说明 | 健康阈值参考 |
|------|------|-------------|
| RPS | 每秒请求数 | 根据业务需求 |
| P50 | 中位数延迟 | < 200ms |
| P90 | 90%请求延迟 | < 500ms |
| P95 | 95%请求延迟 | < 1000ms |
| P99 | 99%请求延迟 | < 2000ms |
| 成功率 | 成功请求占比 | > 99% |

### 后续迭代计划

- [ ] WebSocket支持
- [ ] 自定义测试场景（阶梯加压、脉冲测试）
- [ ] 分布式压测模式
- [ ] 实时结果导出到Prometheus/Grafana
- [ ] 测试脚本录制回放功能
- [ ] 多语言SDK支持

---

## 📦 打包与部署

### 打包为可执行文件

```bash
# 安装PyInstaller
pip install pyinstaller

# 打包为单文件可执行程序
pyinstaller --onefile --name loadtest-pilot loadtest_pilot.py

# 输出在 dist/ 目录
```

### Docker部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY loadtest_pilot.py .

ENTRYPOINT ["python", "loadtest_pilot.py"]
```

```bash
docker build -t loadtest-pilot .
docker run loadtest-pilot -u https://api.example.com/users
```

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 提交Issue

- 使用清晰的标题描述问题
- 提供复现步骤和环境信息
- 贴上相关的错误日志

### 提交PR

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

### 代码规范

- 遵循PEP 8规范
- 添加适当的注释和文档字符串
- 确保代码通过基础测试

---

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

---

<a name="english"></a>
## 🎉 Introduction

**LoadTest-Pilot** is a lightweight API performance and load testing tool designed for developers and QA engineers. Built with pure Python standard library, zero dependencies, ready to use out of the box.

### ✨ Features

- 🎯 **Zero Dependencies** - Pure Python standard library, no third-party packages
- 📊 **Real-time TUI Dashboard** - Beautiful terminal interface with live metrics
- ⚡ **High Performance** - Thread pool based concurrent requests
- 📈 **Rich Metrics** - RPS, latency percentiles (P50/P90/P95/P99), success rate
- 🎨 **Multiple Report Formats** - Console, JSON, and HTML reports
- 🔧 **Flexible Configuration** - Custom concurrency, duration, request count, timeout
- 🌐 **Full Protocol Support** - HTTP/HTTPS with automatic SSL/TLS handling
- 📝 **Custom Requests** - Support custom HTTP methods, headers, and body

### 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/gitstq/LoadTest-Pilot.git
cd LoadTest-Pilot

# Basic load test
python loadtest_pilot.py -u https://api.example.com/users

# High concurrency test
python loadtest_pilot.py -u https://api.example.com/users -c 100 -d 60

# Generate HTML report
python loadtest_pilot.py -u https://api.example.com/users -f html -o report.html
```

### 📄 License

[MIT License](LICENSE)

---

<a name="繁體中文"></a>
## 🎉 專案介紹

**LoadTest-Pilot** 是一款專為開發者和測試工程師打造的輕量級API效能測試與壓力測試工具。採用純Python標準庫實現，零外部依賴，開箱即用。

### ✨ 核心特性

- 🎯 **零依賴設計** - 純Python標準庫，無需安裝第三方套件
- 📊 **即時TUI儀表板** - 美觀的終端介面，即時展示測試指標
- ⚡ **高效能並發** - 基於執行緒池實現高並發請求
- 📈 **豐富指標** - RPS、延遲百分位、成功率、狀態碼分布
- 🎨 **多格式報告** - 支援Console/JSON/HTML三種報告格式

### 🚀 快速開始

```bash
# 克隆倉庫
git clone https://github.com/gitstq/LoadTest-Pilot.git
cd LoadTest-Pilot

# 基礎負載測試
python loadtest_pilot.py -u https://api.example.com/users

# 高並發壓力測試
python loadtest_pilot.py -u https://api.example.com/users -c 100 -d 60
```

### 📄 開源協議

[MIT License](LICENSE)

---

<div align="center">

**Made with ❤️ by LoadTest-Pilot Team**

</div>

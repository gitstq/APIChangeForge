# 🔍 APIChangeForge

<p align="center">
  <strong>轻量级API变更智能检测与影响分析引擎 CLI</strong><br>
  <strong>Lightweight API Change Detection & Impact Analysis Engine</strong><br>
  <strong>輕量級API變更智能檢測與影響分析引擎</strong>
</p>

<p align="center">
  <a href="#简体中文">简体中文</a> •
  <a href="#繁體中文">繁體中文</a> •
  <a href="#english">English</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/Zero%20Dependencies-✓-green.svg" alt="Zero Dependencies">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License">
</p>

---

<a name="简体中文"></a>
## 🎉 简体中文

### 项目介绍

**APIChangeForge** 是一款专为API版本管理设计的轻量级智能检测工具。在微服务和API优先的开发模式下，API的频繁迭代往往让开发者难以追踪变更对下游系统的影响。APIChangeForge 通过自动对比两个版本的API规范，智能识别所有变更点，并评估其对客户端的潜在影响，帮助团队安全、高效地进行API演进。

**灵感来源**：在维护多个微服务API的过程中，我们发现每次版本升级都需要人工对比OpenAPI文档，既耗时又容易遗漏关键变更。因此开发了这款工具，让API变更检测自动化、智能化。

### ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🔍 **智能差异检测** | 自动识别端点、参数、响应字段、安全方案的变更 |
| 🎯 **影响评估** | 智能分级：破坏性/潜在破坏性/已弃用/非破坏性/增强 |
| 📄 **多格式支持** | 支持OpenAPI/Swagger、Postman Collection、HAR文件 |
| 📊 **多格式报告** | 输出Markdown/HTML/JSON/SARIF格式报告 |
| 🚀 **CI/CD集成** | 支持GitHub Actions等流水线，可配置失败阈值 |
| 🪶 **零依赖** | 纯Python标准库实现，单文件即可运行 |
| 🌐 **远程支持** | 可直接对比远程URL的API规范 |

### 🚀 快速开始

#### 环境要求

- **Python**: 3.8 或更高版本
- **操作系统**: Linux / macOS / Windows

#### 安装

```bash
# 方式1：直接下载使用
wget https://raw.githubusercontent.com/gitstq/APIChangeForge/main/apichangeforge.py
chmod +x apichangeforge.py

# 方式2：通过pip安装
pip install apichangeforge

# 方式3：克隆仓库
git clone https://github.com/gitstq/APIChangeForge.git
cd APIChangeForge
```

#### 基本使用

```bash
# 对比两个OpenAPI规范文件
python apichangeforge.py old_api.json new_api.json

# 生成HTML报告
python apichangeforge.py old.yaml new.yaml -f html -o report.html

# 对比远程API文档
python apichangeforge.py https://api.example.com/v1/openapi.json https://api.example.com/v2/openapi.json

# CI模式：检测到破坏性变更时返回错误码
python apichangeforge.py old.json new.json --fail-on-breaking
```

### 📖 详细使用指南

#### 支持的输入格式

| 格式 | 文件扩展名 | 说明 |
|------|-----------|------|
| OpenAPI/Swagger | `.json`, `.yaml`, `.yml` | REST API标准规范 |
| Postman Collection | `.json` | Postman导出的集合文件 |
| HAR | `.har` | HTTP Archive文件 |

#### 输出格式

```bash
# Markdown报告（默认）
python apichangeforge.py old.json new.json -f markdown -o report.md

# HTML可视化报告
python apichangeforge.py old.json new.json -f html -o report.html

# JSON结构化数据
python apichangeforge.py old.json new.json -f json -o report.json

# SARIF格式（用于GitHub Advanced Security）
python apichangeforge.py old.json new.json -f sarif -o results.sarif
```

#### 变更检测维度

- **端点级别**: 新增/删除/弃用端点
- **参数级别**: 新增/删除参数、必填状态变更、类型变更
- **响应级别**: 字段新增/删除、类型变更
- **安全级别**: 认证方案变更

#### 影响评估等级

| 等级 | 图标 | 说明 | 建议 |
|------|------|------|------|
| 🔴 Breaking | 破坏性 | 会导致客户端失效 | 必须处理 |
| 🟡 Potentially Breaking | 潜在破坏 | 可能导致客户端问题 | 建议检查 |
| ⚠️ Deprecated | 已弃用 | 即将移除的功能 | 计划迁移 |
| 🟢 Non-Breaking | 非破坏 | 向后兼容的变更 | 安全升级 |
| 🔵 Enhancement | 增强 | 新功能 | 可以利用 |

### 💡 设计思路与迭代规划

#### 技术选型

- **纯Python标准库**: 避免依赖冲突，确保长期可维护性
- **Dataclass**: 清晰的数据模型定义
- **Enum**: 规范的变更类型和严重程度定义

#### 后续迭代计划

- [ ] 支持GraphQL Schema对比
- [ ] 集成AI辅助的迁移建议生成
- [ ] Web UI可视化界面
- [ ] 增量变更追踪（与Git集成）
- [ ] 团队协作功能（评论、审批）

### 📦 打包与部署

#### 作为命令行工具使用

```bash
# 添加到PATH
chmod +x apichangeforge.py
sudo cp apichangeforge.py /usr/local/bin/apichangeforge

# 直接使用
apichangeforge old.json new.json
```

#### GitHub Actions集成

```yaml
name: API Change Detection
on:
  pull_request:
    paths:
      - 'openapi.json'

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Get base version
        run: git show HEAD~1:openapi.json > old_openapi.json
      
      - name: Detect API changes
        run: |
          python apichangeforge.py old_openapi.json openapi.json \
            --fail-on-breaking \
            -f sarif -o api-changes.sarif
      
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: api-changes.sarif
```

### 🤝 贡献指南

欢迎提交Issue和PR！请遵循以下规范：

- **Issue**: 描述问题、复现步骤、期望行为
- **PR**: 关联相关Issue，包含测试用例，遵循现有代码风格
- **Commit**: 使用Angular提交规范 (`feat:`, `fix:`, `docs:`, `refactor:`)

### 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

---

<a name="繁體中文"></a>
## 🎉 繁體中文

### 專案介紹

**APIChangeForge** 是一款專為API版本管理設計的輕量級智能檢測工具。在微服務和API優先的開發模式下，API的頻繁迭代往往讓開發者難以追蹤變更對下游系統的影響。APIChangeForge 通過自動對比兩個版本的API規範，智能識別所有變更點，並評估其對客戶端的潛在影響，幫助團隊安全、高效地進行API演進。

**靈感來源**：在維護多個微服務API的過程中，我們發現每次版本升級都需要人工對比OpenAPI文檔，既耗時又容易遺漏關鍵變更。因此開發了這款工具，讓API變更檢測自動化、智能化。

### ✨ 核心特性

| 特性 | 說明 |
|------|------|
| 🔍 **智能差異檢測** | 自動識別端點、參數、響應欄位、安全方案的變更 |
| 🎯 **影響評估** | 智能分級：破壞性/潛在破壞性/已棄用/非破壞性/增強 |
| 📄 **多格式支援** | 支援OpenAPI/Swagger、Postman Collection、HAR檔案 |
| 📊 **多格式報告** | 輸出Markdown/HTML/JSON/SARIF格式報告 |
| 🚀 **CI/CD整合** | 支援GitHub Actions等流水線，可配置失敗閾值 |
| 🪶 **零依賴** | 純Python標準庫實現，單檔案即可運行 |
| 🌐 **遠端支援** | 可直接對比遠端URL的API規範 |

### 🚀 快速開始

#### 環境要求

- **Python**: 3.8 或更高版本
- **作業系統**: Linux / macOS / Windows

#### 安裝

```bash
# 方式1：直接下載使用
wget https://raw.githubusercontent.com/gitstq/APIChangeForge/main/apichangeforge.py
chmod +x apichangeforge.py

# 方式2：通過pip安裝
pip install apichangeforge

# 方式3：克隆倉庫
git clone https://github.com/gitstq/APIChangeForge.git
cd APIChangeForge
```

#### 基本使用

```bash
# 對比兩個OpenAPI規範檔案
python apichangeforge.py old_api.json new_api.json

# 生成HTML報告
python apichangeforge.py old.yaml new.yaml -f html -o report.html

# 對比遠端API文件
python apichangeforge.py https://api.example.com/v1/openapi.json https://api.example.com/v2/openapi.json

# CI模式：檢測到破壞性變更時返回錯誤碼
python apichangeforge.py old.json new.json --fail-on-breaking
```

### 📖 詳細使用指南

#### 支援的輸入格式

| 格式 | 檔案副檔名 | 說明 |
|------|-----------|------|
| OpenAPI/Swagger | `.json`, `.yaml`, `.yml` | REST API標準規範 |
| Postman Collection | `.json` | Postman匯出的集合檔案 |
| HAR | `.har` | HTTP Archive檔案 |

#### 輸出格式

```bash
# Markdown報告（預設）
python apichangeforge.py old.json new.json -f markdown -o report.md

# HTML可視化報告
python apichangeforge.py old.json new.json -f html -o report.html

# JSON結構化資料
python apichangeforge.py old.json new.json -f json -o report.json

# SARIF格式（用於GitHub Advanced Security）
python apichangeforge.py old.json new.json -f sarif -o results.sarif
```

#### 變更檢測維度

- **端點級別**: 新增/刪除/棄用端點
- **參數級別**: 新增/刪除參數、必填狀態變更、類型變更
- **響應級別**: 欄位新增/刪除、類型變更
- **安全級別**: 認證方案變更

#### 影響評估等級

| 等級 | 圖示 | 說明 | 建議 |
|------|------|------|------|
| 🔴 Breaking | 破壞性 | 會導致客戶端失效 | 必須處理 |
| 🟡 Potentially Breaking | 潛在破壞 | 可能導致客戶端問題 | 建議檢查 |
| ⚠️ Deprecated | 已棄用 | 即將移除的功能 | 計劃遷移 |
| 🟢 Non-Breaking | 非破壞 | 向後兼容的變更 | 安全升級 |
| 🔵 Enhancement | 增強 | 新功能 | 可以利用 |

### 💡 設計思路與迭代規劃

#### 技術選型

- **純Python標準庫**: 避免依賴衝突，確保長期可維護性
- **Dataclass**: 清晰的資料模型定義
- **Enum**: 規範的變更類型和嚴重程度定義

#### 後續迭代計劃

- [ ] 支援GraphQL Schema對比
- [ ] 整合AI輔助的遷移建議生成
- [ ] Web UI可視化介面
- [ ] 增量變更追蹤（與Git整合）
- [ ] 團隊協作功能（評論、審批）

### 📦 打包與部署

#### 作為命令列工具使用

```bash
# 添加到PATH
chmod +x apichangeforge.py
sudo cp apichangeforge.py /usr/local/bin/apichangeforge

# 直接使用
apichangeforge old.json new.json
```

#### GitHub Actions整合

```yaml
name: API Change Detection
on:
  pull_request:
    paths:
      - 'openapi.json'

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Get base version
        run: git show HEAD~1:openapi.json > old_openapi.json
      
      - name: Detect API changes
        run: |
          python apichangeforge.py old_openapi.json openapi.json \
            --fail-on-breaking \
            -f sarif -o api-changes.sarif
      
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: api-changes.sarif
```

### 🤝 貢獻指南

歡迎提交Issue和PR！請遵循以下規範：

- **Issue**: 描述問題、復現步驟、期望行為
- **PR**: 關聯相關Issue，包含測試用例，遵循現有代碼風格
- **Commit**: 使用Angular提交規範 (`feat:`, `fix:`, `docs:`, `refactor:`)

### 📄 開源協議

本專案採用 [MIT License](LICENSE) 開源協議。

---

<a name="english"></a>
## 🎉 English

### Project Introduction

**APIChangeForge** is a lightweight intelligent detection tool designed for API version management. In microservices and API-first development models, frequent API iterations often make it difficult for developers to track the impact of changes on downstream systems. APIChangeForge automatically compares two versions of API specifications, intelligently identifies all change points, and assesses their potential impact on clients, helping teams evolve APIs safely and efficiently.

**Inspiration**: While maintaining multiple microservice APIs, we found that each version upgrade required manual comparison of OpenAPI documents, which was time-consuming and prone to missing critical changes. Therefore, we developed this tool to automate and intelligentize API change detection.

### ✨ Core Features

| Feature | Description |
|---------|-------------|
| 🔍 **Smart Diff Detection** | Automatically identify changes in endpoints, parameters, response fields, and security schemes |
| 🎯 **Impact Assessment** | Intelligent classification: Breaking / Potentially Breaking / Deprecated / Non-Breaking / Enhancement |
| 📄 **Multi-format Support** | Support OpenAPI/Swagger, Postman Collection, HAR files |
| 📊 **Multi-format Reports** | Output Markdown/HTML/JSON/SARIF format reports |
| 🚀 **CI/CD Integration** | Support GitHub Actions and other pipelines, configurable failure thresholds |
| 🪶 **Zero Dependencies** | Pure Python standard library implementation, single file execution |
| 🌐 **Remote Support** | Directly compare remote URL API specifications |

### 🚀 Quick Start

#### Requirements

- **Python**: 3.8 or higher
- **OS**: Linux / macOS / Windows

#### Installation

```bash
# Method 1: Direct download
wget https://raw.githubusercontent.com/gitstq/APIChangeForge/main/apichangeforge.py
chmod +x apichangeforge.py

# Method 2: Via pip
pip install apichangeforge

# Method 3: Clone repository
git clone https://github.com/gitstq/APIChangeForge.git
cd APIChangeForge
```

#### Basic Usage

```bash
# Compare two OpenAPI specification files
python apichangeforge.py old_api.json new_api.json

# Generate HTML report
python apichangeforge.py old.yaml new.yaml -f html -o report.html

# Compare remote API documentation
python apichangeforge.py https://api.example.com/v1/openapi.json https://api.example.com/v2/openapi.json

# CI mode: return error code when breaking changes detected
python apichangeforge.py old.json new.json --fail-on-breaking
```

### 📖 Detailed Usage Guide

#### Supported Input Formats

| Format | File Extensions | Description |
|--------|----------------|-------------|
| OpenAPI/Swagger | `.json`, `.yaml`, `.yml` | REST API standard specification |
| Postman Collection | `.json` | Postman exported collection files |
| HAR | `.har` | HTTP Archive files |

#### Output Formats

```bash
# Markdown report (default)
python apichangeforge.py old.json new.json -f markdown -o report.md

# HTML visualization report
python apichangeforge.py old.json new.json -f html -o report.html

# JSON structured data
python apichangeforge.py old.json new.json -f json -o report.json

# SARIF format (for GitHub Advanced Security)
python apichangeforge.py old.json new.json -f sarif -o results.sarif
```

#### Change Detection Dimensions

- **Endpoint Level**: Added/Removed/Deprecated endpoints
- **Parameter Level**: Added/Removed parameters, required status changes, type changes
- **Response Level**: Field additions/removals, type changes
- **Security Level**: Authentication scheme changes

#### Impact Assessment Levels

| Level | Icon | Description | Recommendation |
|-------|------|-------------|----------------|
| 🔴 Breaking | Breaking | Will cause client failure | Must handle |
| 🟡 Potentially Breaking | Potentially Breaking | May cause client issues | Recommended check |
| ⚠️ Deprecated | Deprecated | Features to be removed | Plan migration |
| 🟢 Non-Breaking | Non-Breaking | Backward compatible changes | Safe upgrade |
| 🔵 Enhancement | Enhancement | New features | Can leverage |

### 💡 Design Philosophy & Roadmap

#### Technology Choices

- **Pure Python Standard Library**: Avoid dependency conflicts, ensure long-term maintainability
- **Dataclass**: Clear data model definitions
- **Enum**: Standardized change type and severity definitions

#### Future Roadmap

- [ ] Support GraphQL Schema comparison
- [ ] AI-assisted migration suggestion generation
- [ ] Web UI visualization interface
- [ ] Incremental change tracking (Git integration)
- [ ] Team collaboration features (comments, approvals)

### 📦 Packaging & Deployment

#### Use as CLI Tool

```bash
# Add to PATH
chmod +x apichangeforge.py
sudo cp apichangeforge.py /usr/local/bin/apichangeforge

# Use directly
apichangeforge old.json new.json
```

#### GitHub Actions Integration

```yaml
name: API Change Detection
on:
  pull_request:
    paths:
      - 'openapi.json'

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Get base version
        run: git show HEAD~1:openapi.json > old_openapi.json
      
      - name: Detect API changes
        run: |
          python apichangeforge.py old_openapi.json openapi.json \
            --fail-on-breaking \
            -f sarif -o api-changes.sarif
      
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: api-changes.sarif
```

### 🤝 Contributing

Issues and PRs are welcome! Please follow these guidelines:

- **Issue**: Describe the problem, reproduction steps, expected behavior
- **PR**: Link related issues, include test cases, follow existing code style
- **Commit**: Use Angular commit convention (`feat:`, `fix:`, `docs:`, `refactor:`)

### 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">
  Made with ❤️ by APIChangeForge Team
</p>

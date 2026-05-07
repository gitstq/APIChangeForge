#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 APIChangeForge - Lightweight API Change Detection & Impact Analysis Engine CLI
轻量级API变更智能检测与影响分析引擎

Zero dependencies, Python 3.8+
"""

import json
import argparse
import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from urllib.parse import urlparse
import urllib.request
import urllib.error

__version__ = "1.0.0"
__author__ = "APIChangeForge Team"


class ChangeSeverity(Enum):
    """变更严重程度等级"""
    BREAKING = "breaking"           # 🔴 破坏性变更
    POTENTIALLY_BREAKING = "potentially_breaking"  # 🟡 潜在破坏性
    NON_BREAKING = "non_breaking"   # 🟢 非破坏性
    ENHANCEMENT = "enhancement"     # 🔵 功能增强
    DEPRECATED = "deprecated"       # ⚠️ 已弃用


class ChangeType(Enum):
    """变更类型"""
    # 端点级别
    ENDPOINT_ADDED = "endpoint_added"
    ENDPOINT_REMOVED = "endpoint_removed"
    ENDPOINT_MODIFIED = "endpoint_modified"
    
    # 参数级别
    PARAMETER_ADDED = "parameter_added"
    PARAMETER_REMOVED = "parameter_removed"
    PARAMETER_REQUIRED_CHANGED = "parameter_required_changed"
    PARAMETER_TYPE_CHANGED = "parameter_type_changed"
    
    # 响应级别
    RESPONSE_FIELD_ADDED = "response_field_added"
    RESPONSE_FIELD_REMOVED = "response_field_removed"
    RESPONSE_TYPE_CHANGED = "response_type_changed"
    
    # 安全级别
    SECURITY_SCHEME_CHANGED = "security_scheme_changed"
    AUTH_REQUIRED_CHANGED = "auth_required_changed"


@dataclass
class Change:
    """变更记录"""
    change_type: ChangeType
    severity: ChangeSeverity
    path: str
    description: str
    old_value: Any = None
    new_value: Any = None
    suggestion: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "change_type": self.change_type.value,
            "severity": self.severity.value,
            "path": self.path,
            "description": self.description,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "suggestion": self.suggestion
        }


@dataclass
class Endpoint:
    """API端点"""
    path: str
    method: str
    summary: str = ""
    description: str = ""
    parameters: List[Dict] = field(default_factory=list)
    request_body: Dict = field(default_factory=dict)
    responses: Dict = field(default_factory=dict)
    security: List[Dict] = field(default_factory=list)
    deprecated: bool = False
    tags: List[str] = field(default_factory=list)


@dataclass
class APISpec:
    """API规范"""
    title: str = ""
    version: str = ""
    description: str = ""
    endpoints: List[Endpoint] = field(default_factory=list)
    schemas: Dict[str, Any] = field(default_factory=dict)
    security_schemes: Dict[str, Any] = field(default_factory=dict)
    servers: List[str] = field(default_factory=list)
    raw_spec: Dict = field(default_factory=dict)


class OpenAPIParser:
    """OpenAPI/Swagger规范解析器"""
    
    @staticmethod
    def parse(spec_data: Dict) -> APISpec:
        """解析OpenAPI规范"""
        api_spec = APISpec()
        api_spec.raw_spec = spec_data
        
        # 基本信息
        if "info" in spec_data:
            api_spec.title = spec_data["info"].get("title", "")
            api_spec.version = spec_data["info"].get("version", "")
            api_spec.description = spec_data["info"].get("description", "")
        
        # 服务器信息
        if "servers" in spec_data:
            api_spec.servers = [s.get("url", "") for s in spec_data["servers"]]
        
        # 安全方案
        if "components" in spec_data and "securitySchemes" in spec_data["components"]:
            api_spec.security_schemes = spec_data["components"]["securitySchemes"]
        
        # Schema定义
        if "components" in spec_data and "schemas" in spec_data["components"]:
            api_spec.schemas = spec_data["components"]["schemas"]
        
        # 解析端点
        if "paths" in spec_data:
            for path, methods in spec_data["paths"].items():
                for method, details in methods.items():
                    if method.startswith("x-") or not isinstance(details, dict):
                        continue
                    
                    endpoint = Endpoint(
                        path=path,
                        method=method.upper(),
                        summary=details.get("summary", ""),
                        description=details.get("description", ""),
                        parameters=details.get("parameters", []),
                        request_body=details.get("requestBody", {}),
                        responses=details.get("responses", {}),
                        security=details.get("security", []),
                        deprecated=details.get("deprecated", False),
                        tags=details.get("tags", [])
                    )
                    api_spec.endpoints.append(endpoint)
        
        return api_spec


class PostmanParser:
    """Postman Collection解析器"""
    
    @staticmethod
    def parse(collection: Dict) -> APISpec:
        """解析Postman Collection"""
        api_spec = APISpec()
        api_spec.raw_spec = collection
        
        if "info" in collection:
            api_spec.title = collection["info"].get("name", "")
            api_spec.description = collection["info"].get("description", "")
        
        # 递归解析item
        def parse_items(items: List[Dict], base_path: str = ""):
            for item in items:
                if "request" in item:
                    request = item["request"]
                    if isinstance(request, dict):
                        url = request.get("url", {})
                        if isinstance(url, dict):
                            path = "/" + "/".join(url.get("path", []))
                        else:
                            path = str(url)
                        
                        endpoint = Endpoint(
                            path=path,
                            method=request.get("method", "GET").upper(),
                            summary=item.get("name", ""),
                            parameters=[{
                                "name": p.get("key", ""),
                                "in": "query" if p.get("value") else "header",
                                "required": p.get("disabled", True) == False
                            } for p in request.get("header", []) + request.get("url", {}).get("query", [])],
                            request_body=request.get("body", {}),
                            responses={str(r.get("code", 200)): {"description": r.get("name", "")} 
                                      for r in item.get("response", [])}
                        )
                        api_spec.endpoints.append(endpoint)
                
                if "item" in item:
                    parse_items(item["item"], base_path)
        
        if "item" in collection:
            parse_items(collection["item"])
        
        return api_spec


class HARParser:
    """HAR文件解析器"""
    
    @staticmethod
    def parse(har_data: Dict) -> APISpec:
        """解析HAR文件提取API端点"""
        api_spec = APISpec()
        api_spec.raw_spec = har_data
        api_spec.title = "HAR Extracted API"
        
        if "log" in har_data and "entries" in har_data["log"]:
            seen = set()
            for entry in har_data["log"]["entries"]:
                request = entry.get("request", {})
                url = request.get("url", "")
                method = request.get("method", "GET").upper()
                
                # 解析路径
                parsed = urlparse(url)
                path = parsed.path or "/"
                
                # 去重
                key = f"{method}:{path}"
                if key in seen:
                    continue
                seen.add(key)
                
                endpoint = Endpoint(
                    path=path,
                    method=method,
                    parameters=[{
                        "name": p.get("name", ""),
                        "in": "query" if p.get("queryString") else "header",
                        "required": False
                    } for p in request.get("headers", []) + request.get("queryString", [])],
                    request_body={"content": request.get("postData", {})}
                )
                api_spec.endpoints.append(endpoint)
        
        return api_spec


class SpecLoader:
    """规范文件加载器"""
    
    @staticmethod
    def load(source: str) -> Dict:
        """加载规范文件（本地或URL）"""
        # 检查是否为URL
        if source.startswith(("http://", "https://")):
            return SpecLoader._load_from_url(source)
        
        # 本地文件
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {source}")
        
        content = path.read_text(encoding='utf-8')
        return SpecLoader._parse_content(content, path.suffix)
    
    @staticmethod
    def _load_from_url(url: str) -> Dict:
        """从URL加载"""
        try:
            req = urllib.request.Request(
                url,
                headers={
                    'User-Agent': 'APIChangeForge/1.0',
                    'Accept': 'application/json,*/*'
                }
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read().decode('utf-8')
                return SpecLoader._parse_content(content, '.json')
        except urllib.error.URLError as e:
            raise ConnectionError(f"Failed to fetch URL: {e}")
    
    @staticmethod
    def _parse_content(content: str, suffix: str) -> Dict:
        """解析内容"""
        content = content.strip()
        
        # 尝试JSON解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # YAML解析（简化实现）
        if suffix in ('.yaml', '.yml'):
            return SpecLoader._parse_yaml(content)
        
        raise ValueError("Unsupported file format")
    
    @staticmethod
    def _parse_yaml(content: str) -> Dict:
        """简化YAML解析器"""
        # 基本YAML到JSON转换
        result = {}
        current = result
        stack = []
        last_key = None
        
        for line in content.split('\n'):
            if not line.strip() or line.strip().startswith('#'):
                continue
            
            indent = len(line) - len(line.lstrip())
            stripped = line.strip()
            
            # 键值对
            if ':' in stripped:
                key, value = stripped.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if value:
                    # 简单值
                    current[key] = SpecLoader._yaml_value(value)
                else:
                    # 嵌套对象
                    current[key] = {}
                    last_key = key
            
        return result
    
    @staticmethod
    def _yaml_value(value: str) -> Any:
        """转换YAML值"""
        value = value.strip()
        
        # 布尔值
        if value.lower() in ('true', 'yes', 'on'):
            return True
        if value.lower() in ('false', 'no', 'off'):
            return False
        
        # null
        if value.lower() in ('null', '~', ''):
            return None
        
        # 数字
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        # 字符串（去除引号）
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return value[1:-1]
        
        return value
    
    @staticmethod
    def detect_format(data: Dict) -> str:
        """检测规范格式"""
        if "openapi" in data or "swagger" in data:
            return "openapi"
        if "info" in data and "item" in data:
            return "postman"
        if "log" in data and "entries" in data.get("log", {}):
            return "har"
        return "unknown"


class DiffEngine:
    """差异检测引擎"""
    
    def __init__(self, old_spec: APISpec, new_spec: APISpec):
        self.old_spec = old_spec
        self.new_spec = new_spec
        self.changes: List[Change] = []
    
    def detect_changes(self) -> List[Change]:
        """检测所有变更"""
        self._detect_endpoint_changes()
        self._detect_parameter_changes()
        self._detect_response_changes()
        self._detect_security_changes()
        self._detect_schema_changes()
        
        # 按严重程度排序
        severity_order = {
            ChangeSeverity.BREAKING: 0,
            ChangeSeverity.POTENTIALLY_BREAKING: 1,
            ChangeSeverity.DEPRECATED: 2,
            ChangeSeverity.NON_BREAKING: 3,
            ChangeSeverity.ENHANCEMENT: 4
        }
        self.changes.sort(key=lambda c: severity_order.get(c.severity, 5))
        
        return self.changes
    
    def _detect_endpoint_changes(self):
        """检测端点变更"""
        old_endpoints = {(e.path, e.method): e for e in self.old_spec.endpoints}
        new_endpoints = {(e.path, e.method): e for e in self.new_spec.endpoints}
        
        # 新增的端点
        for key, endpoint in new_endpoints.items():
            if key not in old_endpoints:
                self.changes.append(Change(
                    change_type=ChangeType.ENDPOINT_ADDED,
                    severity=ChangeSeverity.ENHANCEMENT,
                    path=f"{endpoint.method} {endpoint.path}",
                    description=f"新增端点: {endpoint.method} {endpoint.path}",
                    new_value={"summary": endpoint.summary, "tags": endpoint.tags},
                    suggestion="这是一个新端点，客户端可以考虑使用它来实现新功能"
                ))
        
        # 删除的端点
        for key, endpoint in old_endpoints.items():
            if key not in new_endpoints:
                self.changes.append(Change(
                    change_type=ChangeType.ENDPOINT_REMOVED,
                    severity=ChangeSeverity.BREAKING,
                    path=f"{endpoint.method} {endpoint.path}",
                    description=f"删除端点: {endpoint.method} {endpoint.path}",
                    old_value={"summary": endpoint.summary},
                    suggestion="⚠️ 破坏性变更！客户端必须停止使用此端点，寻找替代方案"
                ))
        
        # 修改的端点
        for key in old_endpoints:
            if key in new_endpoints:
                old_ep = old_endpoints[key]
                new_ep = new_endpoints[key]
                
                # 检查弃用状态
                if not old_ep.deprecated and new_ep.deprecated:
                    self.changes.append(Change(
                        change_type=ChangeType.ENDPOINT_MODIFIED,
                        severity=ChangeSeverity.DEPRECATED,
                        path=f"{new_ep.method} {new_ep.path}",
                        description=f"端点已弃用: {new_ep.method} {new_ep.path}",
                        suggestion="⚠️ 此端点已被弃用，请尽快迁移到替代方案"
                    ))
    
    def _detect_parameter_changes(self):
        """检测参数变更"""
        old_endpoints = {(e.path, e.method): e for e in self.old_spec.endpoints}
        new_endpoints = {(e.path, e.method): e for e in self.new_spec.endpoints}
        
        for key in old_endpoints:
            if key not in new_endpoints:
                continue
            
            old_ep = old_endpoints[key]
            new_ep = new_endpoints[key]
            
            old_params = {p.get("name", ""): p for p in old_ep.parameters}
            new_params = {p.get("name", ""): p for p in new_ep.parameters}
            
            # 新增参数
            for name, param in new_params.items():
                if name not in old_params:
                    severity = ChangeSeverity.BREAKING if param.get("required") else ChangeSeverity.NON_BREAKING
                    self.changes.append(Change(
                        change_type=ChangeType.PARAMETER_ADDED,
                        severity=severity,
                        path=f"{new_ep.method} {new_ep.path}",
                        description=f"新增参数 '{name}'",
                        new_value=param,
                        suggestion="新增参数" + ("（必填）- 客户端必须提供此参数" if param.get("required") else "（可选）")
                    ))
            
            # 删除参数
            for name, param in old_params.items():
                if name not in new_params:
                    self.changes.append(Change(
                        change_type=ChangeType.PARAMETER_REMOVED,
                        severity=ChangeSeverity.BREAKING,
                        path=f"{new_ep.method} {new_ep.path}",
                        description=f"删除参数 '{name}'",
                        old_value=param,
                        suggestion="⚠️ 破坏性变更！客户端需要移除对此参数的引用"
                    ))
            
            # 修改参数
            for name in old_params:
                if name in new_params:
                    old_param = old_params[name]
                    new_param = new_params[name]
                    
                    # 必填状态变更
                    old_required = old_param.get("required", False)
                    new_required = new_param.get("required", False)
                    
                    if not old_required and new_required:
                        self.changes.append(Change(
                            change_type=ChangeType.PARAMETER_REQUIRED_CHANGED,
                            severity=ChangeSeverity.BREAKING,
                            path=f"{new_ep.method} {new_ep.path}",
                            description=f"参数 '{name}' 变为必填",
                            old_value="optional",
                            new_value="required",
                            suggestion="⚠️ 破坏性变更！客户端必须确保提供此参数"
                        ))
                    
                    # 类型变更
                    old_type = old_param.get("schema", {}).get("type", old_param.get("type", "unknown"))
                    new_type = new_param.get("schema", {}).get("type", new_param.get("type", "unknown"))
                    
                    if old_type != new_type:
                        self.changes.append(Change(
                            change_type=ChangeType.PARAMETER_TYPE_CHANGED,
                            severity=ChangeSeverity.POTENTIALLY_BREAKING,
                            path=f"{new_ep.method} {new_ep.path}",
                            description=f"参数 '{name}' 类型变更: {old_type} → {new_type}",
                            old_value=old_type,
                            new_value=new_type,
                            suggestion="🟡 潜在破坏性变更！客户端需要验证参数类型兼容性"
                        ))
    
    def _detect_response_changes(self):
        """检测响应变更"""
        old_endpoints = {(e.path, e.method): e for e in self.old_spec.endpoints}
        new_endpoints = {(e.path, e.method): e for e in self.new_spec.endpoints}
        
        for key in old_endpoints:
            if key not in new_endpoints:
                continue
            
            old_ep = old_endpoints[key]
            new_ep = new_endpoints[key]
            
            # 检查成功响应(200)的结构变更
            old_200 = old_ep.responses.get("200", {})
            new_200 = new_ep.responses.get("200", {})
            
            old_schema = self._extract_schema(old_200)
            new_schema = self._extract_schema(new_200)
            
            if old_schema and new_schema:
                old_fields = set(self._get_field_paths(old_schema))
                new_fields = set(self._get_field_paths(new_schema))
                
                # 删除的字段
                removed = old_fields - new_fields
                for field in removed:
                    self.changes.append(Change(
                        change_type=ChangeType.RESPONSE_FIELD_REMOVED,
                        severity=ChangeSeverity.POTENTIALLY_BREAKING,
                        path=f"{new_ep.method} {new_ep.path}",
                        description=f"响应字段删除: '{field}'",
                        suggestion="🟡 潜在破坏性变更！客户端可能依赖此字段"
                    ))
                
                # 新增的字段
                added = new_fields - old_fields
                for field in added:
                    self.changes.append(Change(
                        change_type=ChangeType.RESPONSE_FIELD_ADDED,
                        severity=ChangeSeverity.ENHANCEMENT,
                        path=f"{new_ep.method} {new_ep.path}",
                        description=f"响应字段新增: '{field}'",
                        suggestion="客户端可以利用此新字段获取更多信息"
                    ))
    
    def _detect_security_changes(self):
        """检测安全相关变更"""
        old_schemes = set(self.old_spec.security_schemes.keys())
        new_schemes = set(self.new_spec.security_schemes.keys())
        
        # 新增安全方案
        added = new_schemes - old_schemes
        for scheme in added:
            self.changes.append(Change(
                change_type=ChangeType.SECURITY_SCHEME_CHANGED,
                severity=ChangeSeverity.ENHANCEMENT,
                path="security",
                description=f"新增安全方案: '{scheme}'",
                suggestion="客户端可以使用新的认证方式"
            ))
        
        # 删除安全方案
        removed = old_schemes - new_schemes
        for scheme in removed:
            self.changes.append(Change(
                change_type=ChangeType.SECURITY_SCHEME_CHANGED,
                severity=ChangeSeverity.BREAKING,
                path="security",
                description=f"删除安全方案: '{scheme}'",
                suggestion="⚠️ 破坏性变更！使用此认证方式的客户端需要迁移"
            ))
    
    def _detect_schema_changes(self):
        """检测Schema变更"""
        old_schemas = set(self.old_spec.schemas.keys())
        new_schemas = set(self.new_spec.schemas.keys())
        
        # 新增Schema
        added = new_schemas - old_schemas
        for schema in added:
            self.changes.append(Change(
                change_type=ChangeType.ENDPOINT_ADDED,
                severity=ChangeSeverity.ENHANCEMENT,
                path=f"schemas/{schema}",
                description=f"新增Schema定义: '{schema}'",
                suggestion="新的数据模型定义可用"
            ))
    
    def _extract_schema(self, response: Dict) -> Dict:
        """从响应中提取schema"""
        content = response.get("content", {})
        if "application/json" in content:
            return content["application/json"].get("schema", {})
        return {}
    
    def _get_field_paths(self, schema: Dict, prefix: str = "") -> List[str]:
        """获取schema中所有字段路径"""
        paths = []
        
        if "properties" in schema:
            for prop, details in schema["properties"].items():
                path = f"{prefix}.{prop}" if prefix else prop
                paths.append(path)
                
                # 递归处理嵌套对象
                if isinstance(details, dict):
                    if details.get("type") == "object" and "properties" in details:
                        paths.extend(self._get_field_paths(details, path))
                    elif details.get("type") == "array" and "items" in details:
                        paths.extend(self._get_field_paths(details["items"], path))
        
        return paths


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, changes: List[Change], old_spec: APISpec, new_spec: APISpec):
        self.changes = changes
        self.old_spec = old_spec
        self.new_spec = new_spec
    
    def generate_markdown(self) -> str:
        """生成Markdown报告"""
        lines = [
            "# 🔍 API变更检测报告",
            "",
            f"**旧版本**: {self.old_spec.version or 'N/A'}",
            f"**新版本**: {self.new_spec.version or 'N/A'}",
            f"**检测时间**: {self._get_timestamp()}",
            "",
            "## 📊 变更概览",
            "",
            self._generate_summary_table(),
            "",
            "## 🔴 破坏性变更 (Breaking Changes)",
            "",
            self._generate_changes_by_severity(ChangeSeverity.BREAKING),
            "",
            "## 🟡 潜在破坏性变更",
            "",
            self._generate_changes_by_severity(ChangeSeverity.POTENTIALLY_BREAKING),
            "",
            "## ⚠️ 已弃用功能",
            "",
            self._generate_changes_by_severity(ChangeSeverity.DEPRECATED),
            "",
            "## 🟢 非破坏性变更",
            "",
            self._generate_changes_by_severity(ChangeSeverity.NON_BREAKING),
            "",
            "## 🔵 功能增强",
            "",
            self._generate_changes_by_severity(ChangeSeverity.ENHANCEMENT),
            "",
            "## 📝 迁移建议",
            "",
            self._generate_migration_guide(),
            "",
            "---",
            "*Generated by APIChangeForge*"
        ]
        
        return '\n'.join(lines)
    
    def generate_html(self) -> str:
        """生成HTML报告"""
        changes_json = json.dumps([c.to_dict() for c in self.changes], indent=2, ensure_ascii=False)
        
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API变更检测报告</title>
    <style>
        :root {{
            --breaking: #dc3545;
            --potentially: #ffc107;
            --deprecated: #fd7e14;
            --non-breaking: #28a745;
            --enhancement: #17a2b8;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header .meta {{ opacity: 0.9; }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stat-card.breaking {{ border-top: 4px solid var(--breaking); }}
        .stat-card.potentially {{ border-top: 4px solid var(--potentially); }}
        .stat-card.deprecated {{ border-top: 4px solid var(--deprecated); }}
        .stat-card.non-breaking {{ border-top: 4px solid var(--non-breaking); }}
        .stat-card.enhancement {{ border-top: 4px solid var(--enhancement); }}
        .stat-number {{ font-size: 2.5em; font-weight: bold; margin-bottom: 5px; }}
        .stat-label {{ color: #666; font-size: 0.9em; }}
        .section {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }}
        .change-item {{
            padding: 15px;
            border-left: 4px solid #ddd;
            margin-bottom: 15px;
            background: #f8f9fa;
            border-radius: 0 8px 8px 0;
        }}
        .change-item.breaking {{ border-left-color: var(--breaking); }}
        .change-item.potentially {{ border-left-color: var(--potentially); }}
        .change-item.deprecated {{ border-left-color: var(--deprecated); }}
        .change-item.non-breaking {{ border-left-color: var(--non-breaking); }}
        .change-item.enhancement {{ border-left-color: var(--enhancement); }}
        .change-path {{ font-weight: bold; color: #555; margin-bottom: 5px; }}
        .change-desc {{ color: #333; margin-bottom: 8px; }}
        .change-suggestion {{
            font-size: 0.9em;
            color: #666;
            font-style: italic;
        }}
        .badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: bold;
            color: white;
            margin-left: 10px;
        }}
        .badge.breaking {{ background: var(--breaking); }}
        .badge.potentially {{ background: var(--potentially); color: #333; }}
        .badge.deprecated {{ background: var(--deprecated); }}
        .badge.non-breaking {{ background: var(--non-breaking); }}
        .badge.enhancement {{ background: var(--enhancement); }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 API变更检测报告</h1>
            <div class="meta">
                <p>旧版本: {self.old_spec.version or 'N/A'} → 新版本: {self.new_spec.version or 'N/A'}</p>
                <p>检测时间: {self._get_timestamp()}</p>
            </div>
        </div>
        
        <div class="stats">
            {self._generate_html_stats()}
        </div>
        
        <div class="section">
            <h2>📋 详细变更列表</h2>
            <div id="changes-list">
                {self._generate_html_changes()}
            </div>
        </div>
        
        <div class="section">
            <h2>📝 迁移建议</h2>
            {self._generate_html_migration()}
        </div>
    </div>
    
    <script>
        const changes = {changes_json};
        console.log('API Changes:', changes);
    </script>
</body>
</html>'''
    
    def generate_json(self) -> str:
        """生成JSON报告"""
        report = {
            "metadata": {
                "old_version": self.old_spec.version,
                "new_version": self.new_spec.version,
                "old_title": self.old_spec.title,
                "new_title": self.new_spec.title,
                "generated_at": self._get_timestamp(),
                "total_changes": len(self.changes)
            },
            "summary": self._generate_summary_dict(),
            "changes": [c.to_dict() for c in self.changes],
            "migration_guide": self._generate_migration_dict()
        }
        return json.dumps(report, indent=2, ensure_ascii=False)
    
    def generate_sarif(self) -> str:
        """生成SARIF格式报告（用于CI集成）"""
        sarif = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "APIChangeForge",
                        "version": __version__,
                        "informationUri": "https://github.com/yourusername/APIChangeForge"
                    }
                },
                "results": [
                    {
                        "ruleId": c.change_type.value,
                        "level": "error" if c.severity == ChangeSeverity.BREAKING else "warning",
                        "message": {"text": c.description},
                        "locations": [{
                            "physicalLocation": {
                                "artifactLocation": {"uri": c.path}
                            }
                        }]
                    }
                    for c in self.changes
                ]
            }]
        }
        return json.dumps(sarif, indent=2, ensure_ascii=False)
    
    def _generate_summary_table(self) -> str:
        """生成概览表格"""
        summary = self._generate_summary_dict()
        
        return f'''| 变更类型 | 数量 |
|---------|------|
| 🔴 破坏性变更 | {summary['breaking']} |
| 🟡 潜在破坏性 | {summary['potentially_breaking']} |
| ⚠️ 已弃用 | {summary['deprecated']} |
| 🟢 非破坏性 | {summary['non_breaking']} |
| 🔵 功能增强 | {summary['enhancement']} |
| **总计** | **{summary['total']}** |'''
    
    def _generate_summary_dict(self) -> Dict:
        """生成概览字典"""
        counts = {
            ChangeSeverity.BREAKING: 0,
            ChangeSeverity.POTENTIALLY_BREAKING: 0,
            ChangeSeverity.DEPRECATED: 0,
            ChangeSeverity.NON_BREAKING: 0,
            ChangeSeverity.ENHANCEMENT: 0
        }
        
        for change in self.changes:
            counts[change.severity] = counts.get(change.severity, 0) + 1
        
        return {
            "breaking": counts[ChangeSeverity.BREAKING],
            "potentially_breaking": counts[ChangeSeverity.POTENTIALLY_BREAKING],
            "deprecated": counts[ChangeSeverity.DEPRECATED],
            "non_breaking": counts[ChangeSeverity.NON_BREAKING],
            "enhancement": counts[ChangeSeverity.ENHANCEMENT],
            "total": len(self.changes)
        }
    
    def _generate_changes_by_severity(self, severity: ChangeSeverity) -> str:
        """按严重程度生成变更列表"""
        changes = [c for c in self.changes if c.severity == severity]
        
        if not changes:
            return "*无此类变更*"
        
        lines = []
        for change in changes:
            lines.append(f"### {change.path}")
            lines.append(f"**类型**: {change.change_type.value}")
            lines.append(f"**描述**: {change.description}")
            if change.old_value:
                lines.append(f"**旧值**: `{json.dumps(change.old_value, ensure_ascii=False)}`")
            if change.new_value:
                lines.append(f"**新值**: `{json.dumps(change.new_value, ensure_ascii=False)}`")
            lines.append(f"**建议**: {change.suggestion}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_migration_guide(self) -> str:
        """生成迁移指南"""
        breaking = [c for c in self.changes if c.severity == ChangeSeverity.BREAKING]
        deprecated = [c for c in self.changes if c.severity == ChangeSeverity.DEPRECATED]
        
        lines = []
        
        if breaking:
            lines.append("### ⚠️ 必须处理的破坏性变更")
            lines.append("")
            for c in breaking:
                lines.append(f"- **{c.path}**: {c.suggestion}")
            lines.append("")
        
        if deprecated:
            lines.append("### 📋 计划迁移的弃用功能")
            lines.append("")
            for c in deprecated:
                lines.append(f"- **{c.path}**: {c.suggestion}")
            lines.append("")
        
        if not breaking and not deprecated:
            lines.append("✅ 本次变更无破坏性修改，可以安全升级。")
        
        return '\n'.join(lines)
    
    def _generate_html_stats(self) -> str:
        """生成HTML统计卡片"""
        summary = self._generate_summary_dict()
        
        cards = [
            ("breaking", "🔴 破坏性", summary['breaking']),
            ("potentially", "🟡 潜在破坏", summary['potentially_breaking']),
            ("deprecated", "⚠️ 已弃用", summary['deprecated']),
            ("non-breaking", "🟢 非破坏", summary['non_breaking']),
            ("enhancement", "🔵 增强", summary['enhancement'])
        ]
        
        return '\n'.join([
            f'''<div class="stat-card {cls}">
                <div class="stat-number">{count}</div>
                <div class="stat-label">{label}</div>
            </div>''' for cls, label, count in cards
        ])
    
    def _generate_html_changes(self) -> str:
        """生成HTML变更列表"""
        if not self.changes:
            return "<p>无变更</p>"
        
        items = []
        for change in self.changes:
            items.append(f'''
            <div class="change-item {change.severity.value}">
                <div class="change-path">
                    {change.path}
                    <span class="badge {change.severity.value}">{change.severity.value.replace('_', ' ').title()}</span>
                </div>
                <div class="change-desc">{change.description}</div>
                <div class="change-suggestion">💡 {change.suggestion}</div>
            </div>
            ''')
        
        return '\n'.join(items)
    
    def _generate_html_migration(self) -> str:
        """生成HTML迁移指南"""
        breaking = [c for c in self.changes if c.severity == ChangeSeverity.BREAKING]
        
        if not breaking:
            return "<p>✅ 本次变更无破坏性修改，可以安全升级。</p>"
        
        items = [f"<li><strong>{c.path}</strong>: {c.suggestion}</li>" for c in breaking]
        return f"<ul>{''.join(items)}</ul>"
    
    def _generate_migration_dict(self) -> Dict:
        """生成迁移指南字典"""
        breaking = [c for c in self.changes if c.severity == ChangeSeverity.BREAKING]
        deprecated = [c for c in self.changes if c.severity == ChangeSeverity.DEPRECATED]
        
        return {
            "breaking_changes": [
                {"path": c.path, "suggestion": c.suggestion} for c in breaking
            ],
            "deprecated_features": [
                {"path": c.path, "suggestion": c.suggestion} for c in deprecated
            ],
            "safe_to_upgrade": len(breaking) == 0
        }
    
    @staticmethod
    def _get_timestamp() -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class CLI:
    """命令行接口"""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """创建参数解析器"""
        parser = argparse.ArgumentParser(
            prog='apichangeforge',
            description='🔍 APIChangeForge - 轻量级API变更智能检测与影响分析引擎',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog='''
示例:
  # 对比两个OpenAPI规范文件
  apichangeforge old_spec.json new_spec.json

  # 生成HTML报告
  apichangeforge old.yaml new.yaml -f html -o report.html

  # 对比远程URL
  apichangeforge https://api.example.com/v1/openapi.json https://api.example.com/v2/openapi.json

  # CI模式（SARIF输出）
  apichangeforge old.json new.json -f sarif -o results.sarif --fail-on-breaking
            '''
        )
        
        parser.add_argument('old_spec', help='旧版本API规范文件路径或URL')
        parser.add_argument('new_spec', help='新版本API规范文件路径或URL')
        
        parser.add_argument(
            '-f', '--format',
            choices=['markdown', 'html', 'json', 'sarif'],
            default='markdown',
            help='输出格式 (默认: markdown)'
        )
        
        parser.add_argument(
            '-o', '--output',
            help='输出文件路径 (默认: 输出到stdout)'
        )
        
        parser.add_argument(
            '--fail-on-breaking',
            action='store_true',
            help='检测到破坏性变更时返回非零退出码'
        )
        
        parser.add_argument(
            '--fail-on-potentially',
            action='store_true',
            help='检测到潜在破坏性变更时返回非零退出码'
        )
        
        parser.add_argument(
            '-v', '--version',
            action='version',
            version=f'%(prog)s {__version__}'
        )
        
        return parser
    
    def run(self, args=None):
        """运行CLI"""
        parsed_args = self.parser.parse_args(args)
        
        try:
            # 加载规范
            print(f"🔍 正在加载旧版本规范: {parsed_args.old_spec}", file=sys.stderr)
            old_data = SpecLoader.load(parsed_args.old_spec)
            
            print(f"🔍 正在加载新版本规范: {parsed_args.new_spec}", file=sys.stderr)
            new_data = SpecLoader.load(parsed_args.new_spec)
            
            # 检测格式并解析
            old_format = SpecLoader.detect_format(old_data)
            new_format = SpecLoader.detect_format(new_data)
            
            print(f"📄 旧版本格式: {old_format}", file=sys.stderr)
            print(f"📄 新版本格式: {new_format}", file=sys.stderr)
            
            # 解析规范
            if old_format == "openapi":
                old_spec = OpenAPIParser.parse(old_data)
            elif old_format == "postman":
                old_spec = PostmanParser.parse(old_data)
            elif old_format == "har":
                old_spec = HARParser.parse(old_data)
            else:
                raise ValueError(f"无法识别的旧版本格式: {old_format}")
            
            if new_format == "openapi":
                new_spec = OpenAPIParser.parse(new_data)
            elif new_format == "postman":
                new_spec = PostmanParser.parse(new_data)
            elif new_format == "har":
                new_spec = HARParser.parse(new_data)
            else:
                raise ValueError(f"无法识别的新版本格式: {new_format}")
            
            # 执行差异检测
            print("🔍 正在分析API变更...", file=sys.stderr)
            engine = DiffEngine(old_spec, new_spec)
            changes = engine.detect_changes()
            
            print(f"✅ 检测到 {len(changes)} 处变更", file=sys.stderr)
            
            # 生成报告
            generator = ReportGenerator(changes, old_spec, new_spec)
            
            if parsed_args.format == "markdown":
                output = generator.generate_markdown()
            elif parsed_args.format == "html":
                output = generator.generate_html()
            elif parsed_args.format == "json":
                output = generator.generate_json()
            elif parsed_args.format == "sarif":
                output = generator.generate_sarif()
            else:
                output = generator.generate_markdown()
            
            # 输出结果
            if parsed_args.output:
                Path(parsed_args.output).write_text(output, encoding='utf-8')
                print(f"✅ 报告已保存至: {parsed_args.output}", file=sys.stderr)
            else:
                print(output)
            
            # 检查退出码
            has_breaking = any(c.severity == ChangeSeverity.BREAKING for c in changes)
            has_potentially = any(c.severity == ChangeSeverity.POTENTIALLY_BREAKING for c in changes)
            
            if parsed_args.fail_on_breaking and has_breaking:
                print("❌ 检测到破坏性变更", file=sys.stderr)
                return 1
            
            if parsed_args.fail_on_potentially and has_potentially:
                print("❌ 检测到潜在破坏性变更", file=sys.stderr)
                return 1
            
            return 0
            
        except FileNotFoundError as e:
            print(f"❌ 错误: {e}", file=sys.stderr)
            return 2
        except ConnectionError as e:
            print(f"❌ 网络错误: {e}", file=sys.stderr)
            return 3
        except ValueError as e:
            print(f"❌ 格式错误: {e}", file=sys.stderr)
            return 4
        except Exception as e:
            print(f"❌ 未知错误: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            return 99


def main():
    """主入口"""
    cli = CLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()

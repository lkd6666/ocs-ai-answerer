#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCS脚本智能答题API - 多模型支持版本

这是一个功能完整的在线课程系统(OCS)智能答题API服务，提供以下核心功能：

核心特性：
    - 多模型支持：DeepSeek、豆包(Doubao)等多个大语言模型
    - 智能模型选择：根据题目类型（文本/图片）自动选择最合适的模型
    - 思考模式：支持深度推理模式，提高复杂题目的准确率
    - 安全认证：基于密钥的访问控制和限流保护
    - 完整的API：答题、配置管理、数据统计、CSV日志等
    - Web界面：Vue3前端 + 可视化数据分析

支持的题型：
    - 单选题 (single)
    - 多选题 (multiple)
    - 判断题 (judgement)
    - 填空题 (completion)

技术栈：
    - Flask: Web框架
    - OpenAI SDK: 统一的AI模型调用接口
    - httpx: 高性能HTTP客户端
    - CSV: 答题记录持久化

作者：开源项目
版本：v2.2.0
许可：MIT License
"""

# ==================== 标准库导入 ====================
import os
import re
import time
import csv
import base64
import copy
import secrets
import hashlib
import json
import logging
from datetime import datetime
from io import BytesIO
from functools import wraps
from collections import Counter, defaultdict
from typing import List, Dict, Any, Optional, Tuple

# ==================== 第三方库导入 ====================
from flask import Flask, request, jsonify, make_response, redirect, send_from_directory
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==================== 配置区域 ====================
# 所有配置项都从环境变量读取，支持通过.env文件或系统环境变量设置
# 配置优先级：系统环境变量 > .env文件 > 默认值

# -------------------- 预设迁移来源配置 --------------------
# 这些模型字段仅用于首次把旧 .env 配置迁移到内置预设，运行时不再直接读取它们答题
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')

DOUBAO_API_KEY = os.getenv('DOUBAO_API_KEY', '')
DOUBAO_BASE_URL = os.getenv('DOUBAO_BASE_URL', 'https://ark.cn-beijing.volces.com/api/v3')
DOUBAO_MODEL = os.getenv('DOUBAO_MODEL', 'doubao-seed-1-6-251015')

# -------------------- 内置预设配置 --------------------
BUILTIN_PRESET_BOOTSTRAP_VERSION = 1
PRESET_DEEPSEEK_V4_FLASH = 'preset_deepseek_v4_flash'
PRESET_DEEPSEEK_V4_PRO = 'preset_deepseek_v4_pro'
PRESET_DOUBAO = 'preset_doubao'
BUILTIN_PRESET_IDS = (
    PRESET_DEEPSEEK_V4_FLASH,
    PRESET_DEEPSEEK_V4_PRO,
    PRESET_DOUBAO,
)
LEGACY_PRESET_ID_MAP = {
    'system_deepseek': PRESET_DEEPSEEK_V4_FLASH,
    'system_deepseek_chat': PRESET_DEEPSEEK_V4_FLASH,
    'system_deepseek_reasoner': PRESET_DEEPSEEK_V4_PRO,
    'system_doubao': PRESET_DOUBAO,
}

# -------------------- 思考模式配置 --------------------
# 思考模式使用深度推理提高复杂题目的准确率
# 适合多选题、逻辑推理题等需要仔细分析的场景
ENABLE_REASONING = os.getenv('ENABLE_REASONING', 'false').lower() == 'true'
REASONING_EFFORT = os.getenv('REASONING_EFFORT', 'medium')  # low, medium, high
AUTO_REASONING_FOR_MULTIPLE = os.getenv('AUTO_REASONING_FOR_MULTIPLE', 'true').lower() == 'true'
AUTO_REASONING_FOR_IMAGES = os.getenv('AUTO_REASONING_FOR_IMAGES', 'true').lower() == 'true'  # 带图片题目自动启用深度思考

# -------------------- AI参数配置 --------------------
# 控制模型生成的随机性和输出长度
TEMPERATURE = float(os.getenv('TEMPERATURE', '0.1'))

# max_tokens 限制:
# - deepseek-chat: [1, 8192] (最大8K)
# - deepseek-reasoner: [1, 65536] (最大64K)
# 普通模式的 max_tokens（默认500）
MAX_TOKENS_RAW = int(os.getenv('MAX_TOKENS', '500'))
MAX_TOKENS = max(1, min(8192, MAX_TOKENS_RAW))  # 默认限制到8K（deepseek-chat的限制）

# 思考模式的 max_tokens（默认4096，可以更大以支持复杂推理）
REASONING_MAX_TOKENS_RAW = int(os.getenv('REASONING_MAX_TOKENS', '4096'))
REASONING_MAX_TOKENS = max(1, min(65536, REASONING_MAX_TOKENS_RAW))  # 限制到64K（deepseek-reasoner的限制）

TOP_P = float(os.getenv('TOP_P', '0.95'))

# -------------------- 网络配置 --------------------
# 支持HTTP代理、超时控制和自动重试
HTTP_PROXY = os.getenv('HTTP_PROXY', '')
HTTPS_PROXY = os.getenv('HTTPS_PROXY', '')
TIMEOUT = float(os.getenv('TIMEOUT', '1200.0'))  # 请求超时时间（秒）
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))  # 最大重试次数

# -------------------- 服务配置 --------------------
# Flask服务器的监听地址和端口
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# -------------------- 安全配置 --------------------
# 访问控制和限流配置，防止未授权访问和滥用
SECRET_KEY_FILE = os.getenv('SECRET_KEY_FILE', '.secret_key')  # 密钥文件路径
RATE_LIMIT_ATTEMPTS = int(os.getenv('RATE_LIMIT_ATTEMPTS', '5'))  # 允许的连续错误次数
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '300'))  # 限流时间窗口（秒）
CONFIG_EDITABLE_KEYS = (
    'ENABLE_REASONING',
    'REASONING_EFFORT',
    'AUTO_REASONING_FOR_MULTIPLE',
    'AUTO_REASONING_FOR_IMAGES',
    'TEMPERATURE',
    'MAX_TOKENS',
    'REASONING_MAX_TOKENS',
    'TOP_P',
    'HTTP_PROXY',
    'HTTPS_PROXY',
    'TIMEOUT',
    'MAX_RETRIES',
    'HOST',
    'PORT',
    'DEBUG',
    'CSV_LOG_FILE',
    'LOG_LEVEL',
)
MODEL_API_COMPAT_OPENAI = 'openai_compat'
MODEL_API_RESPONSES = 'responses'
MODEL_API_CHAT = 'chat_completions'

# ==================== 配置区域结束 ====================

# ==================== 常量定义 ====================
# HTTP状态码
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_TOO_MANY_REQUESTS = 429
HTTP_SERVER_ERROR = 500
HTTP_SERVICE_UNAVAILABLE = 503

# CSV文件列名（用于确保一致性）
CSV_HEADERS = [
    '时间戳', '题型', '题目', '选项', '原始回答', '思考过程', 
    '处理后答案', 'AI耗时(秒)', '总耗时(秒)', '模型', '思考模式',
    '输入Token', '输出Token', '总Token', '费用(元)', '提供商'
]

# 题型映射常量
QUESTION_TYPE_SINGLE = 'single'
QUESTION_TYPE_MULTIPLE = 'multiple'
QUESTION_TYPE_COMPLETION = 'completion'
QUESTION_TYPE_JUDGEMENT = 'judgement'

# 模型提供商常量
PROVIDER_DEEPSEEK = 'deepseek'
PROVIDER_DOUBAO = 'doubao'

# 配置日志（必须在SecurityManager之前初始化）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
REQUEST_TRACE_LOG_FILE = os.getenv('REQUEST_TRACE_LOG_FILE', 'ocs_request_trace.log')


def write_request_trace(event: str, request_id: str, payload: Dict[str, Any]) -> None:
    """将搜题请求追踪信息写入独立日志文件，便于排查脚本传参与顺序问题。"""
    trace_record = {
        "timestamp": datetime.now().isoformat(),
        "event": event,
        "request_id": request_id,
        "payload": payload
    }

    try:
        with open(REQUEST_TRACE_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(trace_record, ensure_ascii=False) + '\n')
    except Exception as e:
        logger.warning(f"写入请求追踪日志失败[{request_id}]: {str(e)}")


def summarize_messages_for_trace(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """将多模态 messages 压缩为可读预览，避免日志里塞入大段 base64。"""
    summarized = []
    for message in messages or []:
        content = message.get("content")
        if isinstance(content, str):
            summarized.append({
                "role": message.get("role"),
                "content": content
            })
            continue

        compact_content = []
        for item in content or []:
            item_type = item.get("type")
            if item_type == "text":
                compact_content.append({
                    "type": "text",
                    "text": item.get("text", "")
                })
            elif item_type == "image_url":
                image_url = item.get("image_url", {}).get("url", "")
                compact_content.append({
                    "type": "image_url",
                    "preview": image_url[:64] + ("..." if len(image_url) > 64 else "")
                })
        summarized.append({
            "role": message.get("role"),
            "content": compact_content
        })
    return summarized


def build_http_client_kwargs(timeout: Optional[float] = None, follow_redirects: bool = False) -> Dict[str, Any]:
    """统一构造 httpx.Client 参数，确保正式调用、测试连接、图片下载共用网络配置。"""
    client_kwargs: Dict[str, Any] = {
        'timeout': TIMEOUT if timeout is None else timeout,
        'follow_redirects': follow_redirects,
        'trust_env': True
    }

    proxy_url = HTTPS_PROXY or HTTP_PROXY
    if proxy_url:
        client_kwargs['proxy'] = proxy_url

    return client_kwargs


def create_http_client(timeout: Optional[float] = None, follow_redirects: bool = False):
    """创建统一网络配置的 httpx.Client。"""
    import httpx

    return httpx.Client(**build_http_client_kwargs(timeout=timeout, follow_redirects=follow_redirects))


def validate_config_updates(config_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """校验可编辑配置，避免写入会导致重启失败的非法值。"""
    validators = {
        'TEMPERATURE': lambda value: float(value),
        'TOP_P': lambda value: float(value),
        'TIMEOUT': lambda value: float(value),
        'MAX_TOKENS': lambda value: int(value),
        'REASONING_MAX_TOKENS': lambda value: int(value),
        'MAX_RETRIES': lambda value: int(value),
        'PORT': lambda value: int(value),
    }

    for key, parser in validators.items():
        if key not in config_data:
            continue
        value = config_data.get(key)
        if value in ('', None):
            return False, f"{key} 不能为空"
        try:
            parser(value)
        except (TypeError, ValueError):
            return False, f"{key} 的值无效: {value}"

    bool_keys = {
        'ENABLE_REASONING',
        'AUTO_REASONING_FOR_MULTIPLE',
        'AUTO_REASONING_FOR_IMAGES',
        'DEBUG',
    }
    for key in bool_keys:
        if key not in config_data:
            continue
        value = str(config_data.get(key, '')).strip().lower()
        if value not in {'true', 'false'}:
            return False, f"{key} 仅支持 true 或 false"

    return True, None


# 需要重启才能生效的配置项（绑定监听端口 / Flask 启动参数，运行中无法热更新）
CONFIG_RESTART_REQUIRED_KEYS = ('HOST', 'PORT', 'DEBUG')


def reload_runtime_config():
    """从当前环境变量重新加载运行时配置，使设置无需重启脚本即可生效。

    答题相关参数（思考模式、AI 参数、网络/代理、日志级别等）均为模块级全局变量，
    且在每次请求时读取，因此重新赋值后下一次答题立即采用新配置。
    HOST/PORT/DEBUG 绑定在服务启动阶段，运行中无法更改，不在此处重载。
    """
    global ENABLE_REASONING, REASONING_EFFORT
    global AUTO_REASONING_FOR_MULTIPLE, AUTO_REASONING_FOR_IMAGES
    global TEMPERATURE, MAX_TOKENS_RAW, MAX_TOKENS
    global REASONING_MAX_TOKENS_RAW, REASONING_MAX_TOKENS, TOP_P
    global HTTP_PROXY, HTTPS_PROXY, TIMEOUT, MAX_RETRIES

    try:
        ENABLE_REASONING = os.getenv('ENABLE_REASONING', 'false').lower() == 'true'
        REASONING_EFFORT = os.getenv('REASONING_EFFORT', 'medium')
        AUTO_REASONING_FOR_MULTIPLE = os.getenv('AUTO_REASONING_FOR_MULTIPLE', 'true').lower() == 'true'
        AUTO_REASONING_FOR_IMAGES = os.getenv('AUTO_REASONING_FOR_IMAGES', 'true').lower() == 'true'

        TEMPERATURE = float(os.getenv('TEMPERATURE', '0.1'))
        MAX_TOKENS_RAW = int(os.getenv('MAX_TOKENS', '500'))
        MAX_TOKENS = max(1, min(8192, MAX_TOKENS_RAW))
        REASONING_MAX_TOKENS_RAW = int(os.getenv('REASONING_MAX_TOKENS', '4096'))
        REASONING_MAX_TOKENS = max(1, min(65536, REASONING_MAX_TOKENS_RAW))
        TOP_P = float(os.getenv('TOP_P', '0.95'))

        HTTP_PROXY = os.getenv('HTTP_PROXY', '')
        HTTPS_PROXY = os.getenv('HTTPS_PROXY', '')
        TIMEOUT = float(os.getenv('TIMEOUT', '1200.0'))
        MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    except (ValueError, TypeError) as e:
        # 单个数值解析失败时保留旧值，避免整个进程因一次错误输入而异常
        logger.error(f"❌ 热重载运行时配置时数值解析失败，已保留旧配置: {e}")

    # 日志级别可即时调整
    log_level_name = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_name, logging.INFO)
    logging.getLogger().setLevel(log_level)

    logger.info("✅ 运行时配置已热重载（无需重启即可生效）")


# ==================== 自定义模型管理 ====================

class CustomModelManager:
    """
    自定义模型管理器：管理用户自定义的AI模型配置
    
    功能：
        1. 模型CRUD：添加、删除、更新、查询自定义模型
        2. 多模态支持：标记模型是否支持图片输入
        3. Token配置：每个模型可单独配置token参数
        4. 题型映射：为不同题型指定使用的模型
        5. 持久化存储：配置保存到JSON文件
    
    数据结构：
        models = {
            'model_id': {
                'name': '模型显示名称',
                'provider': '提供商类型（openai/custom）',
                'api_key': 'API密钥',
                'base_url': '基础URL',
                'model_name': '实际模型名称',
                'is_multimodal': True/False,
                'max_tokens': 整数,
                'temperature': 浮点数,
                'top_p': 浮点数,
                'supports_reasoning': True/False,
                'enabled': True/False,
                'created_at': '创建时间',
                'updated_at': '更新时间'
            }
        }
        
        question_type_models = {
            'single': {
                'models': ['model_id1', 'model_id2'],
                'enable_reasoning': False
            },
            'multiple': {
                'models': ['model_id1'],
                'enable_reasoning': True
            },
            'judgement': {
                'models': ['model_id1'],
                'enable_reasoning': False
            },
            'completion': {
                'models': ['model_id1'],
                'enable_reasoning': False
            },
            'image': {
                'models': ['model_id2'],
                'enable_reasoning': False
            }
        }
    """
    
    def __init__(self, config_file: str = 'custom_models.json'):
        """初始化自定义模型管理器"""
        self.config_file = config_file
        self.models = {}
        self.metadata = {
            'builtin_presets_bootstrap_version': 0
        }
        self.question_type_models = {
            'single': {'models': [], 'enable_reasoning': False},
            'multiple': {'models': [], 'enable_reasoning': True},
            'judgement': {'models': [], 'enable_reasoning': False},
            'completion': {'models': [], 'enable_reasoning': False},
            'image': {'models': [], 'enable_reasoning': False}
        }
        self._load_config()
    
    def _load_config(self):
        """从文件加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.models = data.get('models', {})
                    self.metadata = data.get('metadata', self.metadata)
                    self.question_type_models = data.get('question_type_models', self.question_type_models)
                    state_changed = self._normalize_loaded_state()
                if not self.metadata:
                    self.metadata = {'builtin_presets_bootstrap_version': 0}
                if state_changed:
                    self._save_config()
                    logger.info("🧹 已清理无效题型映射并回写配置")
                logger.info(f"✅ 已加载 {len(self.models)} 个自定义模型")
            except Exception as e:
                logger.error(f"❌ 加载自定义模型配置失败: {e}")
        else:
            logger.info("📝 未找到自定义模型配置文件，将使用空配置")
    
    def _save_config(self):
        """保存配置到文件"""
        try:
            data = {
                'models': self.models,
                'metadata': self.metadata,
                'question_type_models': self.question_type_models,
                'version': '1.0',
                'updated_at': datetime.now().isoformat()
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ 自定义模型配置已保存")
            return True
        except Exception as e:
            logger.error(f"❌ 保存自定义模型配置失败: {e}")
            return False

    def _normalize_loaded_state(self) -> bool:
        """规范化已加载的模型和题型映射结构。"""
        changed = False
        normalized_models = {}
        for model_id, model_config in self.models.items():
            if not isinstance(model_config, dict):
                changed = True
                continue

            normalized_config = model_config.copy()
            if 'is_builtin' not in normalized_config:
                normalized_config['is_builtin'] = bool(normalized_config.get('is_system', False))
            normalized_config.pop('is_system', None)
            normalized_config.setdefault('is_multimodal', False)
            normalized_config.setdefault('max_tokens', 2000)
            normalized_config.setdefault('temperature', 0.1)
            normalized_config.setdefault('top_p', 0.95)
            normalized_config.setdefault('supports_reasoning', False)
            normalized_config.setdefault('reasoning_param_name', 'reasoning_effort')
            normalized_config.setdefault('reasoning_param_value', 'medium')
            normalized_config.setdefault('api_protocol', MODEL_API_COMPAT_OPENAI)
            normalized_config.setdefault('enabled', True)
            if normalized_config != model_config:
                changed = True
            normalized_models[model_id] = normalized_config

        if normalized_models != self.models:
            changed = True
        self.models = normalized_models
        normalized_mappings = self._normalize_question_type_mappings(self.question_type_models)
        if normalized_mappings != self.question_type_models:
            changed = True
        self.question_type_models = normalized_mappings

        if self._sanitize_question_type_mappings():
            changed = True

        return changed

    def _normalize_question_type_mappings(self, mappings: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """统一题型映射为字典格式。"""
        normalized = {
            'single': {'models': [], 'enable_reasoning': False},
            'multiple': {'models': [], 'enable_reasoning': True},
            'judgement': {'models': [], 'enable_reasoning': False},
            'completion': {'models': [], 'enable_reasoning': False},
            'image': {'models': [], 'enable_reasoning': False}
        }

        for question_type, default_config in normalized.items():
            config = mappings.get(question_type, default_config) if isinstance(mappings, dict) else default_config
            if isinstance(config, dict):
                normalized[question_type] = {
                    'models': [str(model_id) for model_id in config.get('models', []) if model_id],
                    'enable_reasoning': bool(config.get('enable_reasoning', default_config['enable_reasoning']))
                }
            elif isinstance(config, list):
                normalized[question_type] = {
                    'models': [str(model_id) for model_id in config if model_id],
                    'enable_reasoning': default_config['enable_reasoning']
                }

        return normalized

    def _remove_model_from_mappings(self, model_id: str) -> bool:
        """从所有题型映射中移除指定模型。"""
        changed = False
        for question_type, config in self.question_type_models.items():
            if isinstance(config, dict):
                current_models = config.get('models', [])
                filtered_models = [mapped_id for mapped_id in current_models if mapped_id != model_id]
                if filtered_models != current_models:
                    self.question_type_models[question_type]['models'] = filtered_models
                    changed = True
            elif isinstance(config, list):
                filtered_models = [mapped_id for mapped_id in config if mapped_id != model_id]
                if filtered_models != config:
                    self.question_type_models[question_type] = filtered_models
                    changed = True
        return changed

    def _sanitize_question_type_mappings(self) -> bool:
        """清理题型映射中的无效模型，尤其是图片题中的非多模态模型。"""
        changed = False

        for question_type, config in self.question_type_models.items():
            if not isinstance(config, dict):
                continue

            current_models = [str(model_id) for model_id in config.get('models', []) if model_id]
            sanitized_models = []
            seen = set()

            for model_id in current_models:
                model = self.models.get(model_id)
                if not model:
                    logger.warning(f"⚠️  题型 {question_type} 映射包含不存在的模型，已移除: {model_id}")
                    changed = True
                    continue

                if model_id in seen:
                    changed = True
                    continue

                if question_type == 'image' and not model.get('is_multimodal', False):
                    logger.warning(f"⚠️  图片题映射包含非多模态模型，已移除: {model_id}")
                    changed = True
                    continue

                sanitized_models.append(model_id)
                seen.add(model_id)

            if sanitized_models != current_models:
                self.question_type_models[question_type]['models'] = sanitized_models

        return changed
    
    def add_model(self, model_id: str, model_config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        添加自定义模型
        
        Args:
            model_id: 模型唯一标识
            model_config: 模型配置字典
        
        Returns:
            (是否成功, 消息)
        """
        # 验证必需字段
        required_fields = ['name', 'provider', 'api_key', 'base_url', 'model_name']
        for field in required_fields:
            if field not in model_config:
                return False, f"缺少必需字段: {field}"
        
        # 检查是否已存在
        if model_id in self.models:
            return False, f"模型ID已存在: {model_id}"
        
        # 添加默认值
        model_config.setdefault('is_multimodal', False)
        model_config.setdefault('max_tokens', 2000)
        model_config.setdefault('temperature', 0.1)
        model_config.setdefault('top_p', 0.95)
        model_config.setdefault('supports_reasoning', False)
        model_config.setdefault('reasoning_param_name', 'reasoning_effort')  # 思考参数名称
        model_config.setdefault('reasoning_param_value', 'medium')  # 思考参数值
        model_config.setdefault('api_protocol', MODEL_API_COMPAT_OPENAI)
        model_config.setdefault('enabled', True)
        model_config.setdefault('is_builtin', False)  # 标记是否为内置预设
        model_config['created_at'] = datetime.now().isoformat()
        model_config['updated_at'] = datetime.now().isoformat()
        
        # 保存模型
        self.models[model_id] = model_config
        
        if self._save_config():
            logger.info(f"✅ 已添加自定义模型: {model_id} - {model_config['name']}")
            return True, "模型添加成功"
        else:
            # 回滚
            del self.models[model_id]
            return False, "保存配置失败"
    
    def update_model(self, model_id: str, model_config: Dict[str, Any]) -> Tuple[bool, str]:
        """更新模型配置"""
        if model_id not in self.models:
            return False, f"模型不存在: {model_id}"

        previous_model = copy.deepcopy(self.models[model_id])
        previous_mappings = copy.deepcopy(self.question_type_models)

        # 更新配置
        model_config['updated_at'] = datetime.now().isoformat()
        # 保留创建时间和内置预设标记
        model_config['created_at'] = self.models[model_id].get('created_at', datetime.now().isoformat())
        model_config['is_builtin'] = self.models[model_id].get('is_builtin', False)
        model_config.pop('is_system', None)
        
        self.models[model_id].update(model_config)
        self._sanitize_question_type_mappings()
        
        if self._save_config():
            logger.info(f"✅ 已更新模型: {model_id}")
            return True, "模型更新成功"
        else:
            self.models[model_id] = previous_model
            self.question_type_models = previous_mappings
            return False, "保存配置失败"
    
    def delete_model(self, model_id: str) -> Tuple[bool, str]:
        """删除模型"""
        if model_id not in self.models:
            return False, f"模型不存在: {model_id}"

        previous_models = copy.deepcopy(self.models)
        previous_mappings = copy.deepcopy(self.question_type_models)

        # 从题型映射中移除
        self._remove_model_from_mappings(model_id)
        
        # 删除模型
        model_name = self.models[model_id].get('name', model_id)
        del self.models[model_id]
        
        if self._save_config():
            logger.info(f"✅ 已删除模型: {model_id} - {model_name}")
            return True, "模型删除成功"
        else:
            self.models = previous_models
            self.question_type_models = previous_mappings
            return False, "保存配置失败"
    
    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """获取单个模型配置"""
        return self.models.get(model_id)
    
    def get_all_models(self, enabled_only: bool = False) -> Dict[str, Dict[str, Any]]:
        """获取所有模型配置"""
        if enabled_only:
            return {k: v for k, v in self.models.items() if v.get('enabled', True)}
        return self.models.copy()
    
    def set_question_type_models(self, question_type: str, model_ids: List[str], enable_reasoning: bool = None) -> Tuple[bool, str]:
        """
        设置题型使用的模型列表和思考模式配置
        
        Args:
            question_type: 题型（single/multiple/judgement/completion/image）
            model_ids: 模型ID列表（按优先级排序）
            enable_reasoning: 是否启用思考模式（None表示不修改现有配置）
        """
        if question_type not in self.question_type_models:
            return False, f"无效的题型: {question_type}"

        previous_mappings = copy.deepcopy(self.question_type_models)
        filtered_model_ids = []
        removed_non_multimodal = []
        seen = set()

        # 验证所有模型ID是否存在，并对图片题自动过滤非多模态模型
        for model_id in model_ids:
            if model_id not in self.models:
                return False, f"模型不存在: {model_id}"

            if model_id in seen:
                continue

            if question_type == 'image' and not self.models[model_id].get('is_multimodal', False):
                removed_non_multimodal.append(model_id)
                continue

            filtered_model_ids.append(model_id)
            seen.add(model_id)

        # 保持字典结构
        if isinstance(self.question_type_models[question_type], dict):
            self.question_type_models[question_type]['models'] = filtered_model_ids
            if enable_reasoning is not None:
                self.question_type_models[question_type]['enable_reasoning'] = enable_reasoning
        else:
            # 兼容旧格式：从列表转换为字典
            self.question_type_models[question_type] = {
                'models': filtered_model_ids,
                'enable_reasoning': enable_reasoning if enable_reasoning is not None else False
            }
        
        if self._save_config():
            logger.info(f"✅ 已设置 {question_type} 题型的模型列表和思考配置")
            if removed_non_multimodal:
                return True, f"设置成功，已自动移除 {len(removed_non_multimodal)} 个非多模态模型"
            return True, "设置成功"
        else:
            self.question_type_models = previous_mappings
            return False, "保存配置失败"
    
    def get_question_type_models(self, question_type: str) -> List[str]:
        """获取题型使用的模型列表"""
        config = self.question_type_models.get(question_type, {})
        if isinstance(config, dict):
            return config.get('models', [])
        # 兼容旧格式
        return config if isinstance(config, list) else []
    
    def get_question_type_reasoning(self, question_type: str) -> bool:
        """获取题型的思考模式配置"""
        config = self.question_type_models.get(question_type, {})
        if isinstance(config, dict):
            return config.get('enable_reasoning', False)
        return False
    
    def get_best_model_for_question(self, question_type: str, has_images: bool = False) -> Optional[str]:
        """
        为题目选择最佳模型
        
        Args:
            question_type: 题型
            has_images: 是否包含图片
        
        Returns:
            模型ID或None
        """
        # 如果有图片，优先使用图片题专用模型
        if has_images:
            image_models = self.get_question_type_models('image')
            for model_id in image_models:
                model = self.get_model(model_id)
                if model and model.get('enabled', True) and model.get('is_multimodal', False):
                    return model_id
        
        # 使用题型对应的模型
        type_models = self.get_question_type_models(question_type)
        for model_id in type_models:
            model = self.get_model(model_id)
            if model and model.get('enabled', True):
                # 如果有图片，必须是多模态模型
                if has_images and not model.get('is_multimodal', False):
                    continue
                return model_id
        
        return None

    def get_available_model_ids_for_question(self, question_type: str, has_images: bool = False) -> List[str]:
        """获取指定题目的可用模型列表，保留优先级与图片题回退顺序。"""
        candidate_ids = []
        seen = set()

        def append_models(model_ids: List[str], require_multimodal: bool = False):
            for model_id in model_ids:
                if model_id in seen:
                    continue
                model = self.get_model(model_id)
                if not model or not model.get('enabled', True):
                    continue
                if require_multimodal and not model.get('is_multimodal', False):
                    continue
                candidate_ids.append(model_id)
                seen.add(model_id)

        if has_images:
            append_models(self.get_question_type_models('image'), require_multimodal=True)

        append_models(self.get_question_type_models(question_type), require_multimodal=has_images)
        return candidate_ids

    def has_available_multimodal_model(self) -> bool:
        """是否存在启用中的多模态模型。"""
        return any(
            model.get('enabled', True) and model.get('is_multimodal', False)
            for model in self.models.values()
        )

    def get_runtime_summary(self) -> Dict[str, Any]:
        """返回当前运行时模型概览。"""
        enabled_models = self.get_all_models(enabled_only=True)
        mapped_types = {}
        ready_types = []

        for question_type in self.question_type_models:
            has_images = question_type == 'image'
            model_ids = self.get_available_model_ids_for_question(question_type, has_images=has_images)
            mapped_types[question_type] = model_ids
            if model_ids:
                ready_types.append(question_type)

        can_answer_any = bool(ready_types)
        if not self.models:
            init_error = "未配置任何模型，请到模型管理页添加或启用模型"
        elif not enabled_models:
            init_error = "所有模型均已禁用，请到模型管理页启用至少一个模型"
        elif not can_answer_any:
            init_error = "未为任何题型配置可用模型，请到模型管理页设置题型映射"
        else:
            init_error = None

        return {
            'model_count': len(self.models),
            'enabled_model_count': len(enabled_models),
            'mapped_question_types': mapped_types,
            'ready_question_types': ready_types,
            'has_multimodal_model': self.has_available_multimodal_model(),
            'can_answer_any': can_answer_any,
            'init_error': init_error
        }

# 全局自定义模型管理器
custom_model_manager = CustomModelManager()

def build_builtin_preset_config(
    preset_id: str,
    source_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """创建内置预设配置，优先复用迁移来源中的密钥和基础URL。"""
    source_config = source_config or {}

    if preset_id == PRESET_DEEPSEEK_V4_FLASH:
        api_key = source_config.get('api_key', DEEPSEEK_API_KEY)
        config = {
            'name': 'DeepSeek V4 Flash',
            'provider': 'openai',
            'api_key': api_key,
            'base_url': source_config.get('base_url', DEEPSEEK_BASE_URL),
            'model_name': 'deepseek-v4-flash',
            'is_multimodal': False,
            'max_tokens': source_config.get('max_tokens', MAX_TOKENS),
            'temperature': source_config.get('temperature', TEMPERATURE),
            'top_p': source_config.get('top_p', TOP_P),
            'supports_reasoning': True,
            'reasoning_param_name': source_config.get('reasoning_param_name', 'reasoning_effort'),
            'reasoning_param_value': source_config.get('reasoning_param_value', REASONING_EFFORT),
            'api_protocol': source_config.get('api_protocol', MODEL_API_COMPAT_OPENAI),
            'enabled': bool(api_key),
            'is_builtin': True
        }
    elif preset_id == PRESET_DEEPSEEK_V4_PRO:
        api_key = source_config.get('api_key', DEEPSEEK_API_KEY)
        config = {
            'name': 'DeepSeek V4 Pro',
            'provider': 'openai',
            'api_key': api_key,
            'base_url': source_config.get('base_url', DEEPSEEK_BASE_URL),
            'model_name': 'deepseek-v4-pro',
            'is_multimodal': False,
            'max_tokens': source_config.get('max_tokens', REASONING_MAX_TOKENS),
            'temperature': source_config.get('temperature', TEMPERATURE),
            'top_p': source_config.get('top_p', TOP_P),
            'supports_reasoning': True,
            'reasoning_param_name': source_config.get('reasoning_param_name', 'reasoning_effort'),
            'reasoning_param_value': source_config.get('reasoning_param_value', REASONING_EFFORT),
            'api_protocol': source_config.get('api_protocol', MODEL_API_COMPAT_OPENAI),
            'enabled': bool(api_key),
            'is_builtin': True
        }
    else:
        api_key = source_config.get('api_key', DOUBAO_API_KEY)
        config = {
            'name': 'Doubao',
            'provider': 'openai',
            'api_key': api_key,
            'base_url': source_config.get('base_url', DOUBAO_BASE_URL),
            'model_name': source_config.get('model_name', DOUBAO_MODEL),
            'is_multimodal': True,
            'max_tokens': source_config.get('max_tokens', MAX_TOKENS),
            'temperature': source_config.get('temperature', TEMPERATURE),
            'top_p': source_config.get('top_p', TOP_P),
            'supports_reasoning': True,
            'reasoning_param_name': source_config.get('reasoning_param_name', 'reasoning_effort'),
            'reasoning_param_value': source_config.get('reasoning_param_value', REASONING_EFFORT),
            'api_protocol': source_config.get('api_protocol', MODEL_API_COMPAT_OPENAI),
            'enabled': bool(api_key),
            'is_builtin': True
        }

    return config


def bootstrap_builtin_presets():
    """首次将旧系统模型和 .env 凭据迁移为可编辑的内置预设。"""
    manager = custom_model_manager
    current_version = int(manager.metadata.get('builtin_presets_bootstrap_version', 0) or 0)
    if current_version >= BUILTIN_PRESET_BOOTSTRAP_VERSION:
        return

    changed = False
    legacy_models = {}
    for legacy_id, preset_id in LEGACY_PRESET_ID_MAP.items():
        legacy_config = manager.models.pop(legacy_id, None)
        if legacy_config:
            legacy_models[legacy_id] = legacy_config
            changed = True

    preset_sources = {
        PRESET_DEEPSEEK_V4_FLASH: (
            legacy_models.get('system_deepseek_chat')
            or legacy_models.get('system_deepseek')
        ),
        PRESET_DEEPSEEK_V4_PRO: (
            legacy_models.get('system_deepseek_reasoner')
            or legacy_models.get('system_deepseek_chat')
            or legacy_models.get('system_deepseek')
        ),
        PRESET_DOUBAO: legacy_models.get('system_doubao')
    }

    for preset_id in BUILTIN_PRESET_IDS:
        if preset_id in manager.models:
            manager.models[preset_id]['is_builtin'] = True
            manager.models[preset_id].pop('is_system', None)
            continue

        preset_config = build_builtin_preset_config(preset_id, preset_sources.get(preset_id))
        preset_config['created_at'] = datetime.now().isoformat()
        preset_config['updated_at'] = datetime.now().isoformat()
        manager.models[preset_id] = preset_config
        changed = True

    for question_type, config in manager.question_type_models.items():
        if not isinstance(config, dict):
            continue
        replaced_ids = []
        seen = set()
        for model_id in config.get('models', []):
            mapped_id = LEGACY_PRESET_ID_MAP.get(model_id, model_id)
            if mapped_id not in manager.models or mapped_id in seen:
                continue
            replaced_ids.append(mapped_id)
            seen.add(mapped_id)
        if replaced_ids != config.get('models', []):
            manager.question_type_models[question_type]['models'] = replaced_ids
            changed = True

    default_mappings = {
        'single': [PRESET_DEEPSEEK_V4_FLASH],
        'multiple': [PRESET_DEEPSEEK_V4_PRO, PRESET_DEEPSEEK_V4_FLASH],
        'judgement': [PRESET_DEEPSEEK_V4_FLASH],
        'completion': [PRESET_DEEPSEEK_V4_FLASH],
        'image': [PRESET_DOUBAO]
    }

    for question_type, default_ids in default_mappings.items():
        if manager.get_question_type_models(question_type):
            continue

        available_ids = []
        for model_id in default_ids:
            model = manager.get_model(model_id)
            if not model or not model.get('enabled', True):
                continue
            if question_type == 'image' and not model.get('is_multimodal', False):
                continue
            available_ids.append(model_id)

        if available_ids:
            manager.question_type_models[question_type]['models'] = available_ids
            changed = True

    manager.metadata['builtin_presets_bootstrap_version'] = BUILTIN_PRESET_BOOTSTRAP_VERSION
    manager.metadata['builtin_presets_bootstrapped_at'] = datetime.now().isoformat()
    changed = True

    if changed:
        manager._save_config()
        logger.info("✅ 已完成内置预设初始化/迁移")


try:
    bootstrap_builtin_presets()
except Exception as e:
    logger.warning(f"内置预设初始化失败: {e}")

# ==================== 安全认证系统 ====================

class SecurityManager:
    """
    安全管理器：处理API密钥认证和请求限流
    
    功能：
        1. 密钥管理：生成、验证和更新访问密钥
        2. 限流保护：基于IP的失败尝试记录和限流
        3. 密钥存储：使用SHA256哈希存储密钥，保证安全性
    
    Attributes:
        key_file (str): 密钥文件路径
        secret_key_hash (str): 密钥的SHA256哈希值
        failed_attempts (defaultdict): IP到失败时间戳列表的映射
        rate_limit_attempts (int): 允许的最大连续失败次数
        rate_limit_window (int): 限流时间窗口（秒）
    """
    
    def __init__(self, key_file=SECRET_KEY_FILE):
        self.key_file = key_file
        self.secret_key_hash = None
        self.failed_attempts = defaultdict(list)  # IP -> [timestamp1, timestamp2, ...]
        self.rate_limit_attempts = RATE_LIMIT_ATTEMPTS
        self.rate_limit_window = RATE_LIMIT_WINDOW
        
        # 初始化密钥
        self._init_secret_key()
    
    def _init_secret_key(self):
        """
        初始化访问密钥
        
        行为：
            - 如果密钥文件存在：加载现有密钥的哈希值
            - 如果密钥文件不存在：生成新的随机密钥并保存
        
        注意：
            首次生成时会在日志中显示明文密钥，请妥善保管
        """
        if os.path.exists(self.key_file):
            # 加载现有密钥
            try:
                with open(self.key_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.secret_key_hash = data.get('key_hash')
                    logger.info(f"✅ 已加载现有访问密钥")
            except Exception as e:
                logger.error(f"❌ 加载密钥失败: {e}，将生成新密钥")
                self._generate_new_key()
        else:
            # 首次启动，生成新密钥
            self._generate_new_key()
    
    def _generate_new_key(self):
        """
        生成新的64位随机密钥
        
        过程：
            1. 使用secrets.token_hex生成256位熵的随机密钥
            2. 计算密钥的SHA256哈希值用于验证
            3. 将密钥和哈希值保存到文件
            4. 在日志中显示明文密钥（仅此一次）
        
        安全性：
            - 使用加密安全的随机数生成器
            - 只在首次生成时保存明文密钥到文件
            - 后续只使用哈希值进行验证
        """
        # 生成64位随机hex字符串（256位熵）
        raw_key = secrets.token_hex(32)  # 32字节 = 64个hex字符
        
        # 存储密钥的SHA256哈希值
        self.secret_key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        # 保存到文件
        try:
            with open(self.key_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'key_hash': self.secret_key_hash,
                    'created_at': datetime.now().isoformat(),
                    'raw_key': raw_key  # 仅首次生成时保存明文密钥
                }, f, indent=2)
            
            logger.info("=" * 80)
            logger.info("🔐 首次启动：已生成访问密钥")
            logger.info("=" * 80)
            logger.info(f"   访问密钥: {raw_key}")
            logger.info("=" * 80)
            logger.info(f"⚠️  请妥善保管此密钥！")
            logger.info(f"   - 密钥已保存到: {self.key_file}")
            logger.info(f"   - 访问配置页面和敏感接口需要此密钥")
            logger.info(f"   - 可在配置页面修改密钥")
            logger.info("=" * 80)
        except Exception as e:
            logger.error(f"❌ 保存密钥失败: {e}")
    
    def verify_key(self, provided_key: str) -> bool:
        """
        验证提供的密钥是否正确
        
        Args:
            provided_key: 用户提供的密钥
        
        Returns:
            bool: 密钥正确返回True，否则返回False
        
        实现：
            通过比较SHA256哈希值来验证密钥，避免明文比较
        """
        if not provided_key:
            return False
        
        provided_hash = hashlib.sha256(provided_key.encode()).hexdigest()
        return provided_hash == self.secret_key_hash
    
    def update_key(self, old_key: str, new_key: str) -> Tuple[bool, str]:
        """更新密钥"""
        # 验证旧密钥
        if not self.verify_key(old_key):
            return False, "旧密钥错误"
        
        # 验证新密钥格式（至少8字符，像普通密码）
        if len(new_key) < 8:
            return False, "新密钥长度至少8字符"
        
        # 生成新密钥的哈希
        new_hash = hashlib.sha256(new_key.encode()).hexdigest()
        
        # 保存新密钥
        try:
            with open(self.key_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'key_hash': new_hash,
                    'updated_at': datetime.now().isoformat()
                }, f, indent=2)
            
            self.secret_key_hash = new_hash
            logger.info("✅ 访问密钥已更新")
            return True, "密钥更新成功"
        except Exception as e:
            logger.error(f"❌ 更新密钥失败: {e}")
            return False, f"更新失败: {str(e)}"
    
    def check_rate_limit(self, ip: str) -> Tuple[bool, str]:
        """检查IP是否被限流"""
        now = time.time()
        
        # 清理过期的失败记录
        self.failed_attempts[ip] = [
            ts for ts in self.failed_attempts[ip]
            if now - ts < self.rate_limit_window
        ]
        
        # 检查是否超过限制
        if len(self.failed_attempts[ip]) >= self.rate_limit_attempts:
            remaining_time = int(self.rate_limit_window - (now - self.failed_attempts[ip][0]))
            return False, f"错误次数过多，请{remaining_time}秒后重试"
        
        return True, ""
    
    def record_failed_attempt(self, ip: str):
        """记录失败的认证尝试"""
        self.failed_attempts[ip].append(time.time())
    
    def clear_failed_attempts(self, ip: str):
        """清除失败记录（认证成功后调用）"""
        if ip in self.failed_attempts:
            del self.failed_attempts[ip]

# 全局安全管理器
security_manager = SecurityManager()

def require_auth(f):
    """装饰器：要求API密钥认证"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 获取客户端IP
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        # 检查限流
        allowed, message = security_manager.check_rate_limit(client_ip)
        if not allowed:
            return jsonify({"error": message, "code": "RATE_LIMITED"}), 429
        
        # 从请求头或查询参数获取密钥
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            security_manager.record_failed_attempt(client_ip)
            return jsonify({"error": "缺少API密钥", "code": "MISSING_KEY"}), 401
        
        # 验证密钥
        if not security_manager.verify_key(api_key):
            security_manager.record_failed_attempt(client_ip)
            return jsonify({"error": "API密钥无效", "code": "INVALID_KEY"}), 403
        
        # 认证成功，清除失败记录
        security_manager.clear_failed_attempts(client_ip)
        
        return f(*args, **kwargs)
    return decorated_function

# ==================== 安全认证系统结束 ====================

app = Flask(__name__)
CORS(app)

# 题型映射
QUESTION_TYPES = {
    0: "single",
    1: "multiple",
    3: "completion",
    4: "judgement"
}


class PromptBuilder:
    """
    智能Prompt构建器：根据题型生成优化的提示词
    
    功能：
        为不同题型（单选、多选、判断、填空）生成专门优化的提示词，
        确保AI模型能够准确理解题目要求并返回正确格式的答案。
    
    设计原则：
        1. 清晰的题目类型说明
        2. 明确的回答格式要求
        3. 具体的示例演示
        4. 避免AI添加额外的解释
    """
    
    @staticmethod
    def build_prompt(question: str, options: List[str], q_type: str, use_option_labels: bool = False) -> str:
        """根据题型构建prompt"""
        
        if q_type == "single":
            return PromptBuilder._build_single_choice_prompt(question, options, use_option_labels)
        elif q_type == "multiple":
            return PromptBuilder._build_multiple_choice_prompt(question, options, use_option_labels)
        elif q_type == "judgement":
            return PromptBuilder._build_judgement_prompt(question, options)
        elif q_type == "completion":
            return PromptBuilder._build_completion_prompt(question)
        else:
            return PromptBuilder._build_default_prompt(question, options)
    
    @staticmethod
    def _build_single_choice_prompt(question: str, options: List[str], use_option_labels: bool = False) -> str:
        """构建单选题prompt"""
        options_text = "\n".join([f"{chr(65+i)}. {opt}" for i, opt in enumerate(options)])
        answer_format = """4. 回答格式：直接输出选项字母，例如 A、B、C、D
5. 如果选项是图片，必须根据图片标签选择对应字母，不要输出图片里的数值、公式或文字
6. 只输出一个字母，不要有任何解释、分析或额外文字"""
        example = """如果正确答案是 A 选项，则只输出：A"""
        if not use_option_labels:
            answer_format = """4. 回答格式：直接输出选项内容，不要包含A、B、C等标识符
5. 只输出答案内容，不要有任何解释、分析或额外文字"""
            example = """如果正确答案是选项"北京"，则只输出：北京"""
        
        return f"""你是一个专业的在线考试答题助手，请严格按照要求回答。

【题目类型】单选题（只能选择一个正确答案）

【题目】
{question}

【选项】
{options_text}

【回答要求】
1. 仔细分析题目和所有选项
2. 只选择一个最正确的答案
3. 必须从给定的选项中选择，不能自己编造
{answer_format}

【示例】
{example}

现在请回答上述题目："""

    @staticmethod
    def _build_multiple_choice_prompt(question: str, options: List[str], use_option_labels: bool = False) -> str:
        """构建多选题prompt"""
        options_text = "\n".join([f"{chr(65+i)}. {opt}" for i, opt in enumerate(options)])
        answer_format = """5. 回答格式：A#B#C（只包含选项字母，多个答案之间用井号#分隔）
6. 如果选项是图片，必须根据图片标签选择对应字母，不要输出图片里的数值、公式或文字
7. 只输出选项字母，不要有任何解释、分析或额外文字"""
        example = """如果正确答案是 A 和 C 两个选项，则输出：A#C"""
        if not use_option_labels:
            answer_format = """5. 回答格式：选项1#选项2#选项3（不要包含A、B、C等标识符）
6. 只输出答案内容，不要有任何解释、分析或额外文字"""
            example = """如果正确答案是"北京"和"上海"两个选项，则输出：北京#上海"""
        
        return f"""你是一个专业的在线考试答题助手，请严格按照要求回答。

【题目类型】多选题（可能有多个正确答案）

【题目】
{question}

【选项】
{options_text}

【回答要求】
1. 仔细分析题目，找出所有正确的选项
2. 多选题通常有2个或以上的正确答案
3. 必须从给定的选项中选择，不能自己编造
4. 多个答案之间用井号#分隔
{answer_format}

【示例】
{example}

现在请回答上述题目："""

    @staticmethod
    def _build_judgement_prompt(question: str, options: List[str]) -> str:
        """构建判断题prompt"""
        return f"""你是一个专业的在线考试答题助手，请严格按照要求回答。

【题目类型】判断题（判断对错/是否）

【题目】
{question}

【可选答案】
{chr(10).join(options) if options else "正确 / 错误"}

【回答要求】
1. 仔细分析题目陈述是否正确
2. 必须从给定的选项中选择（如：正确/错误、对/错、是/否、√/×等）
3. 只输出一个判断结果
4. 不要有任何解释、分析或额外文字

【示例】
如果题目陈述正确，且选项中有"正确"，则输出：正确

现在请判断上述题目："""

    @staticmethod
    def _build_completion_prompt(question: str) -> str:
        """构建填空题prompt"""
        return f"""你是一个专业的在线考试答题助手，请严格按照要求回答。

【题目类型】填空题

【题目】
{question}

【回答要求】
1. 仔细理解题目要求
2. 给出准确、简洁的答案
3. 如果有多个空，答案之间用井号#分隔
4. 答案要具体、准确，避免模糊表述
5. 只输出答案内容，不要有序号、解释或额外文字

【示例】
- 单空题：如果答案是"北京"，则输出：北京
- 多空题：如果答案是"氢"和"氧"，则输出：氢#氧

现在请回答上述填空题："""

    @staticmethod
    def _build_default_prompt(question: str, options: List[str]) -> str:
        """构建默认prompt"""
        options_text = "\n".join([f"- {opt}" for opt in options]) if options else "无固定选项"
        
        return f"""请回答以下问题：

【题目】
{question}

【选项】
{options_text}

【要求】
1. 给出准确的答案
2. 如果有多个答案，用#分隔
3. 只输出答案，不要解释

请回答："""


class AnswerProcessor:
    """
    答案处理器：清洗和标准化AI返回的答案
    
    策略：
        - 保守清洗：只移除明显的格式标记，避免误删正确内容
        - 优先匹配：优先使用原始答案匹配选项，再尝试清洗后匹配
        - 智能匹配：支持精确匹配、包含匹配、去标点匹配等多种方式
    
    功能：
        1. 清洗答案：移除格式标记（markdown、选项标识等）
        2. 匹配选项：将AI答案与题目选项进行智能匹配
        3. 处理特殊题型：针对判断题、多选题等进行特殊处理
    """
    
    @staticmethod
    def _clean_answer(text: str) -> str:
        """
        轻度清洗，只移除明显的格式标记
        不进行内容修改，避免误删正确答案
        """
        if not text:
            return ""
        
        # 只移除行首的常见前缀（不影响答案内容）
        text = re.sub(r'^(答案[是为：:]*|正确答案[是为：:]*|选择[：:]*)', '', text)
        text = text.strip()
        
        # 只移除markdown的格式符号（不是内容）
        text = re.sub(r'[*`_]', '', text)
        text = text.strip()
        
        # 只移除行首的选项标识（如 "A. "），但不影响答案本身
        text = re.sub(r'^[A-Z][.、)]\s*', '', text)
        text = text.strip()
        
        return text
    
    @staticmethod
    def _match_option(answer: str, option: str) -> bool:
        """
        智能匹配答案和选项
        优先精确匹配，再模糊匹配
        """
        answer = answer.strip()
        option = option.strip()
        
        if not answer or not option:
            return False
        
        # 精确匹配（忽略大小写和空格）
        if answer.lower() == option.lower():
            return True
        
        # 包含匹配
        if answer.lower() in option.lower() or option.lower() in answer.lower():
            return True
        
        # 去除标点符号后匹配
        answer_clean = re.sub(r'[。，、；：！？\s]', '', answer)
        option_clean = re.sub(r'[。，、；：！？\s]', '', option)
        if answer_clean.lower() == option_clean.lower():
            return True
        
        return False
    
    @staticmethod
    def _extract_option_indexes(answer: str, options: List[str]) -> List[int]:
        """从 A/B/C 或 Option A 这类回答中提取选项下标。"""
        if not answer or not options:
            return []

        max_label = chr(64 + min(len(options), 26))
        upper_answer = answer.upper()
        char_range = f"A-{max_label}"
        patterns = [
            rf'选项\s*([{char_range}])',
            rf'OPTION\s*([{char_range}])',
            rf'(?<![A-Z0-9])([{char_range}])(?![A-Z0-9])',
        ]

        indexes = []
        for pattern in patterns:
            for match in re.finditer(pattern, upper_answer):
                idx = ord(match.group(1)) - 65
                if 0 <= idx < len(options) and idx not in indexes:
                    indexes.append(idx)

        compact = re.sub(r'[^A-Z]', '', upper_answer)
        if not indexes and compact and all('A' <= ch <= max_label for ch in compact):
            for ch in compact:
                idx = ord(ch) - 65
                if idx not in indexes:
                    indexes.append(idx)

        return indexes

    @staticmethod
    def _option_indexes_to_answer(indexes: List[int], options: List[str]) -> str:
        return "#".join(options[idx].strip() for idx in indexes if 0 <= idx < len(options))

    @staticmethod
    def resolve_answer_for_ocs(processed_answer: str, raw_answer: str, q_type: str,
                               options: List[str], use_option_labels: bool = False) -> str:
        """
        为 OCS 脚本生成最终用于匹配的答案。

        当选项里包含图片时，OCS 实际上传给后端的 options 往往是图片 URL。
        这时模型虽然应该返回 A/B/C/D，但回传给脚本时更稳妥的做法是把字母
        再映射回对应的原始选项字符串（通常就是图片 URL），避免前端按字母
        再做二次匹配时出现错位。
        """
        if not processed_answer:
            return processed_answer

        if not use_option_labels or q_type not in {"single", "multiple"} or not options:
            return processed_answer

        indexes = AnswerProcessor._extract_option_indexes(processed_answer, options)
        if not indexes and raw_answer:
            indexes = AnswerProcessor._extract_option_indexes(raw_answer, options)

        if indexes:
            resolved = AnswerProcessor._option_indexes_to_answer(indexes, options)
            if resolved:
                return resolved

        return processed_answer

    @staticmethod
    def process_answer(raw_answer: str, q_type: str, options: List[str], use_option_labels: bool = False) -> str:
        """
        处理和清洗答案 - 保守策略，优先保留原始答案
        """
        if not raw_answer:
            return ""
        
        raw_answer = raw_answer.strip()
        
        # 根据题型处理
        if q_type == "single":
            return AnswerProcessor._process_single_choice(raw_answer, options, use_option_labels)
        elif q_type == "multiple":
            return AnswerProcessor._process_multiple_choice(raw_answer, options, use_option_labels)
        elif q_type == "judgement":
            return AnswerProcessor._process_judgement(raw_answer, options)
        elif q_type == "completion":
            # 填空题只做轻度清洗，保留原始答案
            cleaned = AnswerProcessor._clean_answer(raw_answer)
            return cleaned if cleaned else raw_answer
        else:
            # 其他题型只做轻度清洗
            cleaned = AnswerProcessor._clean_answer(raw_answer)
            return cleaned if cleaned else raw_answer
    
    @staticmethod
    def _process_single_choice(raw_answer: str, options: List[str], use_option_labels: bool = False) -> str:
        """处理单选题答案 - 优先使用原始答案匹配"""
        if not options:
            # 没有选项，只做轻度清洗
            return AnswerProcessor._clean_answer(raw_answer)

        if use_option_labels:
            indexes = AnswerProcessor._extract_option_indexes(raw_answer, options)
            if indexes:
                return chr(65 + indexes[0])
        
        # 第一步：尝试用原始答案直接匹配
        for option in options:
            if AnswerProcessor._match_option(raw_answer, option):
                return option.strip()
        
        # 第二步：轻度清洗后再匹配
        cleaned = AnswerProcessor._clean_answer(raw_answer)
        if cleaned != raw_answer:  # 如果清洗有变化
            for option in options:
                if AnswerProcessor._match_option(cleaned, option):
                    return option.strip()
        
        # 第三步：如果还是匹配不到，返回清洗后的答案
        # 这样至少保留了可能的正确答案，而不是空字符串
        return cleaned if cleaned else raw_answer
    
    @staticmethod
    def _process_multiple_choice(raw_answer: str, options: List[str], use_option_labels: bool = False) -> str:
        """处理多选题答案 - 优先使用原始答案匹配"""
        if not options:
            return AnswerProcessor._clean_answer(raw_answer)

        if use_option_labels:
            indexes = AnswerProcessor._extract_option_indexes(raw_answer, options)
            if indexes:
                return "#".join(chr(65 + idx) for idx in indexes if 0 <= idx < len(options))
        
        # 分割答案（支持多种分隔符）
        raw_answers = re.split(r'[#;；、\n]', raw_answer)
        matched_options = []
        
        # 第一步：用原始答案匹配
        for raw_ans in raw_answers:
            raw_ans = raw_ans.strip()
            if not raw_ans:
                continue
            
            for option in options:
                if AnswerProcessor._match_option(raw_ans, option):
                    option_clean = option.strip()
                    if option_clean not in matched_options:
                        matched_options.append(option_clean)
                    break
        
        # 第二步：如果匹配到了，直接返回
        if matched_options:
            return "#".join(matched_options)
        
        # 第三步：尝试清洗后再匹配
        cleaned_answers = [AnswerProcessor._clean_answer(ans) for ans in raw_answers if ans.strip()]
        for cleaned_ans in cleaned_answers:
            for option in options:
                if AnswerProcessor._match_option(cleaned_ans, option):
                    option_clean = option.strip()
                    if option_clean not in matched_options:
                        matched_options.append(option_clean)
                    break
        
        # 第四步：返回匹配结果或清洗后的原始答案
        if matched_options:
            return "#".join(matched_options)
        else:
            # 如果匹配不到，返回清洗后的答案（保留可能的正确答案）
            cleaned = AnswerProcessor._clean_answer(raw_answer)
            return cleaned if cleaned else raw_answer
    
    @staticmethod
    def _process_judgement(raw_answer: str, options: List[str]) -> str:
        """处理判断题答案 - 保守策略"""
        if not options:
            return AnswerProcessor._clean_answer(raw_answer)
        
        raw_answer_lower = raw_answer.lower()
        
        # 第一步：直接匹配选项
        for option in options:
            if AnswerProcessor._match_option(raw_answer, option):
                return option.strip()
        
        # 第二步：清洗后匹配
        cleaned = AnswerProcessor._clean_answer(raw_answer)
        if cleaned != raw_answer:
            for option in options:
                if AnswerProcessor._match_option(cleaned, option):
                    return option.strip()
        
        # 第三步：语义匹配（保守）
        # 只在不匹配的情况下才进行语义判断
        cleaned_lower = cleaned.lower()
        
        # 判断"正确"倾向
        positive_words = ['正确', '对', 'true', '√', '是', 'yes', '成立']
        negative_words = ['错误', '错', 'false', '×', '否', 'no', '不成立']
        
        has_positive = any(word in cleaned_lower for word in positive_words)
        has_negative = any(word in cleaned_lower for word in negative_words)
        
        # 只在明确有倾向且没有匹配到选项时才使用
        if has_positive and not has_negative:
            for opt in options:
                opt_lower = opt.lower()
                if any(word in opt_lower for word in positive_words):
                    return opt.strip()
            # 如果选项中没有明确的正向词，返回第一个选项（通常判断题第一个是"正确"）
            return options[0].strip() if len(options) > 0 else cleaned
        
        if has_negative and not has_positive:
            for opt in options:
                opt_lower = opt.lower()
                if any(word in opt_lower for word in negative_words):
                    return opt.strip()
            # 如果选项中没有明确的负向词，返回第二个选项（通常判断题第二个是"错误"）
            return options[1].strip() if len(options) > 1 else cleaned
        
        # 无法判断，返回清洗后的原始答案
        return cleaned if cleaned else raw_answer


def download_image_as_base64(image_url: str, http_client=None) -> Optional[str]:
    """下载图片并转换为 base64 data URI。"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://mooc1.chaoxing.com/',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'image',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'cross-site',
        }

        if http_client is not None:
            logger.info(f"📥 下载图片: {image_url}")
            response = http_client.get(image_url, headers=headers)
            response.raise_for_status()
        else:
            with create_http_client(timeout=min(TIMEOUT, 30.0), follow_redirects=True) as client:
                logger.info(f"📥 下载图片: {image_url}")
                response = client.get(image_url, headers=headers)
                response.raise_for_status()

        image_data = response.content
        content_type = response.headers.get('Content-Type', 'image/jpeg')
        if 'image/' not in content_type:
            content_type = 'image/jpeg'

        base64_data = base64.b64encode(image_data).decode('utf-8')
        data_uri = f"data:{content_type};base64,{base64_data}"
        logger.info(f"✅ 图片下载成功，大小: {len(image_data)} bytes")
        return data_uri
    except Exception as e:
        logger.error(f"❌ 图片下载失败: {image_url}")
        logger.error(f"   错误: {str(e)}")
        return None


def build_multimodal_messages(
    prompt: str,
    provider_name: str,
    image_urls: Optional[List[str]] = None,
    image_items: Optional[List[Dict[str, str]]] = None,
    include_labels: bool = True,
    http_client=None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]], bool]:
    """
    构建模型消息。

    返回:
        (messages, base64_images, used_images)
    """
    image_urls = image_urls or []
    image_items = image_items or []
    use_images = bool(image_urls)

    base64_images = []
    if use_images:
        image_sources = image_items or [
            {"url": img_url, "label": f"Image {i + 1}"}
            for i, img_url in enumerate(image_urls)
        ]
        logger.info(f"🔄 开始下载 {len(image_sources)} 张图片...")
        for i, image_item in enumerate(image_sources, 1):
            img_url = image_item.get("url", "")
            base64_data = download_image_as_base64(img_url, http_client=http_client)
            if base64_data:
                base64_images.append({
                    "sequence": i,
                    "label": image_item.get("label") or f"Image {i}",
                    "url": img_url,
                    "data": base64_data
                })
            else:
                logger.warning(f"⚠️  跳过无法下载的图片: {img_url}")

        if not base64_images:
            logger.warning("⚠️  所有图片下载失败，将使用纯文本模式")
            use_images = False
        else:
            logger.info(f"✅ 成功下载 {len(base64_images)}/{len(image_sources)} 张图片")

    system_content = (
        "你是一个专业、严谨的答题助手。你必须根据题目、图片和选项给出准确的答案，"
        "严格按照要求的格式输出，不要有任何多余的内容。"
        if use_images else
        "你是一个专业、严谨的答题助手。你必须根据题目和选项给出准确的答案，"
        "严格按照要求的格式输出，不要有任何多余的内容。"
    )

    if use_images:
        user_content = []
        image_occurrences = [image_item for image_item in base64_images if image_item.get("url")]
        downloads_complete = len(base64_images) == len(image_items or image_urls)
        downloaded_counts = Counter(image_item["url"] for image_item in image_occurrences)
        prompt_counts = Counter()
        for image_url in downloaded_counts:
            prompt_counts[image_url] = prompt.count(image_url)

        can_interleave = (
            downloads_complete
            and
            bool(image_occurrences)
            and all(prompt_counts[url] >= count for url, count in downloaded_counts.items())
        )

        if can_interleave:
            logger.info("📝 使用图文混排模式")
            ordered_urls = sorted(downloaded_counts.keys(), key=len, reverse=True)
            url_pattern = '|'.join(re.escape(url) for url in ordered_urls)
            remaining_occurrences = image_occurrences.copy()
            cursor = 0

            for match in re.finditer(url_pattern, prompt):
                text_segment = prompt[cursor:match.start()]
                if text_segment.strip():
                    user_content.append({
                        "type": "text",
                        "text": text_segment.strip()
                    })

                matched_url = match.group(0)
                image_index = next(
                    (idx for idx, image_item in enumerate(remaining_occurrences) if image_item["url"] == matched_url),
                    None
                )
                if image_index is None:
                    can_interleave = False
                    logger.warning("⚠️  图文混排匹配过程中丢失图片顺序，回退传统模式")
                    break

                image_item = remaining_occurrences.pop(image_index)
                if include_labels:
                    user_content.append({
                        "type": "text",
                        "text": f"[{image_item.get('label', 'Image')}]"
                    })
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": image_item["data"]}
                })
                cursor = match.end()

            if can_interleave:
                trailing_text = prompt[cursor:]
                if trailing_text.strip():
                    user_content.append({
                        "type": "text",
                        "text": trailing_text.strip()
                    })
                if remaining_occurrences:
                    can_interleave = False
                    logger.warning("⚠️  部分已下载图片未能插回原文位置，回退传统模式")
        else:
            if not downloads_complete:
                logger.warning("⚠️  存在图片下载失败，无法完整构造图文混排，回退传统模式")
            logger.info("📝 图文混排条件不足，使用传统模式(先图片后文本)")

        if not can_interleave:
            user_content = []
            logger.info("📝 使用传统模式(先图片后文本)")
            for i, image_item in enumerate(base64_images, 1):
                if include_labels:
                    user_content.append({
                        "type": "text",
                        "text": f"[{image_item.get('label') or f'Image {i}'}]"
                    })
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": image_item["data"]}
                })
            user_content.append({"type": "text", "text": prompt})

        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ], base64_images, True

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": prompt}
    ], base64_images, False


def infer_provider_from_model(model_id: str, model_config: Optional[Dict[str, Any]] = None) -> str:
    """推断用于展示和计费的模型提供商。"""
    model_config = model_config or {}
    model_name = str(model_config.get('model_name', '')).lower()
    base_url = str(model_config.get('base_url', '')).lower()
    model_id_lower = str(model_id).lower()

    if 'doubao' in model_name or 'volces' in base_url or 'ark.cn-beijing' in base_url or 'doubao' in model_id_lower:
        return PROVIDER_DOUBAO
    if 'deepseek' in model_name or 'api.deepseek.com' in base_url or 'deepseek' in model_id_lower:
        return PROVIDER_DEEPSEEK
    return str(model_config.get('provider', 'custom'))


def should_use_openai_responses(model_config: Dict[str, Any]) -> bool:
    """判断当前模型是否应优先使用 OpenAI 官方 Responses API。"""
    protocol = str(model_config.get('api_protocol', MODEL_API_COMPAT_OPENAI) or MODEL_API_COMPAT_OPENAI)
    if protocol == MODEL_API_RESPONSES:
        return True
    if protocol == MODEL_API_CHAT:
        return False

    base_url = str(model_config.get('base_url', '')).lower().rstrip('/')
    provider = str(model_config.get('provider', '')).lower()
    if provider != 'openai':
        return False

    return (
        base_url == 'https://api.openai.com/v1'
        or base_url == 'https://api.openai.com'
        or 'api.openai.com' in base_url
    )


def build_responses_input(
    prompt: str,
    provider_name: str,
    image_urls: Optional[List[str]] = None,
    image_items: Optional[List[Dict[str, str]]] = None,
    include_labels: bool = True,
    http_client=None
) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]], bool]:
    """构建 OpenAI Responses API 所需的 input 结构。"""
    messages, base64_images, used_images = build_multimodal_messages(
        prompt,
        provider_name=provider_name,
        image_urls=image_urls,
        image_items=image_items,
        include_labels=include_labels,
        http_client=http_client
    )

    responses_input = []
    for message in messages:
        content = message.get("content")
        if isinstance(content, str):
            responses_input.append({
                "role": message["role"],
                "content": [{"type": "input_text", "text": content}]
            })
            continue

        response_content = []
        for item in content or []:
            if item.get("type") == "text":
                response_content.append({
                    "type": "input_text",
                    "text": item.get("text", "")
                })
            elif item.get("type") == "image_url":
                response_content.append({
                    "type": "input_image",
                    "image_url": item.get("image_url", {}).get("url", "")
                })
        responses_input.append({
            "role": message["role"],
            "content": response_content
        })

    return responses_input, base64_images, used_images


def extract_reasoning_from_responses_api(response: Any) -> Optional[str]:
    """尽力从 OpenAI Responses API 返回中提取可展示的 reasoning 文本。"""
    if isinstance(response, str):
        return None

    output = getattr(response, 'output', None) or []
    reasoning_parts = []

    for item in output:
        item_type = getattr(item, 'type', '') or (item.get('type', '') if isinstance(item, dict) else '')
        if item_type != 'reasoning':
            continue

        summary = getattr(item, 'summary', None)
        if summary is None and isinstance(item, dict):
            summary = item.get('summary')

        for summary_item in summary or []:
            if isinstance(summary_item, dict):
                text_value = summary_item.get('text', '')
                summary_type = summary_item.get('type', '')
            else:
                text_value = getattr(summary_item, 'text', '')
                summary_type = getattr(summary_item, 'type', '')

            if summary_type in ('summary_text', 'text', 'output_text') and str(text_value).strip():
                reasoning_parts.append(str(text_value).strip())

    if reasoning_parts:
        return "\n".join(reasoning_parts).strip()

    return None


def extract_text_from_responses_api(response: Any) -> str:
    """兼容不同 SDK 版本提取 Responses API 的文本输出。"""
    if isinstance(response, str):
        return response.strip()

    output_text = getattr(response, 'output_text', None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    output = getattr(response, 'output', None) or []
    text_parts = []
    for item in output:
        content_list = getattr(item, 'content', None) or []
        for content in content_list:
            content_type = getattr(content, 'type', '')
            if content_type in ('output_text', 'text'):
                text_value = getattr(content, 'text', None)
                if text_value:
                    text_parts.append(str(text_value))

    return "\n".join(part.strip() for part in text_parts if str(part).strip()).strip()


def extract_text_from_chat_completions(response: Any) -> str:
    """兼容不同返回格式提取 Chat Completions 文本输出。"""
    if isinstance(response, str):
        return response.strip()

    if isinstance(response, dict):
        try:
            message = response.get('choices', [{}])[0].get('message', {})
            content = message.get('content', '')
            if isinstance(content, list):
                text_parts = [
                    item.get('text', '')
                    for item in content
                    if isinstance(item, dict) and item.get('type') in ('text', 'output_text')
                ]
                return "\n".join(part.strip() for part in text_parts if str(part).strip()).strip()
            return str(content).strip()
        except Exception:
            return ''

    choices = getattr(response, 'choices', None) or []
    if not choices:
        return ''

    message = getattr(choices[0], 'message', None)
    if message is None and isinstance(choices[0], dict):
        message = choices[0].get('message')

    if isinstance(message, dict):
        content = message.get('content', '')
    else:
        content = getattr(message, 'content', '')

    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get('type') in ('text', 'output_text'):
                    text_parts.append(item.get('text', ''))
            else:
                item_type = getattr(item, 'type', '')
                if item_type in ('text', 'output_text'):
                    text_parts.append(getattr(item, 'text', ''))
        return "\n".join(part.strip() for part in text_parts if str(part).strip()).strip()

    return str(content or '').strip()


def extract_reasoning_from_chat_completions(response: Any) -> Optional[str]:
    """兼容不同返回格式提取 Chat Completions reasoning 文本。"""
    if isinstance(response, str):
        return None

    choices = []
    if isinstance(response, dict):
        choices = response.get('choices', []) or []
    else:
        choices = getattr(response, 'choices', None) or []

    if not choices:
        return None

    first_choice = choices[0]
    if isinstance(first_choice, dict):
        message = first_choice.get('message', {}) or {}
    else:
        message = getattr(first_choice, 'message', None)

    if message is None:
        return None

    direct_reasoning = (
        message.get('reasoning_content')
        if isinstance(message, dict)
        else getattr(message, 'reasoning_content', None)
    )
    if isinstance(direct_reasoning, str) and direct_reasoning.strip():
        return direct_reasoning.strip()

    content = message.get('content', []) if isinstance(message, dict) else getattr(message, 'content', [])
    if not isinstance(content, list):
        return None

    reasoning_parts = []
    for item in content:
        if isinstance(item, dict):
            item_type = item.get('type', '')
            if item_type in ('reasoning', 'reasoning_content'):
                text_value = item.get('text', '') or item.get('reasoning', '')
                if str(text_value).strip():
                    reasoning_parts.append(str(text_value).strip())
        else:
            item_type = getattr(item, 'type', '')
            if item_type in ('reasoning', 'reasoning_content'):
                text_value = getattr(item, 'text', '') or getattr(item, 'reasoning', '')
                if str(text_value).strip():
                    reasoning_parts.append(str(text_value).strip())

    if reasoning_parts:
        return "\n".join(reasoning_parts).strip()

    return None


def extract_usage_from_response(response: Any) -> Dict[str, int]:
    """统一提取 Chat Completions / Responses API 的 usage 信息。"""
    usage = getattr(response, 'usage', None)
    if not usage:
        return {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}

    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0

    if hasattr(usage, 'prompt_tokens') or hasattr(usage, 'completion_tokens') or hasattr(usage, 'total_tokens'):
        prompt_tokens = getattr(usage, 'prompt_tokens', 0) or 0
        completion_tokens = getattr(usage, 'completion_tokens', 0) or 0
        total_tokens = getattr(usage, 'total_tokens', 0) or 0
    else:
        input_tokens = getattr(usage, 'input_tokens', 0) or 0
        output_tokens = getattr(usage, 'output_tokens', 0) or 0
        total_tokens = getattr(usage, 'total_tokens', 0) or (input_tokens + output_tokens)
        prompt_tokens = input_tokens
        completion_tokens = output_tokens

    return {
        'prompt_tokens': int(prompt_tokens),
        'completion_tokens': int(completion_tokens),
        'total_tokens': int(total_tokens)
    }


def build_reasoning_payload(model_config: Dict[str, Any], force_reasoning: bool = False) -> Tuple[Optional[Dict[str, Any]], Optional[Tuple[str, Any]]]:
    """生成 reasoning 参数，兼容 Responses API 与旧参数透传。"""
    if not (force_reasoning and model_config.get('supports_reasoning', False)):
        return None, None

    param_name = model_config.get('reasoning_param_name', 'reasoning_effort')
    param_value = model_config.get('reasoning_param_value', 'medium')

    if should_use_openai_responses(model_config):
        effort = str(param_value or 'medium').strip().lower()
        if effort == 'ultra':
            effort = 'xhigh'
        if effort not in {'minimal', 'low', 'medium', 'high', 'xhigh'}:
            effort = 'medium'
        logger.info(f"🧠 启用 OpenAI Responses 思考模式: reasoning.effort={effort}, summary=auto")
        return {"effort": effort, "summary": "auto"}, None

    logger.info(f"🧠 启用思考模式: {param_name}={param_value}")
    return None, (param_name, param_value)


init_error = custom_model_manager.get_runtime_summary().get('init_error')


def format_time(seconds: float) -> str:
    """
    格式化时间显示为易读格式
    
    Args:
        seconds: 秒数
    
    Returns:
        str: 格式化后的时间字符串
             - 小于60秒："X.X秒"
             - 大于等于60秒："X分Y.Y秒"
    
    Examples:
        >>> format_time(45.5)
        '45.5秒'
        >>> format_time(125.3)
        '2分5.3秒'
    """
    if seconds < 60:
        return f"{seconds:.1f}秒"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}分{secs:.1f}秒"


def _call_custom_model(model_id: str, prompt: str, image_urls: List[str] = None, 
                       force_reasoning: bool = False,
                       image_items: List[Dict[str, str]] = None) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, int]], bool]:
    """
    调用自定义模型
    
    Args:
        model_id: 自定义模型ID
        prompt: 提示词
        image_urls: 图片URL列表
        force_reasoning: 是否强制启用思考模式
        image_items: 带标签的图片列表，用于把选项图片和A/B/C/D绑定
    
    Returns:
        (推理过程, 最终答案, token使用量, 是否实际启用思考)
    """
    model = custom_model_manager.get_model(model_id)
    if not model:
        logger.error(f"自定义模型不存在: {model_id}")
        return None, None, None, False
    
    try:
        inferred_provider = infer_provider_from_model(model_id, model)
        provider_name = inferred_provider if inferred_provider in {PROVIDER_DOUBAO, PROVIDER_DEEPSEEK} else str(model.get('provider', '') or inferred_provider or PROVIDER_DEEPSEEK)
        multimodal_urls = image_urls if model.get('is_multimodal', False) else None
        max_attempts = max(1, int(MAX_RETRIES) + 1)
        last_error = None
        reasoning_payload, legacy_reasoning = build_reasoning_payload(model, force_reasoning)
        reasoning_requested = bool(reasoning_payload or legacy_reasoning)
        use_responses_api = should_use_openai_responses(model)

        with create_http_client(timeout=TIMEOUT, follow_redirects=True) as http_client:
            input_content = None
            messages = None
            if use_responses_api:
                input_content, _, _ = build_responses_input(
                    prompt,
                    provider_name=provider_name,
                    image_urls=multimodal_urls,
                    image_items=image_items,
                    include_labels=True,
                    http_client=http_client
                )
            else:
                messages, _, _ = build_multimodal_messages(
                    prompt,
                    provider_name=provider_name,
                    image_urls=multimodal_urls,
                    image_items=image_items,
                    include_labels=True,
                    http_client=http_client
                )

            for attempt in range(1, max_attempts + 1):
                try:
                    client = OpenAI(
                        api_key=model['api_key'],
                        base_url=model['base_url'],
                        http_client=http_client,
                        max_retries=1
                    )
                
                    if use_responses_api:
                        request_params = {
                            "model": model['model_name'],
                            "input": input_content,
                            "max_output_tokens": model.get('max_tokens', 2000)
                        }

                        temperature = model.get('temperature', 0.1)
                        top_p = model.get('top_p', 0.95)
                        if temperature is not None:
                            request_params["temperature"] = temperature
                        if top_p is not None:
                            request_params["top_p"] = top_p

                        if reasoning_payload:
                            request_params["reasoning"] = reasoning_payload
                        elif legacy_reasoning:
                            request_params[legacy_reasoning[0]] = legacy_reasoning[1]

                        logger.info(
                            f"🧠 使用 Responses API 调用模型: {model.get('model_name')} "
                            f"(多模态={'是' if bool(multimodal_urls) else '否'}, 思考={'是' if reasoning_requested else '否'}, 重试 {attempt}/{max_attempts})"
                        )
                        logger.info(f"📝 Prompt预览[{model_id}]: {prompt[:1200]}")
                        logger.info(f"🧾 Responses输入预览[{model_id}]: {json.dumps(input_content, ensure_ascii=False)[:2000]}")
                        response = client.responses.create(**request_params)
                        reasoning_content = extract_reasoning_from_responses_api(response)
                        answer = extract_text_from_responses_api(response)
                        usage_info = extract_usage_from_response(response)
                        return reasoning_content, answer, usage_info, reasoning_requested

                    request_params = {
                        "model": model['model_name'],
                        "messages": messages,
                        "temperature": model.get('temperature', 0.1),
                        "max_tokens": model.get('max_tokens', 2000),
                        "top_p": model.get('top_p', 0.95),
                        "stream": False
                    }

                    if legacy_reasoning:
                        request_params[legacy_reasoning[0]] = legacy_reasoning[1]

                    logger.info(
                        f"🧠 使用 Chat Completions 调用模型: {model.get('model_name')} "
                        f"(多模态={'是' if bool(multimodal_urls) else '否'}, 思考={'是' if reasoning_requested else '否'}, 重试 {attempt}/{max_attempts})"
                    )
                    logger.info(f"📝 Prompt预览[{model_id}]: {prompt[:1200]}")
                    logger.info(f"🧾 Messages预览[{model_id}]: {json.dumps(summarize_messages_for_trace(messages), ensure_ascii=False)[:2000]}")
                    response = client.chat.completions.create(**request_params)
                
                    reasoning_content = extract_reasoning_from_chat_completions(response)
                    answer = extract_text_from_chat_completions(response)
                    usage_info = extract_usage_from_response(response)
                    return reasoning_content, answer, usage_info, reasoning_requested
                except Exception as attempt_error:
                    last_error = attempt_error
                    logger.warning(f"⚠️  模型调用尝试失败[{model_id} {attempt}/{max_attempts}]: {str(attempt_error)}")
                    if attempt < max_attempts:
                        time.sleep(1)

        logger.error(f"调用自定义模型失败: {model_id}, 错误: {str(last_error)}")
        return None, None, None, False
        
    except Exception as e:
        logger.error(f"调用自定义模型失败: {model_id}, 错误: {str(e)}")
        return None, None, None, False


def check_and_fix_csv_header(csv_file: str, correct_headers: List[str]) -> bool:
    """
    检查并自动修复CSV文件的表头格式
    
    功能：
        1. 验证CSV文件的表头是否与期望的一致
        2. 如果不一致，备份原文件并自动修复
        3. 处理列数不匹配的情况（补齐或截断）
    
    Args:
        csv_file: CSV文件路径
        correct_headers: 正确的表头列表
    
    Returns:
        bool: True表示表头正确或已成功修复，False表示修复失败
    
    注意：
        - 修复前会自动创建备份文件 (.backup)
        - 对于列数不足的行，会填充默认值
    """
    if not os.path.exists(csv_file):
        # 文件不存在，无需修复
        return True
    
    try:
        # 读取当前表头
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            current_headers = next(reader, None)
            if current_headers is None:
                # 空文件，无需修复
                return True
            
            # 检查表头是否正确
            if current_headers == correct_headers:
                # 表头正确，无需修复
                return True
            
            # 表头不正确，需要修复
            logger.warning(f"⚠️  CSV文件表头不正确，当前列数: {len(current_headers)}, 正确列数: {len(correct_headers)}")
            logger.info("🔧 开始自动修复CSV文件表头...")
            
            # 读取所有数据
            f.seek(0)
            reader = csv.reader(f)
            rows = list(reader)
        
        # 备份原文件
        backup_file = csv_file + '.backup'
        import shutil
        shutil.copy2(csv_file, backup_file)
        logger.info(f"📋 已备份到: {backup_file}")
        
        # 修复数据
        fixed_rows = [correct_headers]  # 新表头
        
        for i, row in enumerate(rows[1:], start=2):  # 跳过旧表头
            # 如果行的列数少于新表头，补充默认值
            if len(row) < len(correct_headers):
                missing_cols = len(correct_headers) - len(row)
                # 补充默认值：0, 0, 0, 0.000000, ''
                row.extend(['0'] * (missing_cols - 1) + [''])
            elif len(row) > len(correct_headers):
                # 如果列数过多，截断
                row = row[:len(correct_headers)]
            fixed_rows.append(row)
        
        # 写入修复后的文件
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            writer.writerows(fixed_rows)
        
        logger.info(f"✅ CSV文件表头修复完成，共处理 {len(fixed_rows)-1} 行数据")
        return True
        
    except Exception as e:
        logger.error(f"❌ CSV文件表头修复失败: {str(e)}")
        return False


def save_to_csv(question: str, options: List[str], q_type: str, raw_answer: str, 
                reasoning: Optional[str], processed_answer: str, ai_time: float, 
                total_time: float, model_name: str, reasoning_used: bool,
                prompt_tokens: int = 0, completion_tokens: int = 0, provider: str = ''):
    """
    保存答题记录到CSV文件
    
    Args:
        question: 题目
        options: 选项列表
        q_type: 题型
        raw_answer: AI原始回答
        reasoning: 思考过程（如果有）
        processed_answer: 处理后的答案
        ai_time: AI答题耗时（秒）
        total_time: 总耗时（秒）
        model_name: 模型名称
        reasoning_used: 是否使用了思考模式
        prompt_tokens: 输入token数
        completion_tokens: 输出token数
        provider: 模型提供商 (deepseek/doubao)
    """
    csv_file = os.getenv('CSV_LOG_FILE', 'ocs_answers_log.csv')
    
    # CSV表头
    headers = [
        '时间戳', '题型', '题目', '选项', '原始回答', '思考过程', 
        '处理后答案', 'AI耗时(秒)', '总耗时(秒)', '模型', '思考模式',
        '输入Token', '输出Token', '总Token', '费用(元)', '提供商'
    ]
    
    # 检查并修复CSV文件表头（如果需要）
    if os.path.exists(csv_file):
        check_and_fix_csv_header(csv_file, headers)
    
    # 检查文件是否存在，如果不存在则创建并写入表头
    file_exists = os.path.exists(csv_file)
    
    try:
        # 使用UTF-8 BOM编码，确保Excel可以正确显示中文
        with open(csv_file, 'a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            
            # 如果文件不存在，写入表头
            if not file_exists:
                writer.writerow(headers)
            
            # 准备数据
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            options_str = ' | '.join(options) if options else ''
            reasoning_str = reasoning if reasoning else ''
            
            # 计算费用（基于DeepSeek和豆包的官方价格）
            # DeepSeek: 输入缓存命中0.2元/百万tokens，缓存未命中2元/百万tokens，输出3元/百万tokens
            # 豆包-Seed-1.6: 推理输入0.8元/百万tokens，推理输出2元/百万tokens
            # 注意：这里假设缓存未命中（实际应该根据缓存状态判断）
            cost = 0.0
            if provider.lower() == 'deepseek':
                # DeepSeek价格（假设缓存未命中）
                input_cost = (prompt_tokens / 1000000) * 2.0  # 2元/百万tokens
                output_cost = (completion_tokens / 1000000) * 3.0  # 3元/百万tokens
                cost = input_cost + output_cost
            elif provider.lower() == 'doubao':
                # 豆包-Seed-1.6 官方价格
                input_cost = (prompt_tokens / 1000000) * 0.8  # 0.8元/百万tokens
                output_cost = (completion_tokens / 1000000) * 2.0  # 2元/百万tokens
                cost = input_cost + output_cost
            else:
                # 其他提供商价格未知，不做错误估算
                cost = 0.0
            
            total_tokens = prompt_tokens + completion_tokens
            
            # 写入数据行（所有字段都会被正确转义）
            row = [
                timestamp,
                q_type,
                question,
                options_str,
                raw_answer,
                reasoning_str,
                processed_answer,
                f"{ai_time:.2f}",
                f"{total_time:.2f}",
                model_name,
                '是' if reasoning_used else '否',
                str(prompt_tokens),
                str(completion_tokens),
                str(total_tokens),
                f"{cost:.6f}",
                provider.upper() if provider else ''
            ]
            
            writer.writerow(row)
            logger.debug(f"CSV记录已保存: {len(row)}个字段，思考过程长度: {len(reasoning_str)}")
            
    except Exception as e:
        # CSV记录失败不影响答题流程，只记录日志
        logger.warning(f"保存CSV记录失败: {str(e)}", exc_info=True)


@app.route('/api/answer', methods=['POST'])
def answer_question():
    """
    核心答题API接口
    
    功能：
        1. 接收题目信息（题目、选项、题型、图片）
        2. 调用AI模型生成答案
        3. 处理和清洗答案
        4. 记录答题日志到CSV
        5. 返回OCS脚本兼容的响应格式
    
    请求格式 (JSON):
        {
            "question": "题目内容",
            "options": ["选项1", "选项2", ...],  // 或字符串格式
            "type": 0,  // 0=单选, 1=多选, 3=填空, 4=判断
            "images": ["http://..."]  // 可选，图片URL列表
        }
    
    响应格式 (JSON):
        {
            "success": true,
            "question": "题目内容",
            "answer": "处理后的答案",
            "type": "single",
            "raw_answer": "AI原始回答",
            "model": "deepseek-chat",
            "provider": "deepseek",
            "reasoning_used": false,
            "ai_time": 1.23,
            "total_time": 1.45,
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            "ocs_format": ["题目", "答案", {...}]
        }
    
    特性：
        - 自动识别题目中的图片URL
        - 多选题自动启用思考模式
        - 图片题自动使用支持多模态的模型
        - 过滤图标类URL（video.png、icon/等）
    """
    start_time = time.time()
    request_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
    
    try:
        runtime_summary = custom_model_manager.get_runtime_summary()
        if not runtime_summary.get('can_answer_any'):
            error_msg = runtime_summary.get('init_error') or "未配置可用模型，请到模型管理页添加或启用模型"
            print(f"\n❌ {error_msg}")
            print("="*80 + "\n")
            return jsonify({
                "success": False,
                "error": error_msg,
                "hint": "请在模型管理页配置模型并设置题型映射"
            }), 500
        
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "无效的请求数据"}), 400

        logger.info(f"📥 收到搜题请求 [{request_id}]")
        write_request_trace("request_received", request_id, {
            "remote_addr": request.remote_addr,
            "user_agent": request.headers.get('User-Agent', ''),
            "json": data
        })
        
        question = data.get('question', '').strip()
        options = data.get('options', [])
        type_num = data.get('type', 0)
        images = data.get('images', [])  # 图片URL列表
        
        if not question:
            return jsonify({"success": False, "error": "题目不能为空"}), 400
        
        q_type = QUESTION_TYPES.get(type_num, "single")
        q_type_name = {"single": "单选题", "multiple": "多选题", "judgement": "判断题", "completion": "填空题"}.get(q_type, "未知题型")
        
        # 处理选项：支持多种格式
        raw_options = options
        if isinstance(options, str):
            # 如果是字符串，按换行符分割（OCS脚本传递的格式）
            options = [opt.strip() for opt in options.split('\n')]
        elif isinstance(options, list):
            # 如果是列表，清理每个选项
            options = [str(opt).strip() if opt is not None else '' for opt in options]
        else:
            # 其他格式转为空列表
            options = []

        if q_type == "completion" and options:
            logger.info(f"🧹 填空题忽略上传的选项/编辑器残留，共 {len(options)} 项")
            options = []

        write_request_trace("request_normalized", request_id, {
            "question_type": q_type,
            "type_num": type_num,
            "question": question,
            "raw_options": raw_options,
            "normalized_options": options,
            "images": images
        })
        
        # 提取题目中的图片URL
        image_urls = []
        image_items = []
        
        # 清理URL的函数（去除扩展名后可能附加的字符）
        def clean_url(url):
            """清理URL，去除扩展名后可能附加的字符"""
            url = str(url).strip()
            # 找到最后一个图片扩展名的位置
            match = re.search(r'\.(jpg|jpeg|png|gif|bmp|webp)', url, re.IGNORECASE)
            if match:
                # 只保留到扩展名结束（包括扩展名）
                end_pos = match.end()
                return url[:end_pos]
            return url
        
        prompt_image_items = []
        api_image_items = []
        
        # 从题目文本中提取图片URL（支持常见图片格式）
        # 使用非贪婪匹配，确保在遇到图片扩展名后立即停止
        # 匹配URL中的合法字符，但使用非贪婪模式避免匹配过多
        img_pattern = r'(https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+?\.(?:jpg|jpeg|png|gif|bmp|webp))'
        found_images = re.findall(img_pattern, question, re.IGNORECASE)
        
        # 清理提取的URL
        found_images = [clean_url(url) for url in found_images]
        
        if found_images:
            logger.info(f"📷 从题目中检测到 {len(found_images)} 张图片")
        for i, img_url in enumerate(found_images, 1):
            prompt_image_items.append({
                "url": img_url,
                "label": f"Question Image {i}",
                "source": "question"
            })
        
        # 从选项中提取图片URL
        found_images_in_options = []
        if options:
            for option_index, option in enumerate(options):
                option_images = re.findall(img_pattern, str(option), re.IGNORECASE)
                option_images = [clean_url(url) for url in option_images]
                if option_images:
                    option_label = chr(65 + option_index)
                    for img_url in option_images:
                        found_images_in_options.append(img_url)
                        prompt_image_items.append({
                            "url": img_url,
                            "label": f"Option {option_label}",
                            "source": "option"
                        })
            if found_images_in_options:
                logger.info(f"📷 从选项中检测到 {len(found_images_in_options)} 张图片")

        if images and isinstance(images, list):
            prompt_urls = {item["url"] for item in prompt_image_items if item.get("url")}
            for i, img in enumerate(images, 1):
                if not img:
                    continue
                img_url = clean_url(img)
                if img_url in prompt_urls:
                    continue
                api_image_items.append({
                    "url": img_url,
                    "label": f"API Image {i}",
                    "source": "api"
                })

        raw_image_items = prompt_image_items + api_image_items
        
        # 过滤掉明显的图标URL（通常不是题目内容）
        # 例如：icon/video.png, icon/audio.png, icons/ 等
        icon_keywords = ['/icon/', '/icons/', '/icon.', 'icon/', 'video.png', 'audio.png', 'play.png', 'pause.png']
        image_items = []
        for item in raw_image_items:
            img_url = item.get("url", "")
            if not img_url:
                continue

            img_url_lower = img_url.lower()
            if any(keyword in img_url_lower for keyword in icon_keywords):
                logger.debug(f"跳过图标URL: {img_url}")
                continue

            image_items.append({
                "url": img_url,
                "label": item.get("label") or f"Image {len(image_items) + 1}"
            })

        image_urls = [item["url"] for item in image_items]
        use_option_labels = q_type in ("single", "multiple") and any(
            item.get("label", "").startswith("Option ") for item in image_items
        )
        
        # 记录图片检测结果
        total_found = len(found_images) + len(found_images_in_options) + len([img for img in (images or []) if img])
        if total_found > 0:
            logger.info(f"📷 图片检测结果: 题干{len(found_images)}张, 选项{len(found_images_in_options)}张, API传入{len(images or [])}张, 过滤后{len(image_urls)}张")
            write_request_trace("request_images_detected", request_id, {
                "found_images_in_question": found_images,
                "found_images_in_options": found_images_in_options,
                "api_images": images,
                "image_items": image_items,
                "image_urls": image_urls,
                "normalized_options": options
            })
        
        # 如果过滤后没有图片，记录日志
        if len(image_urls) == 0 and total_found > 0:
            logger.debug("所有图片URL已被过滤（可能都是图标），使用纯文本模式")
        
        # 控制台输出题目信息
        print("\n" + "="*80)
        print(f"📝 【{q_type_name}】")
        print(f"题目: {question}")
        if options:
            print(f"选项: {' | '.join(options)}")
        if image_urls:
            print(f"📷 检测到图片: {len(image_urls)}张")
            if found_images_in_options and len(found_images_in_options) > 0:
                print(f"   ⚠️  选项中有图片，将自动使用豆包模型")
            for image_item in image_items:
                print(f"   {image_item.get('label')}: {image_item.get('url')}")
        print("="*80)
        
        # 构建prompt
        prompt = PromptBuilder.build_prompt(question, options, q_type, use_option_labels=use_option_labels)
        
        # 确定是否启用思考模式
        force_reasoning = False
        reasoning_reasons = []
        
        # 1. 检查题型的思考配置（优先级最高）
        type_reasoning_enabled = custom_model_manager.get_question_type_reasoning(q_type)
        if type_reasoning_enabled:
            force_reasoning = True
            reasoning_reasons.append("题型配置")

        # 1.5. 全局思考开关
        if ENABLE_REASONING:
            force_reasoning = True
            if "全局配置" not in reasoning_reasons:
                reasoning_reasons.append("全局配置")
        
        # 2. 兼容旧的自动启用逻辑
        if q_type == "multiple" and AUTO_REASONING_FOR_MULTIPLE:
            force_reasoning = True
            if "多选题" not in reasoning_reasons:
                reasoning_reasons.append("多选题")
        
        # 3. 带图片题目自动启用思考模式
        if image_urls and AUTO_REASONING_FOR_IMAGES:
            force_reasoning = True
            if "图片题" not in reasoning_reasons:
                reasoning_reasons.append("图片题")
        
        if force_reasoning and reasoning_reasons:
            print(f"🧠 {' + '.join(reasoning_reasons)}自动启用深度思考模式")
        
        # 调用模型（计时）
        # 优先使用自定义模型，支持故障转移
        ai_start = time.time()
        
        type_models = custom_model_manager.get_available_model_ids_for_question(
            q_type,
            has_images=bool(image_urls)
        )
        
        reasoning = None
        raw_answer = None
        usage_info = None
        reasoning_used = False
        custom_model_id = None
        actual_provider = None
        model_name = None
        
        for model_id in type_models:
            model = custom_model_manager.get_model(model_id)
            if not model:
                continue

            logger.info(f"🎯 使用模型: {model_id}")
            print(f"🎯 使用模型: {model_id}")

            reasoning, raw_answer, usage_info, model_reasoning_used = _call_custom_model(
                model_id,
                prompt,
                image_urls,
                force_reasoning,
                image_items=image_items if image_items else None
            )

            if raw_answer:
                custom_model_id = model_id
                actual_provider = infer_provider_from_model(model_id, model)
                model_name = model.get('name', model_id)
                reasoning_used = model_reasoning_used
                break

            logger.warning(f"⚠️  模型 {model_id} 调用失败，尝试下一个模型...")
            print(f"⚠️  模型 {model_id} 调用失败，尝试下一个模型...")
        
        ai_time = time.time() - ai_start
        
        if not raw_answer:
            if not type_models:
                if image_urls:
                    error_message = "图片题未配置可用的多模态模型，请到模型管理页为图片题配置模型"
                else:
                    error_message = f"{q_type_name}未配置可用模型，请到模型管理页设置题型映射"
            else:
                error_message = "可用模型均调用失败，请检查模型配置或网络连接"
            print(f"❌ 答题失败: {error_message}")
            return jsonify({"success": False, "error": error_message}), 500
        
        # 提取token使用量
        prompt_tokens = 0
        completion_tokens = 0
        if usage_info:
            prompt_tokens = usage_info.get('prompt_tokens', 0)
            completion_tokens = usage_info.get('completion_tokens', 0)
        
        # 处理答案
        processed_answer = AnswerProcessor.process_answer(
            raw_answer,
            q_type,
            options,
            use_option_labels=use_option_labels
        )
        ocs_answer = AnswerProcessor.resolve_answer_for_ocs(
            processed_answer,
            raw_answer,
            q_type,
            options,
            use_option_labels=use_option_labels
        )
        
        # 计算总耗时
        total_time = time.time() - start_time
        
        # 控制台输出答案和耗时
        print(f"\n🤖 AI原始回答: {raw_answer}")
        print(f"✅ 处理后答案: {processed_answer}")
        if ocs_answer != processed_answer:
            print(f"🔁 OCS匹配答案: {ocs_answer}")
        print(f"⏱️  模型答题用时: {format_time(ai_time)}")
        print(f"⏱️  总处理用时: {format_time(total_time)}")
        print("="*80 + "\n")
        
        # 记录到CSV文件
        save_to_csv(
            question=question,
            options=options,
            q_type=q_type_name,
            raw_answer=raw_answer,
            reasoning=reasoning,
            processed_answer=processed_answer,
            ai_time=ai_time,
            total_time=total_time,
            model_name=model_name,
            reasoning_used=reasoning_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            provider=actual_provider
        )
        
        # 构建响应（OCS脚本格式：返回[题目, 答案, extra_data]）
        # extra_data格式：{ai: true, tags: [{text, title, color}]}
        # 注意：OCS脚本会在ai=true时自动添加"AI"标签（蓝色）
        # 所以我们只需要添加额外的标签来区分思考/非思考模式
        
        # 构建标签
        tags = []
        
        # 思考模式：添加"深度思考"标签（紫色），OCS会自动添加"AI"标签（蓝色）
        if reasoning_used:
            tags.append({
                "text": "深度思考",
                "title": "使用深度思考模式生成，答案更准确",
                "color": "purple"  # OCS支持的颜色：blue, green, red, yellow, gray, purple, orange
            })
            # 如果是多选题自动启用的思考模式
            if force_reasoning:
                tags.append({
                    "text": "自动思考",
                    "title": "多选题自动启用深度思考",
                    "color": "orange"
                })
        # 普通模式：不添加标签，OCS脚本会自动添加"AI"标签（蓝色）
        
        # 模型标签
        if custom_model_id:
            model = custom_model_manager.get_model(custom_model_id) or {}
            tags.append({
                "text": "内置预设" if model.get('is_builtin') else "自定义模型",
                "title": f"使用模型: {model_name}",
                "color": "green"
            })
        
        # OCS脚本期望的格式：[题目, 答案, extra_data]
        # ai=true 会让OCS自动添加"AI"标签
        # 计算总token数
        total_tokens = prompt_tokens + completion_tokens
        
        ocs_format = [
            question,
            ocs_answer,
            {
                "ai": True,  # OCS会自动添加"AI"标签
                "tags": tags,  # 我们添加的额外标签（深度思考、模型等）
                "model": model_name,
                "provider": actual_provider,
                "reasoning_used": reasoning_used,
                "ai_time": round(ai_time, 2),
                "total_time": round(total_time, 2),
                # Token使用量（从API响应中提取）
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                }
            }
        ]

        write_request_trace("response_ready", request_id, {
            "question_type": q_type,
            "question": question,
            "normalized_options": options,
            "image_items": image_items,
            "use_option_labels": use_option_labels,
            "raw_answer": raw_answer,
            "processed_answer": processed_answer,
            "ocs_format_answer": ocs_answer,
            "model_id": custom_model_id,
            "model_name": model_name,
            "provider": actual_provider,
            "reasoning_used": reasoning_used
        })
        
        # 返回兼容格式（同时支持OCS格式和原始格式）
        response_provider = actual_provider or ''
        
        return jsonify({
            "success": True,
            "question": question,
            "answer": processed_answer,
            "ocs_answer": ocs_answer,
            "type": q_type,
            "raw_answer": raw_answer,
            "model": model_name,
            "provider": response_provider,
            "reasoning_used": reasoning_used,
            "ai_time": round(ai_time, 2),
            "total_time": round(total_time, 2),
            # Token使用量（从API响应中提取）
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            },
            # OCS脚本直接使用的格式
            "ocs_format": ocs_format
        })
    
    except Exception as e:
        error_time = time.time() - start_time
        write_request_trace("request_error", request_id, {
            "error": str(e),
            "elapsed_seconds": round(error_time, 3)
        })
        print(f"\n❌ 错误: {str(e)}")
        print(f"⏱️  处理用时: {format_time(error_time)}")
        print("="*80 + "\n")
        logger.error(f"处理请求错误: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": f"服务器错误: {str(e)}"}), 500


# ==================== API 路由 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    runtime = custom_model_manager.get_runtime_summary()
    return jsonify({
        "status": "ok" if runtime.get('can_answer_any') else "error",
        "service": "OCS AI Answerer (Multi-Model)",
        "version": "3.1.0",
        "reasoning_enabled": ENABLE_REASONING,
        "api_configured": runtime.get('can_answer_any'),
        "model_count": runtime.get('model_count', 0),
        "enabled_model_count": runtime.get('enabled_model_count', 0),
        "ready_question_types": runtime.get('ready_question_types', []),
        "has_multimodal_model": runtime.get('has_multimodal_model', False),
        "init_error": runtime.get('init_error')
    })


@app.route('/api/config', methods=['GET'])
@require_auth
def get_config():
    """获取当前配置（需要认证）- 返回完整密钥"""
    runtime = custom_model_manager.get_runtime_summary()
    config = {
        # 思考模式配置
        "ENABLE_REASONING": str(ENABLE_REASONING).lower(),
        "REASONING_EFFORT": REASONING_EFFORT,
        "AUTO_REASONING_FOR_MULTIPLE": str(AUTO_REASONING_FOR_MULTIPLE).lower(),
        "AUTO_REASONING_FOR_IMAGES": str(AUTO_REASONING_FOR_IMAGES).lower(),
        
        # AI 参数配置
        "TEMPERATURE": str(TEMPERATURE),
        "MAX_TOKENS": str(MAX_TOKENS),
        "REASONING_MAX_TOKENS": str(REASONING_MAX_TOKENS),
        "TOP_P": str(TOP_P),

        # 网络配置
        "HTTP_PROXY": HTTP_PROXY,
        "HTTPS_PROXY": HTTPS_PROXY,
        "TIMEOUT": str(TIMEOUT),
        "MAX_RETRIES": str(MAX_RETRIES),
        
        # 系统配置
        "HOST": HOST,
        "PORT": str(PORT),
        "DEBUG": str(os.getenv('DEBUG', 'false')).lower(),
        "CSV_LOG_FILE": os.getenv('CSV_LOG_FILE', 'ocs_answers_log.csv'),
        "LOG_LEVEL": os.getenv('LOG_LEVEL', 'INFO'),
    }
    
    config["_runtime"] = {
        "model_count": runtime.get('model_count', 0),
        "enabled_model_count": runtime.get('enabled_model_count', 0),
        "ready_question_types": runtime.get('ready_question_types', []),
        "mapped_question_types": runtime.get('mapped_question_types', {}),
        "has_multimodal_model": runtime.get('has_multimodal_model', False),
        "can_answer_any": runtime.get('can_answer_any', False),
        "init_error": runtime.get('init_error')
    }
    
    return jsonify(config)


@app.route('/api/config', methods=['POST'])
@require_auth
def save_config():
    """保存配置到 .env 文件（需要认证）- 匹配修改而非覆盖"""
    try:
        config_data = request.get_json()
        if not config_data:
            return jsonify({"error": "无效的配置数据"}), 400

        config_data = {
            key: value for key, value in config_data.items()
            if key in CONFIG_EDITABLE_KEYS
        }

        is_valid, validation_error = validate_config_updates(config_data)
        if not is_valid:
            return jsonify({"error": validation_error}), 400

        # .env 文件路径
        env_file = os.path.join(os.path.dirname(__file__), '.env')
        
        # 读取现有的 .env 文件内容（逐行）
        lines = []
        if os.path.exists(env_file):
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        # 创建配置键到新值的映射
        updated_keys = set()
        
        # 逐行处理，匹配并修改
        new_lines = []
        for line in lines:
            stripped = line.strip()
            
            # 保留注释和空行
            if not stripped or stripped.startswith('#'):
                new_lines.append(line)
                continue
            
            # 解析配置行
            if '=' in stripped:
                key = stripped.split('=', 1)[0].strip()
                
                # 如果这个key在更新数据中，替换它
                if key in config_data:
                    value = config_data[key]
                    # 处理空值
                    if value == '' or value is None:
                        new_lines.append(f"{key}=\n")
                    else:
                        new_lines.append(f"{key}={value}\n")
                    updated_keys.add(key)
                else:
                    # 保留原有配置
                    new_lines.append(line)
            else:
                # 保留格式不正确的行
                new_lines.append(line)
        
        # 添加新的配置项（如果有）
        new_keys = set(config_data.keys()) - updated_keys
        if new_keys:
            new_lines.append("\n# 新增配置项\n")
            for key in sorted(new_keys):
                value = config_data[key]
                if value == '' or value is None:
                    new_lines.append(f"{key}=\n")
                else:
                    new_lines.append(f"{key}={value}\n")
        
        # 写入文件
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        # 检测哪些配置项需要重启才能生效（绑定监听端口 / Flask 启动参数）
        restart_keys = []
        current_runtime = {
            'HOST': str(HOST),
            'PORT': str(PORT),
            'DEBUG': str(DEBUG).lower(),
        }
        for key in CONFIG_RESTART_REQUIRED_KEYS:
            if key in config_data:
                new_value = str(config_data[key]).strip()
                if key == 'DEBUG':
                    new_value = new_value.lower()
                if new_value != current_runtime.get(key, ''):
                    restart_keys.append(key)

        # 将新配置同步到当前进程环境变量，并热重载运行时全局配置
        # 这样除 HOST/PORT/DEBUG 外的设置都无需重启脚本即可立即生效
        for key, value in config_data.items():
            os.environ[key] = '' if value is None else str(value)
        reload_runtime_config()

        restart_required = len(restart_keys) > 0
        if restart_required:
            note = f"以下配置需重启服务才能生效: {', '.join(restart_keys)}；其余配置已即时生效"
        else:
            note = "配置已即时生效，无需重启服务"

        logger.info(f"配置已保存到 {env_file}，更新了 {len(updated_keys)} 个配置项，新增了 {len(new_keys)} 个配置项；{note}")
        return jsonify({
            "success": True,
            "message": "配置已成功保存到 .env 文件",
            "file": env_file,
            "updated": len(updated_keys),
            "added": len(new_keys),
            "restart_required": restart_required,
            "restart_keys": restart_keys,
            "note": note
        })
        
    except Exception as e:
        logger.error(f"保存配置失败: {str(e)}")
        return jsonify({"error": f"保存配置失败: {str(e)}"}), 500


@app.route('/api/restart', methods=['POST'])
@require_auth
def restart_server():
    """重启服务器（需要认证）"""
    try:
        import sys
        import os
        import threading
        import subprocess
        
        def do_restart():
            """延迟重启以便响应返回"""
            import time
            time.sleep(1)  # 等待响应返回
            logger.info("正在重启服务器...")
            
            # 检测是否为 PyInstaller 打包环境
            if getattr(sys, 'frozen', False):
                # 打包后的 exe 环境
                executable = sys.executable  # exe 文件路径
                logger.info(f"检测到打包环境，重启 exe: {executable}")
                
                # 直接启动新的 exe 进程
                if os.name == 'nt':  # Windows
                    subprocess.Popen([executable], 
                                   creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:  # Linux/Mac
                    subprocess.Popen([executable])
                
                # 退出当前进程
                os._exit(0)
            else:
                # 普通 Python 脚本环境
                python = sys.executable
                script = os.path.abspath(__file__)
                logger.info(f"检测到脚本环境，重启: {python} {script}")
                
                if os.name == 'nt':  # Windows
                    subprocess.Popen([python, script], 
                                   creationflags=subprocess.CREATE_NEW_CONSOLE)
                    os._exit(0)
                else:  # Linux/Mac
                    os.execv(python, [python, script])
        
        # 在后台线程中执行重启
        threading.Thread(target=do_restart, daemon=True).start()
        
        return jsonify({
            "success": True,
            "message": "服务器将在 1 秒后重启"
        })
        
    except Exception as e:
        logger.error(f"重启服务器失败: {str(e)}")
        return jsonify({"error": f"重启失败: {str(e)}"}), 500


@app.route('/api/csv/stats', methods=['GET'])
def get_csv_stats():
    """获取CSV统计数据（支持筛选）"""
    csv_file = os.getenv('CSV_LOG_FILE', 'ocs_answers_log.csv')
    
    # 获取筛选参数
    search = request.args.get('search', '')
    question_type = request.args.get('type', '')
    reasoning = request.args.get('reasoning', '')
    date_filter = request.args.get('date', 'all')
    custom_date = request.args.get('custom_date', '')
    
    try:
        if not os.path.exists(csv_file):
            return jsonify({"error": "CSV文件不存在"}), 404
        
        # 读取并解析CSV
        import csv as csv_module
        stats = {
            'total': 0,
            'avgTime': 0,
            'reasoningCount': 0,
            'totalTime': 0,
            'totalCost': 0,
            'totalTokens': 0,
            'inputTokens': 0,
            'outputTokens': 0,
            'typeCounts': {},
            'timeRanges': {'0-2秒': 0, '2-5秒': 0, '5-10秒': 0, '10秒以上': 0},
            'reasoningCounts': {'思考模式': 0, '普通模式': 0},
            'dailyCounts': {}
        }
        
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv_module.DictReader(f)
            total_ai_time = 0
            
            for row in reader:
                # 应用筛选
                row_text = '|'.join(row.values()).lower()
                if search and search.lower() not in row_text:
                    continue
                if question_type and row.get('题型', '') != question_type:
                    continue
                if reasoning and row.get('思考模式', '') != reasoning:
                    continue
                # TODO: 日期筛选
                
                # 统计
                stats['total'] += 1
                
                # AI耗时
                ai_time = float(row.get('AI耗时(秒)', 0) or 0)
                total_ai_time += ai_time
                
                # 总耗时
                stats['totalTime'] += float(row.get('总耗时(秒)', 0) or 0)
                
                # 费用
                stats['totalCost'] += float(row.get('费用(元)', 0) or 0)
                
                # Token统计
                stats['totalTokens'] += int(row.get('总Token', 0) or 0)
                stats['inputTokens'] += int(row.get('输入Token', 0) or 0)
                stats['outputTokens'] += int(row.get('输出Token', 0) or 0)
                
                # 思考模式
                if row.get('思考模式', '') == '是':
                    stats['reasoningCount'] += 1
                    stats['reasoningCounts']['思考模式'] += 1
                else:
                    stats['reasoningCounts']['普通模式'] += 1
                
                # 题型分布
                q_type = row.get('题型', '未知')
                stats['typeCounts'][q_type] = stats['typeCounts'].get(q_type, 0) + 1
                
                # 耗时分布
                if ai_time <= 2:
                    stats['timeRanges']['0-2秒'] += 1
                elif ai_time <= 5:
                    stats['timeRanges']['2-5秒'] += 1
                elif ai_time <= 10:
                    stats['timeRanges']['5-10秒'] += 1
                else:
                    stats['timeRanges']['10秒以上'] += 1
                
                # 每日答题量
                timestamp = row.get('时间戳', '')
                if timestamp:
                    date = timestamp.split(' ')[0]
                    stats['dailyCounts'][date] = stats['dailyCounts'].get(date, 0) + 1
        
        # 计算平均值
        if stats['total'] > 0:
            stats['avgTime'] = total_ai_time / stats['total']
            stats['totalTime'] = stats['totalTime'] / 60  # 转换为分钟
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"获取统计数据失败: {str(e)}")
        return jsonify({"error": f"获取统计数据失败: {str(e)}"}), 500


@app.route('/api/csv', methods=['GET'])
def get_csv():
    """获取CSV日志文件（返回JSON格式，支持分页和筛选，时间倒序）"""
    csv_file = os.getenv('CSV_LOG_FILE', 'ocs_answers_log.csv')
    
    # 获取分页参数
    page = request.args.get('page', type=int)
    page_size = request.args.get('page_size', type=int)
    export_all = request.args.get('export', '') == 'true'  # 是否导出全部数据
    
    # 获取筛选参数
    search = request.args.get('search', '')
    question_type = request.args.get('type', '')
    reasoning = request.args.get('reasoning', '')
    date_filter = request.args.get('date', 'all')
    custom_date = request.args.get('custom_date', '')
    
    try:
        if not os.path.exists(csv_file):
            return jsonify({"error": "CSV文件不存在"}), 404
        
        # 使用DictReader解析CSV为字典列表
        all_data = []
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 应用筛选
                if search and search.lower() not in str(row).lower():
                    continue
                if question_type and row.get('题型', '') != question_type:
                    continue
                if reasoning:
                    if reasoning == '思考模式':
                        if row.get('思考模式', '否') == '否':
                            continue
                    elif reasoning == '普通模式':
                        if row.get('思考模式', '否') != '否':
                            continue
                
                # 日期筛选
                if date_filter != 'all':
                    timestamp = row.get('时间戳', '')
                    if timestamp:
                        try:
                            from datetime import datetime, timedelta
                            record_date = datetime.strptime(timestamp.split()[0], '%Y-%m-%d')
                            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                            
                            if date_filter == 'today':
                                if record_date.date() != today.date():
                                    continue
                            elif date_filter == 'week':
                                week_ago = today - timedelta(days=7)
                                if record_date < week_ago:
                                    continue
                            elif date_filter == 'month':
                                month_ago = today - timedelta(days=30)
                                if record_date < month_ago:
                                    continue
                            elif date_filter == 'custom' and custom_date:
                                date_range = custom_date.split(',')
                                if len(date_range) == 2:
                                    start_date = datetime.strptime(date_range[0], '%Y-%m-%d')
                                    end_date = datetime.strptime(date_range[1], '%Y-%m-%d')
                                    if not (start_date <= record_date <= end_date):
                                        continue
                        except:
                            pass
                
                all_data.append(row)
        
        # 按时间戳倒序排序（最新的在前面）
        all_data.sort(key=lambda x: x.get('时间戳', ''), reverse=True)
        
        total = len(all_data)
        
        # 如果是导出全部数据
        if export_all:
            return jsonify({
                "data": all_data,
                "total": total
            })
        
        # 如果没有分页参数，返回全部数据
        if page is None or page_size is None:
            return jsonify({
                "data": all_data,
                "total": total
            })
        
        # 分页处理
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        start = (page - 1) * page_size
        end = min(start + page_size, total)
        
        if start >= total or start < 0:
            paginated_data = []
        else:
            paginated_data = all_data[start:end]
        
        return jsonify({
            "data": paginated_data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        })
        
    except Exception as e:
        logger.error(f"读取CSV文件失败: {str(e)}")
        return jsonify({"error": f"读取CSV文件失败: {str(e)}"}), 500


@app.route('/api/csv/clear', methods=['POST'])
@require_auth
def clear_csv():
    """清空CSV日志文件（保留表头，需要认证）"""
    csv_file = os.getenv('CSV_LOG_FILE', 'ocs_answers_log.csv')
    
    try:
        # CSV表头
        headers = [
            '时间戳', '题型', '题目', '选项', '原始回答', '思考过程', 
            '处理后答案', 'AI耗时(秒)', '总耗时(秒)', '模型', '思考模式',
            '输入Token', '输出Token', '总Token', '费用(元)', '提供商'
        ]
        
        # 写入空文件（只保留表头）
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
        
        logger.info(f"CSV文件已清空: {csv_file}")
        return jsonify({
            "success": True,
            "message": "CSV文件已清空（保留表头）",
            "file": csv_file
        })
    except Exception as e:
        logger.error(f"清空CSV文件失败: {str(e)}")
        return jsonify({"success": False, "error": f"清空CSV文件失败: {str(e)}"}), 500


# ==================== 自定义模型管理API ====================

@app.route('/api/models', methods=['GET'])
@require_auth
def get_custom_models():
    """
    获取所有自定义模型列表（需要认证）
    
    查询参数:
        enabled_only: 是否只返回启用的模型（true/false）
    
    响应:
        {
            "success": true,
            "models": {
                "model_id": {...},
                ...
            },
            "question_type_models": {...}
        }
    """
    try:
        enabled_only = request.args.get('enabled_only', 'false').lower() == 'true'
        models = custom_model_manager.get_all_models(enabled_only=enabled_only)
        
        # 移除敏感信息（API密钥只返回部分）
        safe_models = {}
        for model_id, config in models.items():
            safe_config = config.copy()
            if 'api_key' in safe_config and safe_config['api_key']:
                # 只显示前4位和后4位
                key = safe_config['api_key']
                if len(key) > 8:
                    safe_config['api_key'] = key[:4] + '*' * (len(key) - 8) + key[-4:]
            safe_models[model_id] = safe_config
        
        return jsonify({
            "success": True,
            "models": safe_models,
            "question_type_models": custom_model_manager.question_type_models
        })
    except Exception as e:
        logger.error(f"获取自定义模型列表失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/models/<model_id>', methods=['GET'])
@require_auth
def get_custom_model(model_id):
    """获取单个自定义模型详情（需要认证）"""
    try:
        model = custom_model_manager.get_model(model_id)
        if not model:
            return jsonify({"success": False, "error": "模型不存在"}), 404

        return jsonify({
            "success": True,
            "model": model
        })
    except Exception as e:
        logger.error(f"获取模型详情失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/models', methods=['POST'])
@require_auth
def add_custom_model():
    """
    添加自定义模型（需要认证）
    
    请求体:
        {
            "model_id": "my_model",
            "name": "我的模型",
            "provider": "openai",
            "api_key": "sk-xxx",
            "base_url": "https://api.example.com/v1",
            "model_name": "gpt-4",
            "is_multimodal": false,
            "max_tokens": 2000,
            "temperature": 0.1,
            "top_p": 0.95,
            "supports_reasoning": false
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "无效的请求数据"}), 400
        
        model_id = data.get('model_id')
        if not model_id:
            return jsonify({"success": False, "error": "缺少model_id"}), 400
        
        # 移除model_id，因为它作为键使用
        model_config = {k: v for k, v in data.items() if k != 'model_id'}
        
        success, message = custom_model_manager.add_model(model_id, model_config)
        
        if success:
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"success": False, "error": message}), 400
    except Exception as e:
        logger.error(f"添加自定义模型失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/models/<model_id>', methods=['PUT'])
@require_auth
def update_custom_model(model_id):
    """
    更新自定义模型（需要认证）
    
    请求体: 同添加模型，但所有字段都是可选的
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "无效的请求数据"}), 400
        
        success, message = custom_model_manager.update_model(model_id, data)
        
        if success:
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"success": False, "error": message}), 400
    except Exception as e:
        logger.error(f"更新自定义模型失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/models/<model_id>', methods=['DELETE'])
@require_auth
def delete_custom_model(model_id):
    """删除自定义模型（需要认证）"""
    try:
        success, message = custom_model_manager.delete_model(model_id)
        
        if success:
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"success": False, "error": message}), 400
    except Exception as e:
        logger.error(f"删除自定义模型失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/models/question-types/<question_type>', methods=['GET'])
@require_auth
def get_question_type_models(question_type):
    """
    获取指定题型使用的模型列表（需要认证）
    
    路径参数:
        question_type: single/multiple/judgement/completion/image
    """
    try:
        model_ids = custom_model_manager.get_question_type_models(question_type)
        return jsonify({
            "success": True,
            "question_type": question_type,
            "model_ids": model_ids
        })
    except Exception as e:
        logger.error(f"获取题型模型列表失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/models/question-types/<question_type>', methods=['PUT'])
@require_auth
def set_question_type_models(question_type):
    """
    设置指定题型使用的模型列表和思考配置（需要认证）
    
    请求体:
        {
            "model_ids": ["model1", "model2", ...],
            "enable_reasoning": true/false  // 可选，是否启用思考模式
        }
    
    说明:
        - 列表按优先级排序，系统会优先使用靠前的模型
        - 对于图片题，会自动选择支持多模态的模型
        - enable_reasoning: 为该题型启用思考模式（原生思考模型会自动启用，无需配置）
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "无效的请求数据"}), 400
        
        model_ids = data.get('model_ids', [])
        if not isinstance(model_ids, list):
            return jsonify({"success": False, "error": "model_ids必须是数组"}), 400
        
        # 获取思考模式配置（可选）
        enable_reasoning = data.get('enable_reasoning', None)
        
        success, message = custom_model_manager.set_question_type_models(
            question_type, 
            model_ids,
            enable_reasoning
        )
        
        if success:
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"success": False, "error": message}), 400
    except Exception as e:
        logger.error(f"设置题型模型列表失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/models/test/<model_id>', methods=['POST'])
@require_auth
def test_custom_model(model_id):
    """
    测试自定义模型连接（需要认证）
    
    请求体:
        {
            "test_prompt": "你好"  // 可选，默认为简单测试
        }
    
    响应:
        {
            "success": true,
            "response": "模型返回内容",
            "latency": 1.23,
            "tokens": {...}
        }
    """
    try:
        model = custom_model_manager.get_model(model_id)
        if not model:
            return jsonify({"success": False, "error": "模型不存在"}), 404
        
        data = request.get_json() or {}
        test_prompt = data.get('test_prompt', '请用一句话介绍你自己')
        
        start_time = time.time()
        
        try:
            with create_http_client(timeout=min(TIMEOUT, 30.0), follow_redirects=True) as http_client:
                test_client = OpenAI(
                    api_key=model['api_key'],
                    base_url=model['base_url'],
                    http_client=http_client,
                    max_retries=1
                )

                if should_use_openai_responses(model):
                    response = test_client.responses.create(
                        model=model['model_name'],
                        input=[
                            {
                                "role": "system",
                                "content": [{"type": "input_text", "text": "你是一个有帮助的AI助手。"}]
                            },
                            {
                                "role": "user",
                                "content": [{"type": "input_text", "text": test_prompt}]
                            }
                        ],
                        max_output_tokens=100,
                        temperature=0.7
                    )
                    response_text = extract_text_from_responses_api(response)
                else:
                    response = test_client.chat.completions.create(
                        model=model['model_name'],
                        messages=[
                            {"role": "system", "content": "你是一个有帮助的AI助手。"},
                            {"role": "user", "content": test_prompt}
                        ],
                        max_tokens=100,
                        temperature=0.7
                    )
                    response_text = extract_text_from_chat_completions(response)
            
            latency = time.time() - start_time
            usage = extract_usage_from_response(response)
            
            result = {
                "success": True,
                "response": response_text,
                "latency": round(latency, 2),
                "tokens": {
                    "prompt": usage.get('prompt_tokens', 0),
                    "completion": usage.get('completion_tokens', 0),
                    "total": usage.get('total_tokens', 0)
                }
            }
            
            logger.info(f"✅ 模型测试成功: {model_id}, 延迟: {latency:.2f}秒")
            return jsonify(result)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ 模型测试失败: {model_id}, 错误: {error_msg}")
            return jsonify({
                "success": False,
                "error": f"连接测试失败: {error_msg}"
            }), 400
            
    except Exception as e:
        logger.error(f"测试模型失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== 安全认证API ====================

@app.route('/api/auth/verify', methods=['POST'])
def verify_auth():
    """验证API密钥是否有效"""
    try:
        data = request.get_json()
        api_key = data.get('api_key', '')
        
        if not api_key:
            return jsonify({"valid": False, "error": "缺少API密钥"}), 400
        
        # 验证密钥
        is_valid = security_manager.verify_key(api_key)
        
        if is_valid:
            return jsonify({"valid": True})
        else:
            return jsonify({"valid": False, "error": "密钥无效"}), 403
    except Exception as e:
        logger.error(f"验证密钥失败: {str(e)}")
        return jsonify({"valid": False, "error": str(e)}), 500


@app.route('/api/auth/update-key', methods=['POST'])
@require_auth
def update_secret_key():
    """更新访问密钥（需要旧密钥认证）"""
    try:
        data = request.get_json()
        old_key = data.get('old_key', '')
        new_key = data.get('new_key', '')
        
        if not old_key or not new_key:
            return jsonify({"success": False, "error": "缺少必要参数"}), 400
        
        # 更新密钥
        success, message = security_manager.update_key(old_key, new_key)
        
        if success:
            return jsonify({"success": True, "message": message})
        else:
            return jsonify({"success": False, "error": message}), 400
    except Exception as e:
        logger.error(f"更新密钥失败: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """获取认证状态（不需要密钥，用于检查是否启用了认证）"""
    return jsonify({
        "auth_enabled": True,
        "message": "此服务需要API密钥才能访问敏感接口"
    })


# ==================== Vue SPA 静态文件服务 ====================

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """提供Vue打包后的静态资源"""
    dist_dir = os.path.join(os.path.dirname(__file__), 'dist', 'assets')
    return send_from_directory(dist_dir, filename)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_spa(path):
    """
    服务 Vue SPA 应用
    - 如果请求的是 API 路径，跳过（由其他路由处理）
    - 如果请求有时间戳参数 (?t=...)，作为延迟测试
    - 否则返回 Vue 应用的 index.html
    """
    # API 路径已经被上面的路由处理，这里不应该被触发
    if path.startswith('api/'):
        return jsonify({"error": "API endpoint not found"}), 404
    
    # 延迟测试（向后兼容旧的 OCS 脚本）
    timestamp = request.args.get('t', None)
    if timestamp and request.method in ['HEAD', 'GET']:
        response = make_response('', 200)
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        response.headers['X-Service'] = 'OCS AI Answerer'
        response.headers['X-Version'] = '3.1.0'
        
        try:
            client_timestamp = int(timestamp) / 1000
            server_timestamp = time.time()
            latency = (server_timestamp - client_timestamp) * 1000
            response.headers['X-Latency'] = f"{latency:.2f}ms"
        except (ValueError, TypeError):
            pass
        
        if request.method == 'GET':
            response.set_data('OK')
        
        return response
    
    # 服务 Vue SPA
    dist_dir = os.path.join(os.path.dirname(__file__), 'dist')
    index_file = os.path.join(dist_dir, 'index.html')
    
    # 如果 dist 目录不存在，提示需要构建前端
    if not os.path.exists(dist_dir) or not os.path.exists(index_file):
        return jsonify({
            "error": "前端应用未构建",
            "message": "请先构建前端应用：cd frontend && npm install && npm run build",
            "note": "或者使用旧版HTML界面，访问 /config_legacy"
        }), 503
    
    # 返回 Vue 应用的 index.html
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        response = make_response(html_content)
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        return response
    except Exception as e:
        logger.error(f"加载Vue应用失败: {str(e)}")
        return jsonify({"error": f"加载前端应用失败: {str(e)}"}), 500


# ==================== 旧版HTML页面路由(向后兼容) ====================

@app.route('/config_legacy', methods=['GET'])
def config_panel_legacy():
    """配置管理面板 (旧版HTML)"""
    html_file = os.path.join(os.path.dirname(__file__), 'config_panel.html')
    
    try:
        if os.path.exists(html_file):
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            return response
        else:
            return jsonify({"error": "配置面板文件不存在"}), 404
    except Exception as e:
        logger.error(f"加载配置面板失败: {str(e)}")
        return jsonify({"error": f"加载配置面板失败: {str(e)}"}), 500


@app.route('/viewer_legacy', methods=['GET'])
def viewer_legacy():
    """答题记录可视化页面 (旧版HTML)"""
    html_file = os.path.join(os.path.dirname(__file__), 'ocs_answers_viewer.html')
    
    try:
        if os.path.exists(html_file):
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 修改HTML中的fetch路径，使其指向Flask API
            html_content = html_content.replace(
                "fetch('ocs_answers_log.csv')",
                "fetch('/api/csv')"
            )
            html_content = html_content.replace(
                'fetch("ocs_answers_log.csv")',
                'fetch("/api/csv")'
            )
            html_content = html_content.replace(
                '<script src="chart.js.min.js"></script>',
                '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>'
            )
            
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            return response
        else:
            return jsonify({"error": "可视化页面文件不存在"}), 404
    except Exception as e:
        logger.error(f"加载可视化页面失败: {str(e)}")
        return jsonify({"error": f"加载可视化页面失败: {str(e)}"}), 500


@app.route('/docs_legacy', methods=['GET'])
def api_docs_legacy():
    """API文档页面 (旧版HTML)"""
    html_file = os.path.join(os.path.dirname(__file__), 'api_docs.html')
    
    try:
        if os.path.exists(html_file):
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            return response
        else:
            return jsonify({"error": "API文档文件不存在"}), 404
    except Exception as e:
        logger.error(f"加载API文档失败: {str(e)}")
        return jsonify({"error": f"加载API文档失败: {str(e)}"}), 500


if __name__ == '__main__':
    runtime = custom_model_manager.get_runtime_summary()
    ready_types = "、".join(runtime.get('ready_question_types', [])) or "无"
    model_info = f"已配置模型 {runtime.get('model_count', 0)} 个 / 已启用 {runtime.get('enabled_model_count', 0)} 个"
    model_detail = f"可答题型: {ready_types}"
    
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║       OCS智能答题API服务 - 多模型支持版本 v3.0              ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  � Vue3 前端: http://{HOST}:{PORT}/                    
    ║  📊 数据可视化: http://{HOST}:{PORT}/viewer             
    ║  📖 API文档: http://{HOST}:{PORT}/docs                  
    ╠═══════════════════════════════════════════════════════════╣
    ║  接口地址: http://{HOST}:{PORT}/api/answer              
    ║  健康检查: http://{HOST}:{PORT}/api/health              
    ║  配置查询: http://{HOST}:{PORT}/api/config              
    ║  CSV数据: http://{HOST}:{PORT}/api/csv                  
    ║  延迟测试: http://{HOST}:{PORT}/?t=时间戳 (HEAD/GET)    
    ╠═══════════════════════════════════════════════════════════╣
    ║  当前模式: {model_info:<48s}║
    ║  {'  ' + model_detail if model_detail else '':<60s}║
    ║  思考模式: {'✅ 已启用' if ENABLE_REASONING else '❌ 未启用':<40s}║
    ║  多选题思考: {'✅ 自动启用' if AUTO_REASONING_FOR_MULTIPLE else '❌ 关闭':<38s}║
    ║  图片题思考: {'✅ 自动启用' if AUTO_REASONING_FOR_IMAGES else '❌ 关闭':<38s}║
    ║  支持题型: 单选、多选、判断、填空                        ║
    ╠═══════════════════════════════════════════════════════════╣
    ║  💡 旧版HTML: http://{HOST}:{PORT}/config_legacy         
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    if not runtime.get('can_answer_any'):
        print("\n" + "="*80)
        print("❌ 当前没有可用的答题模型")
        if runtime.get('init_error'):
            print(f"错误信息: {runtime.get('init_error')}")
        print("\n💡 解决方案:")
        print("   1. 打开 Web 模型管理页面")
        print("   2. 为内置预设或自定义模型填写 API 密钥")
        print("   3. 启用至少一个模型")
        print("   4. 为题型设置模型映射（图片题需要多模态模型）")
        print("="*80 + "\n")
    else:
        print("✅ 服务启动成功！\n")
        print("💡 当前状态:")
        print(f"   🔧 已配置模型: {runtime.get('model_count', 0)}")
        print(f"   ✅ 已启用模型: {runtime.get('enabled_model_count', 0)}")
        print(f"   📝 可答题型: {ready_types}")
        print(f"   🖼️  多模态模型: {'已配置' if runtime.get('has_multimodal_model') else '未配置'}\n")
    
    # 检查前端是否已构建
    dist_dir = os.path.join(os.path.dirname(__file__), 'dist')
    if not os.path.exists(dist_dir):
        print("⚠️  警告: 前端应用未构建")
        print("   访问 Web 界面需要先构建前端：")
        print("   执行: build_frontend.bat")
        print("   或访问旧版界面: http://{}:{}/config_legacy\n".format(HOST, PORT))
    
    app.run(host=HOST, port=PORT, debug=DEBUG)

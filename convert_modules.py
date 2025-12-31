#!/usr/bin/env python3
"""
代理软件模块转换脚本
支持 Loon、QX、Surge 模块之间的相互转换

功能特性：
- 支持跨平台转换（loon -> surge, qx -> loon 等）
- 支持自身类型转换（loon -> loon, qx -> qx 等），用于复制和标准化文件
- 自动创建目录结构
- 批量处理多个模块
- 支持自定义目标类型配置
- 支持 Surge 高级特性：pre-matching 和 extended-matching (sni/pm 参数)

使用方法：
1. 在 module_sources.json 中配置模块源
2. 可选择性指定 targets 数组来控制转换目标
3. 对于需要 sni/pm 参数的模块，设置 "advanced_matching": true
4. 运行脚本进行批量转换
"""

import json
import os
import re
import shutil
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

# 转换配置
CONVERSION_CONFIG = {
    "loon": {
        "type": "loon-plugin",
        "targets": {
            "surge": {"target": "surge-module", "ext": "sgmodule"},
            "shadowrocket": {"target": "shadowrocket-module", "ext": "sgmodule"}
        }
    },
    "qx": {
        "type": "qx-rewrite",
        "targets": {
            "surge": {"target": "surge-module", "ext": "sgmodule"},
            "shadowrocket": {"target": "shadowrocket-module", "ext": "sgmodule"}
        }
    },
    "surge": {
        "type": "surge-module",
        "targets": {
            "surge": {"target": "surge-module", "ext": "sgmodule"},
            "shadowrocket": {"target": "shadowrocket-module", "ext": "sgmodule"}
        }
    }
}


BASE_URL = "https://sc.sephiroth.club"
MODULE_DIR = "module"


def load_module_sources() -> Dict[str, List[Dict[str, Any]]]:
    """加载模块源配置"""
    with open("module_sources.json", "r", encoding="utf-8") as f:
        return json.load(f)


def extract_rules_for_matching(content: str) -> tuple[Set[str], Set[str]]:
    """
    从 Surge 模块的 [Rule] 部分提取规则值

    返回:
        tuple[Set[str], Set[str]]: (sni_values, pm_values)
        - sni_values: 用于 extended-matching (DOMAIN, DOMAIN-SUFFIX, DOMAIN-KEYWORD, URL-REGEX)
        - pm_values: 用于 pre-matching (DOMAIN, DOMAIN-SUFFIX, DOMAIN-KEYWORD, IP-CIDR, IP-CIDR6)
                     注意: pm 只能用于 REJECT 策略的规则
    """
    sni_values = set()  # extended-matching
    pm_values = set()   # pre-matching

    # 查找 [Rule] 部分（匹配到下一个 section 标记或文件末尾）
    # section 标记格式: [字母开头的名称]，排除 IPv6 地址中的方括号
    rule_match = re.search(r'\[Rule\]\s*(.*?)(?=\[[A-Za-z]|\Z)', content, re.DOTALL | re.IGNORECASE)
    if not rule_match:
        return sni_values, pm_values

    # 逐行处理规则
    for line in rule_match.group(1).split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        parts = line.split(',')
        if len(parts) < 2:
            continue

        rule_type = parts[0].strip().upper()
        value = parts[1].strip().strip('"')  # 去除引号

        # 获取策略，用于判断是否可以添加到 pm
        # 拒绝策略包括: REJECT, REJECT-DROP, REJECT-TINYGIF, REJECT-NO-DROP 等
        if rule_type in ('AND', 'OR', 'NOT'):
            # 复合规则的策略在括号组之后，通常是最后一个部分
            # 例如: AND,((DOMAIN-KEYWORD,adash),(DOMAIN-SUFFIX,example.com)),REJECT
            policy = parts[-1].strip().upper()
        else:
            # 普通规则格式: DOMAIN,example.com,REJECT 或 IP-CIDR,1.2.3.4/24,REJECT-DROP,no-resolve
            policy = parts[2].strip().upper() if len(parts) >= 3 else ""
        is_reject = policy.startswith("REJECT")

        # DOMAIN, DOMAIN-SUFFIX, DOMAIN-KEYWORD -> sni, pm(仅REJECT)
        if rule_type in ('DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD'):
            sni_values.add(value)
            if is_reject:
                pm_values.add(value)

        # IP-CIDR, IP-CIDR6 -> pm only (仅REJECT)
        elif rule_type in ('IP-CIDR', 'IP-CIDR6'):
            if is_reject:
                pm_values.add(value)

        # URL-REGEX -> sni only
        elif rule_type == 'URL-REGEX':
            sni_values.add(value)

        # AND/OR 复合规则 - 提取嵌套值
        elif rule_type in ('AND', 'OR','NOT'):
            _extract_composite_values(line, sni_values, pm_values, is_reject)

    return sni_values, pm_values


def _extract_composite_values(line: str, sni_values: Set[str], pm_values: Set[str], is_reject: bool = False):
    """
    从 AND/OR 复合规则中提取值

    Args:
        line: 规则行
        sni_values: sni 值集合
        pm_values: pm 值集合
        is_reject: 是否为 REJECT 策略，只有 REJECT 策略才能添加到 pm
    """
    # DOMAIN, DOMAIN-SUFFIX, DOMAIN-KEYWORD -> sni, pm(仅REJECT)
    for m in re.finditer(r'\((?:DOMAIN|DOMAIN-SUFFIX|DOMAIN-KEYWORD),([^,)]+)', line, re.IGNORECASE):
        value = m.group(1).strip()
        sni_values.add(value)
        if is_reject:
            pm_values.add(value)

    # IP-CIDR, IP-CIDR6 -> pm only (仅REJECT)
    for m in re.finditer(r'\(IP-CIDR6?,([^,)]+)', line, re.IGNORECASE):
        if is_reject:
            pm_values.add(m.group(1).strip())

    # URL-REGEX -> sni only (值在引号内)
    for m in re.finditer(r'\(URL-REGEX,"([^"]+)"', line, re.IGNORECASE):
        sni_values.add(m.group(1).strip())


def fetch_content(url: str) -> Optional[str]:
    """获取URL内容"""
    try:
        with urllib.request.urlopen(url) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"获取内容失败 {url}: {e}")
        return None


def create_conversion_url(source_url: str, module_name: str, source_type: str, target_type: str,
                          desc: str = None, sni_domains: str = None, pm_domains: str = None) -> str:
    """
    创建转换URL

    Args:
        source_url: 源模块URL
        module_name: 模块名称
        source_type: 源类型 (loon/qx/surge)
        target_type: 目标类型 (surge/shadowrocket)
        desc: 模块描述
        sni_domains: SNI域名列表，用+连接
        pm_domains: pre-matching域名列表，用+连接
    """
    config = CONVERSION_CONFIG[source_type]
    target_config = config["targets"][target_type]

    # 构建转换URL
    filename = f"{module_name}.{target_config['ext']}"

    # 构建基础URL
    base_conversion_url = f"{BASE_URL}/file/_start_/{source_url}/_end_/{filename}"

    # 构建查询参数
    params = {
        'type': config['type'],
        'target': target_config['target'],
        'del': 'true',
        'jqEnabled': 'true',
        'category': 'Lang'
    }

    # 如果有desc参数，添加到参数中
    if desc:
        params['n'] = desc

    # 添加 sni 和 pm 参数（用于 Surge 高级特性）
    if sni_domains:
        params['sni'] = sni_domains
    if pm_domains:
        params['pm'] = pm_domains

    # 使用urlencode来正确编码查询参数
    query_string = urllib.parse.urlencode(params, encoding='utf-8')
    conversion_url = f"{base_conversion_url}?{query_string}"

    return conversion_url


def get_advanced_matching_values(source_url: str, module_name: str, source_type: str) -> tuple[Optional[str], Optional[str]]:
    """
    获取用于 sni/pm 参数的规则值列表

    流程：
    1. 先获取基础转换后的 Surge 模块内容
    2. 解析 [Rule] 部分提取规则值
    3. 返回用 + 连接的字符串 (sni_str, pm_str)

    规则分类：
    - sni (extended-matching): DOMAIN, DOMAIN-SUFFIX, DOMAIN-KEYWORD, URL-REGEX
    - pm (pre-matching): DOMAIN, DOMAIN-SUFFIX, DOMAIN-KEYWORD, IP-CIDR, IP-CIDR6
    """
    # 先创建一个不带 sni/pm 的基础转换URL
    basic_url = create_conversion_url(source_url, module_name, source_type, "surge")

    print(f"  获取模块内容以提取规则...")
    content = fetch_content(basic_url)
    if not content:
        return None, None

    sni_values, pm_values = extract_rules_for_matching(content)

    if not sni_values and not pm_values:
        print(f"  未找到匹配规则")
        return None, None

    # 用 + 连接值
    sni_str = '+'.join(sorted(sni_values)) if sni_values else None
    pm_str = '+'.join(sorted(pm_values)) if pm_values else None

    print(f"  提取到 {len(sni_values)} 个 sni 规则, {len(pm_values)} 个 pm 规则")
    return sni_str, pm_str


def download_file(url: str, filepath: str) -> bool:
    """下载文件"""
    try:
        print(f"正在下载: {url}")
        with urllib.request.urlopen(url) as response:
            content = response.read()
        
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, "wb") as f:
            f.write(content)
        
        print(f"下载完成: {filepath}")
        return True
    except Exception as e:
        print(f"下载失败 {url}: {e}")
        return False


def clean_module_directories():
    """清理现有的模块目录"""
    module_path = Path(MODULE_DIR)
    if module_path.exists():
        print("清理现有模块目录...")
        shutil.rmtree(module_path)
    
    # 创建新的目录结构
    #for target_type in ["surge", "loon", "qx", "stash", "shadowrocket"]:
    for target_type in ["surge","shadowrocket"]:
        target_dir = module_path / target_type
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"创建目录: {target_dir}")

def check_base_url_accessible() -> bool:
    """检查BASE_URL是否可访问"""
    import urllib.request
    import urllib.error
    import socket

    try:
        # 尝试访问BASE_URL，设置超时
        req = urllib.request.Request(BASE_URL, method='HEAD')
        # 设置超时时间为5秒
        with urllib.request.urlopen(req, timeout=5) as response:
            # 只要没有异常抛出，就认为可访问
            status = response.status
            print(f"BASE_URL ({BASE_URL}) 可访问，状态码: {status}")
            return True
    except urllib.error.HTTPError as e:
        # HTTP错误（如404、500）表示服务器可访问，只是返回了错误状态
        print(f"BASE_URL ({BASE_URL}) 可访问，但返回错误状态码: {e.code} {e.reason}")
        return True
    except urllib.error.URLError as e:
        # 其他URL错误（连接拒绝、DNS解析失败等）表示不可访问
        print(f"BASE_URL ({BASE_URL}) 无法访问: {e}")
        return False
    except socket.timeout:
        print(f"BASE_URL ({BASE_URL}) 连接超时")
        return False
    except Exception as e:
        print(f"BASE_URL ({BASE_URL}) 检查时发生未知错误: {e}")
        return False


def convert_modules():
    """执行模块转换"""
    print("开始模块转换...")

    # 检查BASE_URL是否可访问
    if not check_base_url_accessible():
        print("错误: BASE_URL无法访问，跳过模块转换以避免数据丢失。")
        print("请检查网络连接或BASE_URL配置。")
        return

    # 清理并创建目录
    clean_module_directories()

    # 加载模块源配置
    sources = load_module_sources()

    total_conversions = 0
    successful_conversions = 0

    for source_type, modules in sources.items():
        print(f"\n处理 {source_type.upper()} 模块...")

        for module in modules:
            module_name = module["name"]
            source_url = module["url"]
            desc = module.get("desc")  # 获取desc字段，如果不存在则为None

            # 如果没有配置targets，则使用默认的所有可用目标类型（包括自身）
            if "targets" in module and module["targets"]:
                targets = module["targets"]
            else:
                # 获取该源类型的所有可用目标类型（包括自身）
                all_targets = list(CONVERSION_CONFIG[source_type]["targets"].keys())
                targets = all_targets
                print(f"  未配置targets，使用默认目标: {', '.join(targets)}")

            print(f"\n转换模块: {module_name}")
            print(f"源地址: {source_url}")

            # 检查目标是否包含 surge，如果包含则需要获取高级匹配特性的值
            sni_str = None
            pm_str = None
            needs_surge = "surge" in targets and "surge" in CONVERSION_CONFIG[source_type]["targets"]

            if needs_surge:
                print(f"  启用高级匹配特性 (pre-matching/extended-matching)")
                sni_str, pm_str = get_advanced_matching_values(source_url, module_name, source_type)

            for target_type in targets:
                # 检查目标类型是否在转换配置中
                if target_type not in CONVERSION_CONFIG[source_type]["targets"]:
                    print(f"  跳过 {target_type.upper()}: 不支持从 {source_type.upper()} 转换")
                    continue

                total_conversions += 1

                # 确定保存路径 - 使用正确的文件扩展名
                target_config = CONVERSION_CONFIG[source_type]["targets"][target_type]
                filename = f"{module_name}.{target_config['ext']}"
                filepath = os.path.join(MODULE_DIR, target_type, filename)

                # 创建转换URL
                # 只有 surge 目标类型才使用 sni/pm 参数
                if target_type == "surge" and (sni_str or pm_str):
                    conversion_url = create_conversion_url(
                        source_url, module_name, source_type, target_type, desc,
                        sni_domains=sni_str, pm_domains=pm_str
                    )
                else:
                    conversion_url = create_conversion_url(source_url, module_name, source_type, target_type, desc)

                print(f"  转换为 {target_type.upper()}: {conversion_url}")

                # 下载转换后的文件
                if download_file(conversion_url, filepath):
                    successful_conversions += 1
                    print(f"  保存到: {filepath}")
                else:
                    print(f"  转换失败: {target_type}")
    
    print(f"\n转换完成!")
    print(f"总转换数: {total_conversions}")
    print(f"成功转换: {successful_conversions}")
    print(f"失败转换: {total_conversions - successful_conversions}")


if __name__ == "__main__":
    convert_modules()

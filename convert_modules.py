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

使用方法：
1. 在 module_sources.json 中配置模块源
2. 可选择性指定 targets 数组来控制转换目标
3. 运行脚本进行批量转换
"""

import json
import os
import shutil
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any

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


def create_conversion_url(source_url: str, module_name: str, source_type: str, target_type: str, desc: str = None) -> str:
    """创建转换URL"""
    config = CONVERSION_CONFIG[source_type]
    target_config = config["targets"][target_type]

    # 构建转换URL
    filename = f"{module_name}.{target_config['ext']}"

    # 对source_url进行URL编码，处理中文字符
    # encoded_source_url = urllib.parse.quote(source_url, safe=':/?#[]@!$&\'()*+,;=')

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
    
    # 使用urlencode来正确编码查询参数
    query_string = urllib.parse.urlencode(params, encoding='utf-8')
    conversion_url = f"{base_conversion_url}?{query_string}"

    return conversion_url


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


def convert_modules():
    """执行模块转换"""
    print("开始模块转换...")

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
                conversion_url = create_conversion_url(source_url, module_name, source_type, target_type, desc)

                # 如果是自身类型转换，显示特殊信息
                # if source_type == target_type:
                #     print(f"  复制原始文件到 {target_type.upper()}: {conversion_url}")
                # else:
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

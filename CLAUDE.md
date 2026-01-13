# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个代理软件规则和模块管理工具集，主要功能包括：
- 为多种代理软件（Clash、Surge、Loon、Quantumult X、Shadowrocket、Stash、sing-box、mihomo等）提供规则文件
- 提供模块转换工具，支持不同代理软件模块之间的相互转换
- 管理GeoIP数据库文件
- 通过自动化工作流定期更新规则和模块

## 核心架构

### 目录结构
```
/
├── .github/workflows/          # GitHub Actions工作流
│   ├── Build.yml              # 主构建工作流（每天0:05和12:05执行）
│   ├── convert-modules.yml    # 模块转换工作流（每天凌晨2点执行）
│   └── ClearCommits.yml       # 清理提交历史
├── Clash/                     # Clash配置
│   ├── Rules/                # 规则文件（.list格式）
│   └── clash.yaml            # Clash主配置文件
├── Surge/                     # Surge配置
│   ├── Rules/                # 规则文件
│   └── Custom/               # 自定义配置
├── Loon/                      # Loon配置
├── QuantumultX/               # Quantumult X配置
├── Shadowrocket/              # Shadowrocket配置
├── Stash/                     # Stash配置
├── sing-box/                  # sing-box配置
├── mihomo/                    # mihomo配置
├── Egern/                     # Egern配置（.yaml格式）
├── GeoIP/                     # GeoIP数据库文件（.mmdb格式）
├── module/                    # 代理软件模块
│   ├── surge/                # Surge模块（.sgmodule）
│   └── shadowrocket/         # Shadowrocket模块
├── convert_modules.py         # 模块转换主脚本
├── module_sources.json        # 模块源配置
└── README.md                  # 项目说明（含免责声明）
```

### 自动化工作流

#### 1. 主构建工作流（Build.yml）
- **触发时机**: 每天0:05和12:05（UTC时间）
- **主要功能**:
  - 下载并合并广告过滤规则
  - 下载各类应用规则（Apple、AI、社交媒体、流媒体等）
  - 格式化规则文件（添加DOMAIN前缀、排序、去重）
  - 为不同代理软件生成适配的规则格式
  - 自动提交更新

#### 2. 模块转换工作流（convert-modules.yml）
- **触发时机**: 每天凌晨2点（UTC时间）
- **主要功能**:
  - 运行 `convert_modules.py` 脚本
  - 将Loon、QX、Surge模块相互转换
  - 支持Surge高级特性（pre-matching和extended-matching）
  - 自动提交转换后的模块

### 核心脚本

#### `convert_modules.py`
- **功能**: 代理软件模块转换脚本
- **支持转换**: Loon ↔ Surge ↔ Quantumult X ↔ Shadowrocket
- **高级特性**: 支持Surge的pre-matching和extended-matching
- **配置**: 使用 `module_sources.json` 定义模块源

#### `module_sources.json`
- **格式**: JSON配置文件
- **结构**: 按源类型（loon/qx/surge）分组定义模块
- **字段**:
  - `name`: 模块名称
  - `url`: 源URL
  - `desc`: 模块描述（可选）
  - `targets`: 目标类型数组（可选）
  - `advanced_matching`: 是否启用高级匹配（可选）

### 规则分类系统

规则按功能分类，主要包括：
- **广告过滤规则**: `Ads_*` 前缀
- **应用特定规则**: `Bilibili`、`TikTok`、`Steam` 等
- **地区规则**: `ChinaIP`、`ChinaDomain`、`ChinaASN`
- **服务规则**: `AppleMedia`、`OpenAI`、`Google` 等
- **自定义规则**: `Custom/` 目录下的规则

### 开发命令

#### 本地运行构建脚本
```bash
# 手动运行构建流程（模拟GitHub Actions）
./.github/workflows/Build.yml中的bash脚本部分
```

#### 运行模块转换
```bash
# 安装Python依赖（如果需要）
python3 -m pip install --upgrade pip

# 运行模块转换脚本
python3 convert_modules.py
```

#### 检查规则格式
```bash
# 检查规则文件格式
for file in Ruleset/*.list; do
  echo "检查: $file"
  head -5 "$file"
done
```

### 重要注意事项

1. **免责声明**: 项目包含详细的免责声明，所有代码仅用于资源共享和学习研究
2. **自动化提交**: 工作流会自动检测文件变化并提交，无需手动操作
3. **格式转换**: 不同代理软件使用不同的规则格式，构建脚本会自动转换
4. **模块转换**: 模块转换依赖于外部服务（sc.sephiroth.club）
5. **GeoIP数据库**: 定期从上游源更新中国和全球IP数据库

### 文件格式说明

- **.list文件**: 标准规则文件格式，包含DOMAIN、IP-CIDR等规则
- **.yaml文件**: Egern代理软件使用的规则格式
- **.json文件**: sing-box代理软件使用的规则格式
- **.sgmodule文件**: Surge/Shadowrocket模块文件
- **.mmdb文件**: GeoIP数据库文件（MaxMind DB格式）

### 维护要点

1. **规则更新**: 修改 `Build.yml` 中的URL列表来更新规则源
2. **模块源管理**: 编辑 `module_sources.json` 来添加/删除模块
3. **格式适配**: 不同代理软件的规则处理逻辑在构建脚本的不同部分
4. **错误处理**: 构建脚本包含错误检查和重试机制
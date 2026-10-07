# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个代理软件规则和模块管理工具集，主要功能包括：
- 为多种代理软件（Clash、Surge、Loon、Quantumult X、Shadowrocket、Stash、sing-box、mihomo等）提供规则文件
- 模块转换工具已迁移到 https://github.com/mlang233/ProxyModules
- 通过自动化工作流定期更新规则；旧模块目录作为兼容快照保留

## 核心架构

### 目录结构
```
/
├── .github/workflows/          # GitHub Actions工作流
│   ├── Build.yml              # 主构建工作流（每天0:05和12:05执行）
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
├── module/                    # 模块迁移前快照，不再自动更新
│   ├── surge/                # Surge模块（.sgmodule）
│   ├── shadowrocket/         # Shadowrocket模块
│   └── stash/                # Stash模块
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

### 模块功能迁移

模块转换脚本、源配置与更新工作流已独立到 [ProxyModules](https://github.com/mlang233/ProxyModules)。本仓库不再运行转换或管理模块源。

- `module/` 保留旧下载地址的最后一份快照，不应在此添加或更新模块。
- 添加模块、修改转换逻辑或修复转换工作流，应在新仓库中进行。
- 新模块地址使用 `ProxyModules/main/module/`；规则文件地址仍使用本仓库。

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
4. **模块迁移**: 模块转换在 ProxyModules 仓库维护，旧模块文件保留为兼容快照
### 文件格式说明

- **.list文件**: 标准规则文件格式，包含DOMAIN、IP-CIDR等规则
- **.yaml文件**: Egern代理软件使用的规则格式
- **.json文件**: sing-box代理软件使用的规则格式
- **.sgmodule文件**: Surge/Shadowrocket模块文件

### 维护要点

1. **规则更新**: 修改 `Build.yml` 中的URL列表来更新规则源
2. **模块源管理**: 在 ProxyModules 仓库的 `module_sources.json` 中添加/删除模块
3. **格式适配**: 不同代理软件的规则处理逻辑在构建脚本的不同部分
4. **错误处理**: 构建脚本包含错误检查和重试机制

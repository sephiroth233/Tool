# Fake-IP Sub-Store 模板

这套文件从当前 `config.fakeip.json` 派生，用于通过 Sub-Store 把订阅节点动态注入 sing-box 配置。

## 文件

- `sing-box-fakeip-template.json`：Fake-IP 配置模板，保留 DNS、入站、路由、规则集、Clash API 和缓存设置，不包含任何节点或节点凭据。
- `sing-box-fakeip.js`：Sub-Store 脚本，读取模板和指定订阅/集合，生成可由 sing-box 使用的完整配置。

模板文件本身不是可直接启动的完整 sing-box 配置；必须先由脚本注入节点和策略组。

## Sub-Store 参数

脚本使用与 `sephiroth233/Tool/template/sing-box.js` 相同的参数形式：

- `name`：Sub-Store 中订阅或集合的名称，必填。
- `type`：传入 `1` 或包含 `col` 的值时将 `name` 作为集合处理；否则作为单个订阅处理。
- `$files[0]`：必须是 `sing-box-fakeip-template.json` 的内容。

示例参数：

```text
name=我的节点&type=subscription
```

若使用集合：

```text
name=我的节点集合&type=collection
```

具体脚本和文件的绑定方式取决于 Sub-Store 客户端或服务端版本，但生成逻辑必须同时获得本模板文件、脚本和上述参数。

## 更新订阅链接

订阅 URL 不写入模板。链接发生变化时，在 Sub-Store 中修改 `name` 对应订阅的源 URL，然后重新生成配置即可；只要订阅名称不变，脚本参数和模板都不需要修改。

如果不使用 Sub-Store，也可以继续使用本目录上一级的本地更新脚本：

```sh
SUBSCRIPTION_URL='新的订阅链接' ../update-fakeip.sh
```

## 动态生成行为

- 完整保留转换器生成的每一个节点，不按协议类型过滤，Snell 也会保留。
- 检测重复 tag 和与策略组重名的 tag；发现冲突时中止生成，不静默删除节点。
- 根据节点 tag 动态建立美国、香港、台湾、日本、韩国、新加坡地区组；没有对应节点的地区组不会生成。
- `全部节点` 和各地区组中的具体节点严格保持订阅转换结果的原始顺序，只进行地区筛选，不做重新排序。
- 美国组使用 `tolerance: 500`，其他地区组使用 `tolerance: 50`。
- 地区 `urltest` 不设置 `interrupt_exist_connections`，使用默认值 `false`。
- `全部节点`、`Final`、`Apple`、`Github`、`Telegram`、`YouTube`、`AI`、`Linuxdo`、`Emby` 使用 `selector`，并设置 `interrupt_exist_connections: true`。
- 服务器地址是域名且订阅未指定解析器时，补充 `domain_resolver: dns-cn`；订阅已有的解析器不会被覆盖。
- 已知国内域名直接使用 `dns-cn`，并按 `ChinaDomain` 规则直连；其余 A/AAAA 查询先通过 `evaluate` 检查 `dns-cn` 响应，命中 `ChinaIP` 时返回真实 IP，并按 `ChinaIP` 规则直连，否则返回 Fake-IP。DNS 判断与路由保持一致，避免国内 CDN 因 IP 规则更新滞后而落入 `Final`。

## 安全性

模板不包含当前订阅的服务器地址、端口、密码、密钥或 UUID，可以安全地作为模板单独保存。脚本生成的最终配置会包含订阅凭据，应按敏感文件处理。

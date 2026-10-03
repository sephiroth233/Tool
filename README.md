# Tool

## 模块下载

本仓库公开发布各客户端的模块、参数适配脚本和附加规则。源配置与转换器由独立的私有仓库维护，计划每天北京时间 10:00 下载上游源文件、转换并同步到本仓库。规则文件继续在本仓库维护。

模块下载地址：

```text
https://raw.githubusercontent.com/sephiroth233/Tool/master/module/surge/<模块名>.sgmodule
https://raw.githubusercontent.com/sephiroth233/Tool/master/module/shadowrocket/<模块名>.sgmodule
https://raw.githubusercontent.com/sephiroth233/Tool/master/module/stash/<模块名>.stoverride
```

此前使用独立转换仓库下载地址的用户，请切换到以上地址。`module/` 是自动生成目录，其中的模块、`scripts/` 和 `rules/` 会一起更新；请勿直接修改生成文件。

Stash 参数目前使用生成时确定的值；Surge 和小火箭模块保留参数声明。哔哩哔哩 Surge 模块的附加代理规则需在主配置中引用，并将末尾策略改成实际使用的代理组：

```text
RULE-SET,https://raw.githubusercontent.com/sephiroth233/Tool/master/module/rules/Bilibili_remove_ads-proxy.list,你的代理组
```

> [!Caution]
> 禁止任何形式的转载或发布至国内平台

> [!WARNING]
> 禁止 FORK

## 免责申明

> [!IMPORTANT]
> 任何以任何方式查看此项目的人或直接或间接使用该项目的使用者都应仔细阅读此声明。
>
> 保留随时更改或补充此免责声明的权利。
>
> 一旦使用并复制了该项目的任何文件，则视为您已接受此免责声明.

- 本项目涉及的脚本仅用于资源共享和学习研究，不能保证其合法性，准确性，完整性和有效性，请根据情况自行判断.

- 间接使用该项目的任何用户，包括但不限于建立VPS或在某些行为违反国家/地区法律或相关法规的情况下进行传播, 本项目对于由此引起的任何隐私泄漏或其他后果概不负责.

- 请勿将本项目的任何内容用于商业或非法目的，否则后果自负.

- 如果任何单位或个人认为该项目的脚本可能涉嫌侵犯其权利，则应及时通知并提供身份证明，所有权证明，我们将在收到认证文件后删除相关脚本.

- 对任何脚本问题概不负责，包括但不限于由任何脚本错误导致的任何损失或损害.

- 您必须在下载后的24小时内从计算机或手机中完全删除以上内容.


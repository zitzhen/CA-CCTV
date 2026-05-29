# CA-CCTV

> 📺 像 CCTV 摄像头一样监控证书颁发机构。

CA-CCTV 会持续监控证书透明度（Certificate Transparency，CT）日志，并在你的域名有新的 TLS 证书签发时发出提醒。

由 GitHub Actions、crt.sh 和邮件通知驱动。

## 功能

* 🔍 监控一个或多个域名
* 📜 查询公开的证书透明度日志
* 🚨 对新签发的证书发送邮件通知
* 💾 持久化跟踪证书状态
* ⚡ 使用 GitHub Actions 实现零服务器部署
* 🆓 完全可运行在 GitHub 免费计划中

---

## 为什么需要 CA-CCTV？

意外的证书签发可能意味着：

* 自动化配置错误
* 被遗忘的基础设施
* 第三方服务活动
* CA 验证流程被破坏
* 未经授权的证书签发

CA-CCTV 就像证书颁发机构的 CCTV 摄像头，帮助你尽早发现证书相关活动。

---

## 快速开始

### 1. 使用此模板

点击：

```text
Use this template
↓
Create a new repository
```

从此模板创建你自己的仓库。

---

### 2. 配置要监控的域名

编辑 `domains.txt`。

示例：

```text
# One domain per line

example.com
example.org
subdomain.example.net
```

以 `#` 开头的注释和空行会被忽略。

---

### 3. 配置仓库密钥

进入：

```text
Repository
→ Settings
→ Secrets and variables
→ Actions
```

创建以下仓库密钥：

| Secret        | 说明                         |
| ------------- | ---------------------------- |
| SMTP_HOST     | SMTP 服务器主机名            |
| SMTP_PORT     | SMTP 服务器端口              |
| SMTP_USER     | SMTP 用户名                  |
| SMTP_PASSWORD | SMTP 密码 / 应用专用密码     |
| MAIL_TO       | 通知接收人                   |
| MAIL_FROM     | 发件人地址（可选）           |

示例：

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=xxxxxxxxxxxxxxxx
MAIL_TO=you@example.com
MAIL_FROM=CA-CCTV <your@email.com>
```

> 大多数服务商要求使用应用专用密码，而不是你的普通账户密码。

---

### 4. 启用 GitHub Actions

进入：

```text
Repository
→ Actions
```

如果 GitHub 请求授权：

```text
Enable workflows
```

确保已为该仓库启用 Actions。

---

### 5. 初始化状态

手动运行一次工作流：

```text
Actions
→ CA-CCTV
→ Run workflow
→ init = true
```

这会将当前已知的证书导入本地状态数据库。

初始化期间不会发送通知邮件。

---

### 6. 完成

CA-CCTV 会按计划自动运行。

每当 CT 日志中出现新证书时，都会发送一封邮件提醒。

---

## 工作原理

```text
GitHub Actions
        │
        ▼
     crt.sh
        │
        ▼
 证书透明度日志
        │
        ▼
 与上一次状态进行比对
        │
        ▼
 发现新证书？
        │
   ┌────┴────┐
   │         │
  否         是
   │         │
   ▼         ▼
 结束     发送邮件
```

---

## 项目结构

```text
.
├── domains.txt
├── ct_watch.py
├── email.py
├── .ct-state/
│   └── *.json
└── .github/
    └── workflows/
        └── ca-cctv.yml
```

---

## 限制

* 依赖公开 CT 日志的可见性。
* 检测速度取决于 CT 日志发布和 crt.sh 索引速度。
* 邮件送达取决于你的 SMTP 服务商。

---

## 许可证

Apache License 2.0

---

由 ☕、Python 和过于旺盛的好奇心制作。

# 防止提交敏感信息指南

本指南用于减少将密钥、口令、令牌等敏感信息提交到 Git 仓库的风险。

## 1. 什么是敏感信息

以下内容禁止提交到仓库：

- 各类密钥与令牌：`API Key`、`Access Token`、`JWT`、`OAuth Client Secret`
- 账号密码：数据库密码、Redis 密码、MinIO 密码、第三方平台账号密码
- 私钥与证书：`*.pem`、`*.p12`、`*.key`、`-----BEGIN PRIVATE KEY-----`
- 生产环境配置：生产数据库连接串、内部服务地址、云账号信息
- 个人隐私数据：手机号、身份证号、邮箱列表、客户数据导出文件

## 2. 开发与配置规则

- 不要提交本地环境文件：`.env`、`.env.local`、`.env.*.local`
- 只提交模板文件：使用 `.env.example`，真实值用占位符
- 真实密钥只通过环境变量注入，不写死在代码中
- CI/CD 使用平台 Secret（如 GitHub Actions Secrets），不要写入 workflow 明文
- 测试数据使用脱敏数据，不使用真实用户数据

## 3. 提交前检查（必须执行）

在 `git commit` 之前执行：

```bash
git status
git diff --cached
```

快速扫描暂存区中的高风险模式：

```bash
git diff --cached | rg -n "(?i)(api[_-]?key|secret|token|password)\\s*[:=]|AKIA[0-9A-Z]{16}|-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----"
```

建议安装并执行泄露扫描工具（至少一个）：

```bash
# gitleaks
gitleaks detect --staged --redact

# 或 detect-secrets（示例）
detect-secrets scan > .secrets.baseline
detect-secrets-hook --baseline .secrets.baseline
```

## 4. 推荐 Git Hook

建议在本地配置 `pre-commit`，拦截疑似敏感信息：

```bash
#!/usr/bin/env bash
set -euo pipefail

PATTERN='(?i)(api[_-]?key|secret|token|password)\s*[:=]|AKIA[0-9A-Z]{16}|-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----'

if git diff --cached | rg -n "$PATTERN" >/dev/null; then
  echo "Potential secret detected in staged changes. Commit blocked."
  exit 1
fi
```

保存为 `.git/hooks/pre-commit` 并赋可执行权限：

```bash
chmod +x .git/hooks/pre-commit
```

## 5. 泄露应急处理

如果已经提交了敏感信息，按以下顺序处理：

1. 立刻轮换泄露凭证（改密码、废弃旧 token、重发新 key）
2. 立即撤销泄露凭证权限（最小化暴露窗口）
3. 清理 Git 历史中的敏感内容（`git filter-repo` 或 BFG）
4. 强制推送清理后的分支，并通知所有协作者重新同步
5. 在平台侧复核访问日志，确认是否出现异常调用

## 6. Pull Request 审查清单

PR 合并前，至少检查：

- 是否新增/修改了 `.env`、证书、密钥文件
- 是否出现硬编码凭证
- 是否把真实连接串写进了文档、注释或示例代码
- 是否上传了导出数据、日志快照、调试转储文件

## 7. 仓库建议

建议在仓库根目录维护统一 `.gitignore`，至少包含：

```gitignore
.env
.env.*
*.pem
*.key
*.p12
*.pfx
*.crt
```

---

Owner: Maintainers  
Last Updated: 2026-02-15

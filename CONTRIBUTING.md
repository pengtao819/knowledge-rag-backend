# 贡献指南

感谢你有兴趣为这个项目做贡献！这是一个面向学习者的开源项目，**任何形式的贡献都很欢迎**——不一定是写大段代码，报告一个 Bug、修正一处注释、补充一句文档，都同样有价值。

## 我可以做什么？

| 我想做 | 怎么做 |
| --- | --- |
| 报告 Bug | 提一个 Issue，尽量说明复现步骤、环境（Python 版本、模型、报错日志） |
| 提新想法 | 提一个 Issue，描述你想解决的问题和大致思路 |
| 修 Bug / 加功能 | 参考下面的开发流程，直接提 Pull Request |
| 改进文档 / 注释 | Fork 后直接改，提 PR |

## 开发流程

```bash
# 1. Fork 本仓库并克隆到本地
git clone https://github.com/pengtao819/knowledge-rag-backend.git
cd knowledge-rag-backend

# 2. 新建分支
git checkout -b feature/你的功能名

# 3. 配置环境（见 README「快速开始」），跑通项目
cp .env.example .env
pip install -r requirements.txt
uvicorn main:app --reload

# 4. 提交（建议遵循 Conventional Commits 风格）
git commit -m "feat: 简述改动"

# 5. 推送并提 PR
git push origin feature/你的功能名
```

## 提交信息约定

- `feat:` 新增功能
- `fix:` 修复 Bug
- `docs:` 文档改动
- `refactor:` 重构（不改变行为）
- `chore:` 杂项（依赖、配置等）

## 代码风格

- 遵循现有代码的分层结构：`api`（路由）→ `services`（业务）→ `db` / `core`
- 关键逻辑加中文注释，说明「为什么这么做」，而不只是「做了什么」
- 一个 PR 只做一件事，保持可审查

## 提 PR 前请确认

- [ ] 代码能跑通（`uvicorn main:app --reload` 正常启动）
- [ ] 相关接口自测通过
- [ ] 没有引入新的敏感信息（API Key 只写进本地 `.env`，不提交）

再次感谢你的贡献 🙌
# Contributing

感谢关注 `zhengda-research-copilot`。项目当前为 Preview，欢迎针对工作流、统计方法、文档和测试提出建议。

## 贡献前先确认

- 本项目是参赛研究辅助工具，不是主办方官方产品，也不保证获奖。
- 不提交真实受访者信息、原始问卷导出、账号凭证、报名代码或任何未经授权的材料。
- 不将模拟数据、虚构引用或示例统计结果包装成真实研究证据。
- 不直接复制其他仓库的 Skill 文本、代码、模板或素材；若确需复用，先核对许可证、保留必要版权声明并更新 `THIRD_PARTY_NOTICES.md`。
- 不新增虚假的徽章、测试结果、自动化能力或赛事规则。

## 推荐流程

1. 提交问题或说明需要解决的实际场景。
2. 对涉及竞赛规则的变更，附当届主办方/赛区/学校通知链接、发布日期与核验日期。
3. 对方法论变更，说明适用的数据类型、前提、失败条件与替代方案。
4. 更新 `SKILL.md`、对应 `references/`、模板与 `docs/PROJECT_SPEC.md` 中受影响的内容。
5. 更新 `CHANGELOG.md`。
6. 运行：

   ```powershell
   python -m unittest discover -s tests -p "test_*.py" -v
   python scripts/workflow.py --help
   python scripts/task_queue.py --help
   ```

7. 确认 ZIP 或发行包中包含完整目录，并且不包含 `state/`、`raw_private/`、`tasks/`、密钥或真实调查数据。

## Pull Request 检查项

- [ ] 变更目的和行为清晰；
- [ ] 测试通过，或明确说明无法运行的测试及原因；
- [ ] 文档和实现一致；
- [ ] 没有将人工操作描述为自动化；
- [ ] 没有降低数据真实性、隐私或独立审查要求；
- [ ] 第三方来源与许可证说明已更新（如适用）。

## 许可证

项目许可证仍待所有者确认。在 `LICENSE` 决策完成之前，请勿假定项目采用 MIT、Apache-2.0 或其他开源许可证。

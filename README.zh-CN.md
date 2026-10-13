# BadmintonAutoCut

[English](README.md) | [简体中文](README.zh-CN.md)

**一个探索如何从录制视频中识别羽毛球回合区间的计算机视觉研究项目。**研究结合场地几何、球员检测与 Pose、TrackNet V3 羽毛球候选，以及 LIVE / DEAD / UNKNOWN 活动时序建模。

[GitHub 仓库](https://github.com/YuCloer/BadmintonAutoCut-Demo) · [双语研究作品集](https://yucloer.github.io/BadmintonAutoCut-Demo/zh/) · [研究方法](docs/site/zh/methods.html) · [研究结果](docs/site/zh/research-report.html) · [完整原始报告](docs/site/RESEARCH_REPORT.html)

## 研究证据

### Court 几何

![真实羽毛球画面中的 Court 几何](docs/site/assets/evidence/court-260807-92-midpoint.jpg)

### 球员检测与 Pose

![真实画面中的实验性 Near/Far 姿态框和关键点骨架](docs/site/assets/evidence/m6-live-match-26100302-017-084s.png)

### TrackNet V3 候选点

![四个来源中的 52,861 个未关联 TrackNet 原始候选点](docs/site/assets/evidence/tracknet-raw-scatter-four-source.png)

### 活动时序

![编辑参照与 M6 的 LIVE、DEAD、UNKNOWN 状态时间线](docs/site/assets/evidence/m6-gt-state-timeline-four-source.png)

## 研究概况

2026-10-12 离线融合研究在**同一拍摄日的四段视频**上比较了两个独立模型分支。参照是人工编辑时间线，不是物理 LIVE/DEAD 或 Hit 真值。

| 离线分支 | 平衡准确率 | UNKNOWN | 完整区间 | 精确率 | 召回率 | 编辑 LIVE 损失 | 编辑 DEAD 保留 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 带尾部隔离的 Player + TrackNet 上下文 | 87.75% | 5.08% | 79/148 | 59.85% | 53.38% | 164.33 秒 | 62.85 秒 |
| 未隔离尾部的 Player + TrackNet 上下文 | 87.44% | 5.46% | 82/148 | 61.65% | 55.41% | 175.60 秒 | 51.12 秒 |

Tail-safe 少命中 3 个完整区间，但少损失 11.27 秒编辑 LIVE，并多保留 11.73 秒编辑 DEAD。平衡准确率衡量状态分类，不是 Rally 检测准确率。

## 方法与限制

- 视觉示例、Court 检查点、Tail-safe 评测和归档消融来自不同研究，不是一次生产运行。
- TrackNet 原始候选不等于时间关联轨迹，也不等于已验证的羽毛球轨迹。
- Near/Far 是实验性图像纵坐标 Pose 槽位，不是持久人物身份或认证过的场地远近侧身份。
- START 和 END 是候选边界；只有配对并独立评测后，才可能成为正式 Rally 边界。
- 四源对照属于同日开发证据，不能证明跨日期泛化。
- EventFirst 仍是已实现的生产路径，状态为 **`PRODUCTION_NOT_READY`**。该研究没有验收通过的生产 Rally 区间、KeepTimeline 输出或新增导出。

## 项目资源

- [双语研究作品集](https://yucloer.github.io/BadmintonAutoCut-Demo/zh/)
- [交互式实验对照](https://yucloer.github.io/BadmintonAutoCut-Demo/zh/#experiments)
- [研究方法说明](docs/site/zh/methods.html) · [维护中的方法 Markdown](docs/site/METHODS.md)
- [可复现性说明](docs/site/zh/reproducibility.html) · [维护中的溯源 Markdown](docs/site/REPRODUCIBILITY.md)
- [证据清单](docs/site/evidence-manifest.json)
- [完整原始研究报告](docs/site/RESEARCH_REPORT.html)

公开仓库只包含精选静帧和聚合研究结果，不包含源视频、模型权重、原始缓存或标注文件，因此无法仅凭本仓库重新运行数值评测。

# Moon Terrain · 七类月面地形与 Unity 演示

以真实月球 DEM 为基础，分层补充近景细节、岩石和表面材质，用于地形资产展示与后续实验场地筛选。

## 八类地形 × 三级 Unity 演示 v0.4.0

新增 **8 类 × 3 级，共 24 个场景**：石障、沟壑、上行阶梯、局部坑、盆地、波状起伏、Perlin 起伏、粗糙 Perlin。三级称为**基础、增强、复合**，用于比较形态和遮挡变化，尚未经过机器人或模型的经验难度标定。

**[下载工具包（Windows）](https://github.com/moonspace123/moon-terrain/releases/download/v0.4.0/Lunar_Terrain_Download_Tools_v0.4.0.zip)** · **[版本页面](https://github.com/moonspace123/moon-terrain/releases/tag/v0.4.0)** · **[详细打开步骤](docs/terrain-three-levels.md)**

完整解压下载工具包，然后选择：

| 使用方式 | 双击命令 | 下载内容 |
| --- | --- | --- |
| 在 Unity 中打开和编辑 | `Download_Unity.cmd` | 工程和配套资源，合计约 2.52 GB |
| Windows 直接看效果 | `Download_Windows_Demo.cmd` | 独立演示，约 0.72 GB |

工具会下载小分段，逐段校验、合并为普通 ZIP 并解压。中断后可再次运行，复用已校验分段；需要互联网，不需要安装 Python、Git 或登录 GitHub。

Unity 使用 **2022.3.62f3c1**。在 Hub 添加工具包内的 `Ready/Extracted_Unity/Lunar_Terrain_Three_Levels/UnityProject`，等待导入，打开 `Assets/LevelScenes/occlusion_levels_trench_a0.unity` 并播放。Windows 演示在 `Ready/Extracted_Windows/Lunar_Terrain_Three_Levels/Open_Demo.cmd`。

![八类三级总览，Unity 实机渲染](docs/images/terrain_three_levels_overview.jpg)

- 保留真实 DEM 大尺度背景；同一类三级共用水平路线、目标落地规则、光照和比较相机。增强级提高主人工形态幅度，复合级加入温和次级起伏；石障类加入第二块主要遮挡岩石。
- 包含源资产、旧场景、脚本、`.meta`、`Packages`、`ProjectSettings`；[生成与检查源码](unity/three-levels/)可在仓库浏览。完整模型、贴图与程序在 Release 分段附件中，GitHub 自动生成的 Source code ZIP 不含这些大资产。
- 24 场景的 Unity Play Mode 和 Windows 实际运行检查通过，包括 GPU 可见性、画面与场景切换。未执行逐按钮鼠标点击、机器人行走、MuJoCo、VLM 或 RSR@K；目前为相机路线演示。

v0.3.0、v0.2.0、v0.1.0 的下载和说明继续保留在下方。

## 完整 Unity 地形工程 v0.3.0

**[下载完整可编辑 Unity 工程](https://github.com/moonspace123/moon-terrain/releases/download/v0.3.0/Lunar_Unity_Project_v0.3.0.zip)** · **[版本说明、校验文件与验证报告](https://github.com/moonspace123/moon-terrain/releases/tag/v0.3.0)**

解压后，在 Unity Hub 中添加 `Lunar_Unity_Project/UnityProject`，使用 **Unity 2022.3.62f3c1** 打开。首次导入完成后，选择菜单 **Lunar Terrain → Open interactive preview**，在 Game 窗口演示。

- 包含七个已保存场景、全部地形网格、九类岩石源模型、贴图、材质、着色器、脚本和项目设置，保留全部 `.meta`。
- 可切换七类地形和七种材质；支持右键转向、WASD 移动、滚轮调整视场、低机位复位与俯视近景。
- 发布副本已登记七个可切换场景，并把生成与验证输出放到工程内的 `Outputs/`，方便换电脑打开。
- 已在新路径重新导入并运行七个场景，完成 49 次材质切换、视角检查和实际画面渲染。验证记录随包提供。

也可运行 `python tools/download_unity_project.py`，下载、校验并解压到 `projects/Lunar_Unity_Project/`。

**[打开工程的详细说明](docs/unity-project.md)** · **[可浏览的小体积工程源码](unity/)**

![Unity 工程实际 Play Mode 画面](docs/images/unity_project_play_mode.jpg)

完整工程的大型网格和贴图随 Release ZIP 提供，克隆仓库后需另外下载。工程用于地形外观与交互演示；真实 DEM、合成近景细节与岩石布置的来源边界见文档。

## 网页演示：Unity 材质与七类地形 v0.2.0

**[下载完整演示包（约 396 MB）](https://github.com/moonspace123/moon-terrain/releases/download/v0.2.0/Lunar_Unity_Demo.zip)** · **[版本说明与校验文件](https://github.com/moonspace123/moon-terrain/releases/tag/v0.2.0)**

解压后双击 `Lunar_Unity_Demo/index.html` 或 `START_HERE.cmd`，使用 Edge / Chrome 打开；保留完整文件夹，可离线演示。

![七类月面地形 Unity 演示页面](docs/images/unity_demo_preview.jpg)

- 七类地形一键切换；98 张 1920×1080 Unity 实际渲染图覆盖七类 × 两机位 × 七种材质。
- 默认使用当前认可的混合材质：Moon 01 底层、Flat Macro 近处细节、Dusted 局部覆尘。
- 同机位滑动与并排对比，低机位与俯视近景切换，顺序导览、演示模式和全屏。
- 三维观察可拖动旋转、滚轮缩放、查看地形全貌；首次离线加载在制作机器上约 5 秒。

**Unity 区是实际渲染图；可旋转三维区是同源地形的 Three.js 浏览器重渲染，外观可能不同，并非 Unity WebGL。** 原材质是 Unity 内重建的比较基线。新材质没有新增几何位移，原有微起伏与岩石保持。

也可以通过 Python 标准库工具下载并校验：

```console
python tools/download_unity_demo.py
```

下载后打开 `demo/Lunar_Unity_Demo/index.html`。无需安装 Python 也可直接下载 ZIP 使用。

[制作方法与数据边界](docs/UNITY_DEMO.md) · [网页界面源文件](viewer/unity-demo/) · [检查记录](viewer/unity-demo/evidence/browser_checks.json)

大体量渲染图、贴图与地形数据随 Release 提供；`viewer/unity-demo/` 是界面与交互源文件，需要完整包中的资产才能运行。v0.2.0 网页包包含 Unity 渲染成果和浏览器交互地形；完整可编辑 Unity 工程另见上方 v0.3.0。

---

## 历史演示 v0.1.0

以下保留原三维细节对照页面的说明、旧版下载和制作流程。

以真实月面 DEM 为大尺度地形基础，叠加可复现的表面细节和岩石布局，展示七类地形。当前版本是 **Three.js / WebGL 浏览器样板**。

![沟谷岩石接地修正前后](docs/images/rille_seating_comparison.jpg)

## 下载并查看

**[下载完整离线展示包（约 240 MB）](https://github.com/moonspace123/moon-terrain/releases/download/v0.1.0/Lunar_Detail_Regions_03.zip)**

完整解压后，在 Windows 双击 `START_HERE.cmd`；或用 Edge / Chrome 打开 `START.html`（图片入口）和 `index.html`（三维交互）。完整包可离线使用，不需要安装 Python。请保留所有子目录。

也可以克隆仓库后，用 Python 3.10+ 下载和启动：

```console
git clone https://github.com/moonspace123/moon-terrain.git
cd moon-terrain
python tools/download_demo.py
python tools/verify_demo.py
python tools/serve.py
```

上述下载、校验与浏览工具仅使用 Python 标准库。制作代码的依赖见 `requirements.txt`。

## 七类地形

| 类型 | 组合效果 |
| --- | --- |
| 平坦岩块区 | ![平坦岩块区](docs/images/plain.jpg) |
| 连续坡面 | ![连续坡面](docs/images/slope.jpg) |
| 完整坑区与坑缘 | ![坑缘](docs/images/rim.jpg) |
| 局部凹地 | ![局部凹地](docs/images/depression.jpg) |
| 天然坡折 | ![天然坡折](docs/images/ridge.jpg) |
| 坑外连续起伏 | ![坑外连续起伏](docs/images/ejecta.jpg) |
| 沟谷与两岸 | ![沟谷与两岸](docs/images/rille.jpg) |

每类只增强一处 12×12 米细节观察点，共七处；不代表原区域的每个位置均已加入同等细节。

## 效果由什么组成

- **真实 DEM**：LROC 的 LINNECRATER、SHACKRDGE02、MERSENIUS1，原始间距约 2 米或 3.5 米，决定大尺度地貌。
- **扫描素材**：Poly Haven 月壤模拟材料与地球岩石扫描，以及 Apollo 样品形状资产。素材来源与原位月面测量需区分。
- **合成增强**：数值生成的小凸起、细颗粒法线、岩石尺寸与空间布局、埋入程度。
- **渲染**：Three.js 材质、太阳光、投影、颜色与曝光处理。
- **检查**：数值与接地检查，加上 Playwright 浏览器加载、切换、截图复查。Skill 是工作指引，不是三维渲染器；下载和运行样板不需要安装 Codex skill。

局部网格间距为 2 厘米，**不等于 2 厘米实测精度**。细节未经对应地点的岩石统计标定。没有调用外部图像或三维生成模型来生成该样板。

## 四种对照

| 版本 | 内容 |
| --- | --- |
| A | 原认可地面与石头布局 |
| B | 增加法线受光细节，几何保持不变 |
| C | 增加真实网格凸起 |
| D | 凸起、法线细节与分层岩石布局组合 |

## 验证范围

- 已检查七类地形、28 种版本切换及 43 张贴图的加载。
- 已检查网格接缝、原始 DEM 副本、导出数据和静态接地；沟谷修订覆盖继承岩石与碎石。
- 已检查完整压缩包、文件哈希及解压后的离线浏览。
- **尚未验证** MuJoCo / UE 导入、动态物理稳定性、机器狗行走、TASK3 重观测或 VLM 导航。

静态接地、截图和页面打开不构成机器人任务成功证据。具体检查记录见 [docs/reports](docs/reports/)。

## 仓库内容与复现边界

```text
src/             数值细节、布局、接地修正与接缝检查代码
viewer/          浏览器页面与渲染代码（大型素材在 Release 中）
tools/           完整样板的下载、文件校验与本地浏览工具
docs/            效果图、参数、来源、历史检查记录
requirements.txt 制作代码所需依赖
```

完整样板的下载、离线查看与文件校验可独立使用。**从原始 DEM 重新构建全部成果仍依赖前序区域库输入；这些输入不在本仓库中。** 本仓库没有声称一条命令可以从原始卫星数据重建全部成果。重建输入格式和处理阶段见 [制作流程](docs/PIPELINE.md)。

第三方资产及其许可见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。原创代码尚未另行指定开源许可。历史报告保留各自检查阶段的含义，不代表本次上传重新运行了机器人或物理实验。

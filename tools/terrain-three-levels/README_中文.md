# 八类地形 × 三级（v0.4.0）：下载与打开

## 推荐：自动下载

下载并完整解压 **Lunar_Terrain_Download_Tools_v0.4.0.zip**。

- 要在 Unity 打开、修改：双击 `Download_Unity.cmd`。
- 只看 Windows 演示：双击 `Download_Windows_Demo.cmd`。

工具会从本仓库 Release 下载小分段，逐段校验，自动合并成普通 ZIP 并解压。
中断后再次双击同一命令，会复用已经校验通过的分段。
工具使用 Windows PowerShell，不需要安装 Python、Git 或 GitHub CLI，也不需要登录 GitHub。
请在空间充足的位置完整解压下载工具；Unity 建议至少预留 15 GB，Windows 演示至少 5 GB。

## Unity 打开

下载完成后，打开：
`Ready/Extracted_Unity/Lunar_Terrain_Three_Levels/UnityProject`

使用 **Unity 2022.3.62f3c1**，在 Unity Hub 添加上述 UnityProject 文件夹。
等待首次导入，打开 `Assets/LevelScenes/occlusion_levels_trench_a0.unity`，点击播放。
新场景共 24 个，左侧选择八类地形，上方选择基础、增强、复合三级。
旧场景、源资产与全部 .meta、Packages、ProjectSettings 同时保留。
`对比浏览.html` 可查看 24 场景静态对比；Preview 内有总览与灰色材质矩阵。

## Windows 演示

下载完成后，双击：
`Ready/Extracted_Windows/Lunar_Terrain_Three_Levels/Open_Demo.cmd`

请保留 WindowsDemo 内全部文件，不要只取出 exe。

## 手动下载与合并

分段附件是普通 ZIP 的连续二进制部分，不能单独解压。
Unity 需要清单列出的全部工程分段和配套资源分段，Windows 演示只需要全部演示分段。
附件名称含 `.part` 或 `.chunk`；请按清单选择，不要依靠文件名推测所需分段。
完整分段清单、大小与 SHA-256 在 `Release_Manifest_v0.4.0.json`。

把分段放在下载工具的 Parts 文件夹，然后运行对应命令即可合并、校验和解压。
合并后的两个 Unity ZIP 也可手动解压到同一个目录，合并同名文件夹。
GitHub 自动提供的 Source code ZIP 不含完整模型、贴图或 Windows 程序，请使用本版下载工具。
如果解压输出目录已存在，工具会保留已有目录，只准备 ZIP；可将 ZIP 手动解压到一个新目录。

## 内容与检查边界

八类为 barrier、trench、stairs_up、pit、basin、waves、perlin、perlin_rough。
真实 DEM 背景不整体缩放。增强级的主人工形态幅度为基础级的 1.5 倍；
复合级叠加温和次级起伏，石障类增加第二块主要遮挡岩石。
同一类三级共用水平路线、目标落地规则、比较相机与光照。

24 场景 Unity Play Mode 与 Windows 实际运行检查通过，包含 GPU 可见性、渲染和场景切换。
切换检查调用运行时入口，未进行鼠标逐按钮点击。
目前为相机路线演示；机器人行走、MuJoCo、VLM、RSR@K 与经验难度标定未执行。
基础/增强/复合为设计分级，不能宣称简单/中等/困难已通过实验标定。

原交付包 1496 个文件均保留。证据见 Verification 与 UnityProject/Outputs。
第三方来源见包内 THIRD_PARTY_NOTICES.md 和仓库 docs/sources。

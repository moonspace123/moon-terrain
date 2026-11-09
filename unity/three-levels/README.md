# 八类 × 三级 Unity 源码

完整可编辑工程请从 [v0.4.0 Release](https://github.com/moonspace123/moon-terrain/releases/tag/v0.4.0)
下载工具包，运行 Download_Unity.cmd 获取工程和配套资源。仓库只保存小体积源码、预览和说明。

`Sources/` 与交付包对应目录一致，包含几何生成器和 Unity 场景、运行时、检查脚本。
Python 生成器需 NumPy、SciPy；应在完整解压的交付目录使用，`Sources` 与 `UnityProject` 并列。
先退出 Unity，运行 `python Sources/build_three_levels.py`，然后在 Unity 菜单
`Lunar Levels/Rebuild twenty-four scenes` 重建场景。
运行时脚本的实际安装位置为 `Assets/TerrainLevels/Scripts`，Editor 脚本位于 `Assets/TerrainLevels/Editor`。
修改脚本时请编辑项目中的实际文件；这里的副本用于浏览和追踪。

`level_parameters.json` 记录分级参数和源区域；`delivery_verification.json` 记录已完成检查及未执行项目。
来源声明沿用仓库根目录 THIRD_PARTY_NOTICES.md；本仓库原创代码尚未指定统一开源许可证。

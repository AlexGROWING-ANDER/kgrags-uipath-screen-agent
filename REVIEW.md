# KGRAGS UiPath Screen Agent 安卓适配

运行器来自`6a36226933763dc37a5a686f9498cdeaba7d4879`。从`run_mobile_uipath.py`启动。每步开始时保存截图，下一步截图显示上一动作后的画面。

`runtime_dependencies/OSWorld-v1/`保存运行时引用的`mm_agents/uipath`模块，基于`b138d348256078fa634fc3b73567a7337c793e6b`及本机调用、定位和记忆适配。按运行器的`UIPATH_REPO`路径使用对应的OSWorld-v1源码环境。`runtime_dependencies/mobile_agent_v3/`保存运行器引用的通信权限模块，供核对原工作区中的同名依赖。网关凭据从本机配置加载。

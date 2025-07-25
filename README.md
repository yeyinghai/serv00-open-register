# serv00开放注册通知

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](https://choosealicense.com/licenses/mit/)

一个简单而机器人，用于serv00网站的注册开放情况检测。它会自动检查开放注册后，通过bark开放通知。

## 1、Fork 或创建仓库

加⭐收藏本项目，然后将此仓库 Fork 到你的 GitHub 账号。

## 2、 配置环境变量
在 GitHub 仓库中配置以下环境变量：

**方式1：直接跳转** 👉 [点击进入Secrets配置页面](../../settings/secrets/actions) → 点击 **"New repository secret"** 按钮

**方式2：手动导航**：Settings → Secrets and variables → Actions → New repository secret

必需配置

名称：BARK_KEY  

值：粘贴您在第一步中从 Bark App 获取的 Key。

名称：BARK_SERVER_URL   

值：如果用官方的地址填写: https://api.day.app

有自建的bark服务器，请填写自己的地址。

## ✨ 特性

-   **易于配置**: 为了安全地使用您的 bark，我们不把它们直接写在代码里，而是使用 GitHub 的 "Secrets" 功能。
-   **易于部署**: 可以轻松地作为定时任务 (Cron Job) 或通过 GitHub Actions 自动化运行。

## bark token获取
在您的 iPhone 或 Android 手机上，从 App Store 或应用市场搜索并下载 Bark App。

打开 App，您会看到一个 URL 地址，格式类似于 。https://api.day.app/YOUR_KEY/这里是推送内容

其中， 就是您独一无二的 Bark Key。 请复制并安全保存它。 之后我们发送的任何通知都会推送到安装了这个 App 并使用此 Key 的设备上。YOUR_KEY

## 🚀 说明

这是一个更精确、更可靠的判断方法。 我们从页面上提取两个数字（当前账户数和最大账户数），然后比较它们是否一致。

## 🤖 使用 GitHub Actions 实现自动化

您无需自己的服务器即可 24/7 运行此监控。可以使用 GitHub Actions 来实现定时自动化检查。

在您的 GitHub 仓库页面，点击 Settings (设置)。

在左侧菜单中，找到 Secrets and variables -> Actions。

点击 New repository secret 按钮，创建一个新的 Secret：

名称：BARK_KEY

Secret: 粘贴您在第一步中从 Bark App 获取的 Key。

再创建一个新的 Secret：

名称：BARK_SERVER_URL

如果用官方的地址填写: https://api.day.app

有自建的bark服务器，请填写自己的地址。

## 完成与测试

一切都已准备就绪。 GitHub Actions 会在您设定的时间自动运行。

如果您想立刻测试，可以和之前一样，进入仓库的 Actions 标签页，手动触发 "检测Serv00开放注册" 工作流。

如果脚本检测到注册开放，您的手机将会收到一条来自 Bark 的推送通知，点击该通知会直接跳转到 Serv00 的注册页面，非常方便。

## 📜 许可证

本项目使用 [MIT License](LICENSE)。

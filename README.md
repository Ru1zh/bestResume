# bestResume

[English version](README_en.md)

## 项目简介

本项目基于 [easyCV](https://github.com/lvy010/easyCV) 开发，是一个由 YAML 驱动的中英文简历系统，支持：

- 中文和英文两套简历内容
- 浏览器实时预览
- 浏览器内编辑 YAML
- 中英文版本切换
- A4 页面分页预览
- 使用浏览器打印并保存为 PDF
- IEEE、APA、MLA 文献引用格式
- Windows、macOS、Linux 启动方式

简历使用 A4 页面和简洁的学术风格；中文简历中的中文字符使用思源黑体（Source Han Sans），英文、数字、链接和英文标点使用 Times New Roman。

## 简历示意图与字体

### 中文简历

![中文简历示意图](example/Resume_Chinese.jpg)

中文简历中的中文字符使用思源黑体（Source Han Sans）；英文、数字、链接和英文标点使用 Times New Roman。

### 英文简历

![英文简历示意图](example/Resume_English.jpg)

英文简历使用 Times New Roman。

## 快速启动

### Windows

```bat
cd bestResume
start.bat
```

### macOS

```bash
cd bestResume
chmod +x start_mac.sh
./start_mac.sh
```

### Linux

```bash
cd bestResume
chmod +x start_linux.sh
./start_linux.sh
```

启动脚本会创建虚拟环境、安装依赖，并在 `http://127.0.0.1:8020` 启动服务。

## 页面地址

- [英文简历预览](http://127.0.0.1:8020/resume?lang=en)
- [中文简历预览](http://127.0.0.1:8020/resume?lang=zh)
- [英文 YAML 编辑器](http://127.0.0.1:8020/editor?lang=en)
- [中文 YAML 编辑器](http://127.0.0.1:8020/editor?lang=zh)

## 编辑简历

可以直接编辑：

- `resume_english.yaml`：英文简历数据
- `resume_chinese.yaml`：中文简历数据

也可以打开对应语言的 YAML 编辑器，在浏览器中修改并保存。

## 照片与无照片模式

简历会根据 `basics.photo` 是否存在自动切换页首布局。

### 有照片模式

保留 `photo` 字段时，基本信息显示在左侧，照片显示在右侧：

```yaml
basics:
  photo: "/img/奶龙证件照.jpg"
```

LinkedIn、GitHub 和个人主页会沿用详细显示方式，同时显示名称和完整网址。

### 无照片模式

不需要照片时，可以注释或删除 `photo` 字段：

```yaml
basics:
  # photo: "/img/奶龙证件照.jpg"
```

无照片模式下：

- 姓名、学校、求职方向和联系方式整体居中。
- LinkedIn、GitHub 和个人主页合并为一行，例如 `LinkedIn | GitHub | 个人主页`。
- 页面只显示链接名称，不显示完整网址；点击名称后会在新标签页打开对应页面。
- 缺少某个链接字段时会自动隐藏该项，并调整分隔符。

#### 中文无照片简历

![中文无照片简历示意图](example/Resume_Chinese_NoPhoto.jpg)

#### 英文无照片简历

![英文无照片简历示意图](example/Resume_English_NoPhoto.jpg)

修改 YAML 并保存后，刷新简历预览即可看到对应布局。

## 文献引用

文献使用结构化 YAML 字段，每条文献可以单独选择 `ieee`、`apa` 或 `mla`：

```yaml
publications:
  - style: ieee
    authors:
      - N. Hao
      - R. Vega
      - S. Ito
    title: "A compositional world model for open-ended environment prediction"
    type: journal
    container_title: "Nature"
    year: 2026
```

如果文献缺少标题或内容为空，该文献会被忽略；如果所有文献都为空，整个“论文发表”小节不会显示。

## 项目结构

```text
resume_english.yaml   <- 英文简历数据
resume_chinese.yaml   <- 中文简历数据
app.py                <- FastAPI 服务
templates/resume.html <- 简历预览模板
templates/editor.html <- YAML 编辑器页面
static/style.css      <- A4 页面和简历样式
start.bat             <- Windows 启动脚本
start_mac.sh          <- macOS 启动脚本
start_linux.sh        <- Linux 启动脚本
```

## 打印

点击预览页面顶部的“打印”按钮。在浏览器打印对话框中选择“保存为 PDF”即可生成 PDF。

## API

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/resume` | 简历预览 |
| `GET` | `/editor` | YAML 编辑器 |
| `GET` | `/api/resume` | 获取简历 JSON |
| `PUT` | `/api/resume` | 保存简历 JSON |
| `GET` | `/api/resume/raw` | 获取原始 YAML |
| `PUT` | `/api/resume/raw` | 保存原始 YAML |
| `GET` | `/docs` | OpenAPI 文档 |

## License

MIT

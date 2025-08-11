# 文件处理模块 (File Module)

一个独立的文件上传、下载和解析模块，可以直接复制到其他项目中使用。

## ✨ 特性

- **独立运行**: 无需额外配置，复制即可使用
- **远程服务器**: 默认连接到远程存储服务
- **多格式支持**: 支持 docx, xlsx, pptx, txt, md, html, json 等格式
- **完整功能**: 文件上传、下载、解析一体化
- **简单易用**: 一行代码即可初始化使用

## 🚀 快速开始

### 1. 复制模块
```bash
# 将整个 file_module 文件夹复制到您的项目中
cp -r file_module /path/to/your/project/
```

### 2. 安装依赖
```bash
cd file_module
pip install -r requirements.txt
```

### 3. 使用模块
```python
from file_module import FileProcessor

# 初始化（使用默认远程服务器配置）
processor = FileProcessor()

# 上传文件
file_token = processor.upload_file("/path/to/file.docx")

# 下载文件
file_path = processor.download_file(file_token, "/tmp")

# 解析文件
content = processor.parse_file(file_path, "docx")
```

## 📁 文件结构

```
file_module/
├── __init__.py              # 模块入口
├── file_processor.py        # 核心处理器
├── file_utils.py           # 文件工具类
├── parsers/                # 文件解析器
│   ├── __init__.py
│   ├── word_parser.py      # Word文档解析
│   ├── excel_parser.py     # Excel文件解析
│   ├── powerpoint_parser.py # PowerPoint解析
│   ├── text_parser.py      # 文本文件解析
│   ├── markdown_parser.py  # Markdown解析
│   └── html_parser.py      # HTML解析
├── requirements.txt        # 依赖包列表
├── run_demo.py            # 演示脚本
├── INSTALL.md             # 安装说明
├── README.md              # 本文档
├── tests/                 # 测试文件
└── examples/              # 使用示例
```

## 🔧 配置说明

### 默认配置
模块默认连接到远程服务器：
- **存储服务**: `http://ai.test.hcece.net`
- **应用标识**: `hdec`
- **租户ID**: `100023`

### 自定义配置
```python
processor = FileProcessor(
    storage_base_url="http://your-server.com",
    app="your_app",
    app_secret="your_secret",
    tenant_id="your_tenant"
)
```

## 📋 支持的文件格式

| 格式 | 扩展名 | 解析器 | 状态 |
|------|--------|--------|------|
| Word文档 | .docx, .doc | WordParser | ✅ |
| Excel表格 | .xlsx, .xls | ExcelParser | ✅ |
| PowerPoint | .pptx, .ppt | PowerPointParser | ✅ |
| 文本文件 | .txt | TextParser | ✅ |
| Markdown | .md, .markdown | MarkdownParser | ✅ |
| HTML网页 | .html, .htm | HtmlParser | ✅ |
| JSON数据 | .json | 内置解析 | ✅ |

## 🎯 主要功能

### 文件上传
```python
file_token = processor.upload_file("/path/to/file.docx")
print(f"文件Token: {file_token}")
```

### 文件下载
```python
file_path = processor.download_file(file_token, "/tmp")
print(f"下载路径: {file_path}")
```

### 文件解析
```python
content = processor.parse_file(file_path, "docx")
print(f"解析出 {len(content)} 个内容块")
```

### 下载并解析
```python
content = processor.download_and_parse(file_token, "docx", "/tmp")
```

## 🧪 测试

### 运行演示
```bash
python run_demo.py
```

### 验证导入
```bash
python -c "from file_module import FileProcessor; print('✅ 模块导入成功')"
```

## 📦 依赖包

- `requests>=2.25.1` - HTTP请求
- `chardet>=4.0.0` - 字符编码检测
- `python-docx>=0.8.11` - Word文档处理
- `pandas>=1.3.0` - 数据处理
- `openpyxl>=3.0.9` - Excel文件处理
- `python-pptx>=0.6.21` - PowerPoint处理
- `beautifulsoup4>=4.9.3` - HTML解析
- `lxml>=4.6.3` - XML/HTML解析

## 🔍 故障排除

### 导入错误
确保：
1. 已安装所有依赖包
2. Python路径设置正确
3. 模块文件夹结构完整

### 网络连接
确保：
1. 网络连接正常
2. 远程服务器可访问
3. 防火墙设置正确

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**注意**: 此模块已配置好远程服务器，可直接使用。如需修改服务器配置，请在初始化时传入自定义参数。

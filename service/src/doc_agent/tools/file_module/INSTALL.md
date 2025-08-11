# 文件模块安装和使用说明

## 快速开始

### 1. 复制模块
将整个 `file_module` 文件夹复制到您的项目中。

### 2. 安装依赖
```bash
cd file_module
pip install -r requirements.txt
```

### 3. 测试运行
```bash
python run_demo.py
```

### 4. 验证功能
```bash
python -c "from file_module import FileProcessor; print('✅ 模块导入成功')"
```

## 使用方法

### 基本使用
```python
from file_module import FileProcessor

# 使用默认配置（连接到远程服务器）
processor = FileProcessor()

# 下载文件
file_path = processor.download_file("your_file_token", "/tmp")

# 解析文件
content = processor.parse_file(file_path, "docx")

# 上传文件
file_token = processor.upload_file("/path/to/your/file.docx")
```

### 自定义配置
```python
# 使用自定义配置
processor = FileProcessor(
    storage_base_url="http://your-storage-service.com",
    app="your_app",
    app_secret="your_secret",
    tenant_id="your_tenant"
)
```

## 支持的文件格式

- **文档**: docx, doc, xlsx, xls, pptx, ppt
- **文本**: txt, md
- **网页**: html, htm
- **数据**: json

## 功能特性

- ✅ 文件上传到远程服务器
- ✅ 从远程服务器下载文件
- ✅ 多种文件格式解析
- ✅ 文件格式转换
- ✅ 错误处理和日志记录

## 注意事项

1. 默认配置连接到 `http://ai.test.hcece.net` 服务器
2. 确保网络连接正常
3. 文件上传下载需要有效的文件token
4. 解析功能支持本地文件，无需网络连接

## 故障排除

如果遇到导入错误，请确保：
1. 已安装所有依赖包
2. Python路径设置正确
3. 模块文件夹结构完整

# VSCode Auto-Format Python Setup Guide

## 🚀 Tổng quan

Hướng dẫn này sẽ giúp bạn cấu hình VSCode để tự động format Python code khi auto save bằng các công cụ có sẵn trong Python extension.

## 📋 Các bước cài đặt

### 1. Cài đặt Python Extension

Đảm bảo bạn đã cài đặt Python extension cho VSCode:

- Extension ID: `ms-python.python`
- Hoặc tìm "Python" trong Extensions marketplace

### 2. Cấu hình tự động

File `.vscode/settings.json` đã được tạo với cấu hình sử dụng formatter có sẵn:

- **autopep8**: Format code theo chuẩn PEP8 (có sẵn trong Python extension)
- **pylint**: Kiểm tra code quality (có sẵn trong Python extension)
- **Auto format on save**: Tự động format khi save
- **Không cần cài thêm package nào**

## 🔧 Cấu hình chi tiết

### Formatter: autopep8 (Built-in)

```json
{
  "python.formatting.provider": "autopep8",
  "[python]": {
    "editor.defaultFormatter": "ms-python.python"
  }
}
```

**Ưu điểm của autopep8:**

- ✅ Có sẵn trong Python extension
- ✅ Tuân thủ chuẩn PEP8
- ✅ Không cần cài thêm package
- ✅ Tự động fix formatting issues

### Linting: pylint (Built-in)

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.lintOnSave": true
}
```

**Linting features:**

- ✅ PEP 8 compliance
- ✅ Code quality checks
- ✅ Có sẵn trong Python extension
- ✅ Không cần cài thêm package

### Auto-save Settings

```json
{
  "editor.formatOnSave": true,
  "editor.formatOnPaste": true,
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true
}
```

## 🎯 Các tính năng

### 1. Format on Save ✅

- Tự động format khi nhấn `Ctrl+S` (Windows/Linux) hoặc `Cmd+S` (Mac)
- Code sẽ được format theo chuẩn PEP8

### 2. Format on Paste ✅

- Tự động format khi paste code vào editor
- Giúp code paste vào luôn đẹp

### 3. Linting ✅

- Hiển thị warnings/errors trực tiếp trong editor
- Kiểm tra code quality real-time

### 4. No Extra Installation ✅

- Không cần cài thêm package nào
- Sử dụng formatter có sẵn trong Python extension

## 🔥 Keyboard Shortcuts

### Manual Format

- `Shift+Alt+F` (Windows/Linux)
- `Shift+Option+F` (Mac)

### Quick Fix

- `Ctrl+.` (Windows/Linux)
- `Cmd+.` (Mac)

## 📝 Ví dụ Before/After

### Before (messy code):

```python
import os,sys
def   get_article(id):
    if id==None:
        return None
    return{"id":id,"title":"Test"}

class ArticleService:
    def __init__(self):
        self.redis=Redis()
```

### After (auto-formatted):

```python
import os
import sys


def get_article(id):
    if id is None:
        return None
    return {"id": id, "title": "Test"}


class ArticleService:
    def __init__(self):
        self.redis = Redis()
```

## 🛠️ Troubleshooting

### 1. Formatter không hoạt động

- Kiểm tra Python extension đã cài đặt
- Reload VSCode: `Ctrl+Shift+P` → "Developer: Reload Window"

### 2. Linting không hoạt động

- Kiểm tra Python interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter"
- Đảm bảo Python extension đã active

### 3. Settings không áp dụng

- Restart VSCode
- Kiểm tra file `.vscode/settings.json` đã tồn tại

## 🎨 Customization

### Thay đổi line length

```json
{
  "editor.rulers": [100]
}
```

### Disable format on save cho specific files

```json
{
  "[python]": {
    "editor.formatOnSave": false
  }
}
```

### Chuyển sang formatter khác (nếu cần)

```json
{
  "python.formatting.provider": "yapf"
}
```

## ✅ Kết quả

Sau khi setup xong, bạn sẽ có:

- 🎯 Code tự động format khi save
- 🔍 Real-time linting warnings
- 🎨 Consistent code style theo PEP8
- 🚀 Không cần cài thêm package nào
- ⚡ Setup đơn giản chỉ với Python extension

## 📖 Tài liệu tham khảo

- [VSCode Python Extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- [PEP8 Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [autopep8 Documentation](https://pypi.org/project/autopep8/)

---

_Happy coding! 🎉_

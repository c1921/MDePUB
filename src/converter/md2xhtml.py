import markdown2
import os
from typing import Optional

class MarkdownConverter:
    def __init__(self):
        self.md = markdown2.Markdown(extras=[
            'fenced-code-blocks',
            'tables',
            'header-ids',
            'metadata',
            'footnotes'
        ])
    
    def convert_to_xhtml(self, markdown_content: str) -> str:
        """
        将Markdown内容转换为XHTML
        
        Args:
            markdown_content: Markdown格式的文本内容
            
        Returns:
            转换后的XHTML字符串
        """
        xhtml_content = self.md.convert(markdown_content)
        
        # 添加XHTML头部
        xhtml_template = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Converted from Markdown</title>
    <meta charset="utf-8"/>
</head>
<body>
{xhtml_content}
</body>
</html>'''
        
        return xhtml_template
    
    def convert_file(self, input_file: str, output_file: Optional[str] = None) -> str:
        """
        转换Markdown文件为XHTML文件
        
        Args:
            input_file: 输入的Markdown文件路径
            output_file: 输出的XHTML文件路径（可选）
            
        Returns:
            生成的XHTML文件路径
        """
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"找不到输入文件: {input_file}")
            
        with open(input_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
            
        xhtml_content = self.convert_to_xhtml(markdown_content)
        
        if output_file is None:
            output_file = os.path.splitext(input_file)[0] + '.xhtml'
            
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xhtml_content)
            
        return output_file
    
    def convert_directory(self, input_dir: str, output_dir: str, recursive: bool = True) -> list[str]:
        """
        转换目录下的所有Markdown文件为XHTML文件
        
        Args:
            input_dir: 输入目录路径
            output_dir: 输出目录路径（EPUB根目录）
            recursive: 是否递归处理子目录，默认为True
            
        Returns:
            生成的所有XHTML文件路径列表（相对于OEBPS目录的路径）
        """
        if not os.path.exists(input_dir):
            raise FileNotFoundError(f"找不到输入目录: {input_dir}")
        
        # 确保OEBPS目录存在
        oebps_dir = os.path.join(output_dir, 'OEBPS')
        os.makedirs(oebps_dir, exist_ok=True)
        
        converted_files = []
        
        def process_markdown_file(file_path: str) -> None:
            # 获取相对路径，用于在输出目录中创建相同的目录结构
            rel_path = os.path.relpath(file_path, input_dir)
            output_path = os.path.join(oebps_dir, os.path.splitext(rel_path)[0] + '.xhtml')
            
            # 确保输出文件的目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 转换文件
            self.convert_file(file_path, output_path)
            
            # 添加相对于OEBPS的路径
            rel_output_path = os.path.relpath(output_path, oebps_dir)
            converted_files.append(rel_output_path)
        
        for root, dirs, files in os.walk(input_dir):
            if not recursive and root != input_dir:
                continue
                
            for file in files:
                if file.lower().endswith(('.md', '.markdown')):
                    file_path = os.path.join(root, file)
                    process_markdown_file(file_path)
        
        return converted_files 
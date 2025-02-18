import os
import shutil
from src.converter.md2xhtml import MarkdownConverter
from src.converter.epub_builder import EPUBBuilder

def get_book_info(markdown_dir: str) -> tuple[str, str]:
    """
    从markdown目录获取书籍信息
    如果目录名为空，使用默认值
    
    Returns:
        (书名, 作者名)的元组
    """
    dir_name = os.path.basename(markdown_dir)
    if not dir_name or dir_name == "markdown":
        return "未命名书籍", "佚名"
    return dir_name, "佚名"

def main():
    # 获取当前工作目录
    base_dir = os.getcwd()
    
    # 设置目录
    input_dir = os.path.join(base_dir, 'markdown')
    temp_dir = os.path.join(base_dir, '.epub_temp')  # 临时目录
    output_dir = os.path.join(base_dir, 'epub')      # 最终输出目录
    
    # 确保输入和输出目录存在
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
        print(f"已创建输入目录: {input_dir}")
        print("请将Markdown文件放入 'markdown' 目录中")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # 清理临时目录
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        
        # 获取书籍信息
        title, author = get_book_info(input_dir)
        print(f"开始转换《{title}》...")
        
        # 初始化转换器和构建器
        converter = MarkdownConverter()
        builder = EPUBBuilder(title, author)
        
        # 创建EPUB基本结构
        builder.create_epub_structure(temp_dir)
        print("已创建EPUB基本结构")
        
        # 转换markdown文件到XHTML
        print("正在转换Markdown文件...")
        converted_files = converter.convert_directory(input_dir, temp_dir)
        
        if not converted_files:
            print("在 'markdown' 目录中没有找到Markdown文件")
            return
        
        # 将转换后的文件添加到EPUB
        print("正在生成EPUB文件结构...")
        for file in converted_files:
            builder.add_item(file)
        
        # 生成content.opf
        content_opf = builder.generate_content_opf(temp_dir)
        print(f"已生成content.opf文件")
        
        # 打包EPUB文件到输出目录
        print("\n正在打包EPUB文件...")
        epub_path = builder.create_epub(temp_dir, output_dir=output_dir)
        
        # 输出转换结果
        print(f"\n转换完成！")
        print(f"共转换 {len(converted_files)} 个文件:")
        for file in converted_files:
            print(f"- {file}")
        print(f"\nEPUB文件已生成: {epub_path}")
        
        # 清理临时文件
        # shutil.rmtree(temp_dir)
        
    except Exception as e:
        print(f"转换过程中出现错误: {str(e)}")
        # 清理临时文件
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise

if __name__ == '__main__':
    main() 
import os
from typing import List, Dict, Optional, Tuple
import uuid
import zipfile
from datetime import datetime
import hashlib

class EPUBBuilder:
    def __init__(self, title: str, author: str = "Unknown"):
        self.title = title
        self.author = author
        self.uuid = str(uuid.uuid4())
        self.items: List[Dict[str, str]] = []
        
    def add_item(self, href: str, media_type: str = "application/xhtml+xml") -> None:
        """
        添加一个内容项到EPUB中
        
        Args:
            href: 内容文件的相对路径
            media_type: 文件的MIME类型
        """
        item_id = f"item_{len(self.items) + 1}"
        self.items.append({
            "id": item_id,
            "href": href,
            "media_type": media_type
        })
        
    def create_epub_structure(self, output_dir: str) -> None:
        """
        创建EPUB所需的基本目录结构和文件
        
        Args:
            output_dir: EPUB文件的输出目录
        """
        # 创建必要的目录
        meta_inf_dir = os.path.join(output_dir, 'META-INF')
        oebps_dir = os.path.join(output_dir, 'OEBPS')
        os.makedirs(meta_inf_dir, exist_ok=True)
        os.makedirs(oebps_dir, exist_ok=True)
        
        # 创建mimetype文件
        self._create_mimetype(output_dir)
        
        # 创建container.xml
        self._create_container_xml(meta_inf_dir)
        
    def _create_mimetype(self, output_dir: str) -> None:
        """
        创建mimetype文件
        
        Args:
            output_dir: 输出目录路径
        """
        mimetype_path = os.path.join(output_dir, 'mimetype')
        with open(mimetype_path, 'w', encoding='utf-8', newline='') as f:
            f.write('application/epub+zip')
    
    def _create_container_xml(self, meta_inf_dir: str) -> None:
        """
        创建container.xml文件
        
        Args:
            meta_inf_dir: META-INF目录路径
        """
        container_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''
        
        container_path = os.path.join(meta_inf_dir, 'container.xml')
        with open(container_path, 'w', encoding='utf-8') as f:
            f.write(container_xml)
    
    def generate_content_opf(self, output_dir: str) -> str:
        """
        生成content.opf文件
        
        Args:
            output_dir: 输出目录路径
            
        Returns:
            生成的content.opf文件路径
        """
        # 修改输出路径到OEBPS目录
        oebps_dir = os.path.join(output_dir, 'OEBPS')
        os.makedirs(oebps_dir, exist_ok=True)
        
        content_opf = f'''<?xml version="1.0" encoding="UTF-8"?>
<package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
        <dc:identifier id="BookId">{self.uuid}</dc:identifier>
        <dc:title>{self.title}</dc:title>
        <dc:creator>{self.author}</dc:creator>
        <dc:language>zh-CN</dc:language>
        <meta property="dcterms:modified">{self._get_current_time()}</meta>
    </metadata>
    
    <manifest>
        {self._generate_manifest_items()}
    </manifest>
    
    <spine>
        {self._generate_spine_items()}
    </spine>
</package>'''
        
        output_path = os.path.join(oebps_dir, 'content.opf')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content_opf)
            
        return output_path
    
    def _generate_manifest_items(self) -> str:
        """生成manifest部分的项目列表"""
        return '\n        '.join(
            f'<item id="{item["id"]}" href="{item["href"]}" media-type="{item["media_type"]}"/>'
            for item in self.items
        )
    
    def _generate_spine_items(self) -> str:
        """生成spine部分的项目列表"""
        return '\n        '.join(
            f'<itemref idref="{item["id"]}"/>'
            for item in self.items
        )
    
    def _get_current_time(self) -> str:
        """获取当前时间的ISO格式字符串"""
        return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    def create_epub(self, temp_dir: str, output_dir: str, epub_name: Optional[str] = None) -> str:
        """
        将EPUB目录打包为.epub文件
        
        Args:
            temp_dir: EPUB文件结构所在的临时目录
            output_dir: 最终EPUB文件的输出目录
            epub_name: 输出的EPUB文件名（可选，默认使用书名）
            
        Returns:
            生成的EPUB文件路径
        """
        # 先验证所需文件是否都存在
        for item in self.items:
            # 使用正斜杠，确保路径格式一致
            file_path = os.path.join(temp_dir, 'OEBPS', item['href']).replace('\\', '/')
            if not os.path.exists(file_path):
                raise ValueError(f"找不到必需的文件: {item['href']}")
        
        if epub_name is None:
            epub_name = f"{self.title}.epub"
        
        # 确保文件名是合法的
        epub_name = self._sanitize_filename(epub_name)
        epub_path = os.path.join(output_dir, epub_name)
        
        # 创建EPUB文件（ZIP格式）
        with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as epub:
            # 首先添加mimetype文件（不压缩）
            mimetype_path = os.path.join(temp_dir, 'mimetype')
            epub.write(mimetype_path, 'mimetype', compress_type=zipfile.ZIP_STORED)
            
            # 添加其他文件
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file == 'mimetype' or file == epub_name:
                        continue
                        
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    epub.write(file_path, arcname)
        
        # 验证生成的EPUB文件
        validation_result = self.validate_epub(epub_path)
        if not validation_result[0]:
            # 如果验证失败，删除已生成的文件
            os.remove(epub_path)
            raise ValueError(f"EPUB文件验证失败: {validation_result[1]}")
            
        return epub_path
    
    def validate_epub(self, epub_path: str) -> Tuple[bool, str]:
        """
        验证EPUB文件的完整性
        
        Args:
            epub_path: EPUB文件路径
            
        Returns:
            (是否验证通过, 错误信息)的元组
        """
        try:
            with zipfile.ZipFile(epub_path, 'r') as epub:
                # 1. 验证ZIP文件完整性
                zip_test = epub.testzip()
                if zip_test is not None:
                    return False, f"ZIP文件损坏，首个错误文件: {zip_test}"
                
                # 2. 验证必需文件是否存在
                required_files = [
                    'mimetype',
                    'META-INF/container.xml',
                    'OEBPS/content.opf'
                ]
                
                for file in required_files:
                    try:
                        epub.getinfo(file)
                    except KeyError:
                        return False, f"缺少必需文件: {file}"
                
                # 3. 验证mimetype文件
                mimetype_content = epub.read('mimetype').decode('utf-8')
                if mimetype_content != 'application/epub+zip':
                    return False, "mimetype文件内容不正确"
                
                # 4. 验证mimetype是否为第一个文件且未压缩
                if epub.filelist[0].filename != 'mimetype' or epub.filelist[0].compress_type != zipfile.ZIP_STORED:
                    return False, "mimetype必须是第一个且未压缩的文件"
                
                # 5. 验证content.opf中列出的文件是否都存在
                content_opf = epub.read('OEBPS/content.opf').decode('utf-8')
                for item in self.items:
                    # 使用正斜杠，确保路径格式一致
                    file_path = os.path.join('OEBPS', item['href']).replace('\\', '/')
                    try:
                        epub.getinfo(file_path)
                    except KeyError:
                        return False, f"content.opf中列出的文件不存在: {file_path}"
                
                # 6. 计算并记录文件校验和
                checksums = {}
                for file in epub.filelist:
                    if file.filename != 'mimetype':  # mimetype已经验证过
                        content = epub.read(file.filename)
                        checksums[file.filename] = hashlib.md5(content).hexdigest()
                
                return True, "验证通过"
                
        except zipfile.BadZipFile:
            return False, "无效的ZIP文件"
        except Exception as e:
            return False, f"验证过程出错: {str(e)}"
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除非法字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        # 替换Windows文件名中的非法字符
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        
        # 确保文件扩展名为.epub
        if not filename.lower().endswith('.epub'):
            filename += '.epub'
            
        return filename 
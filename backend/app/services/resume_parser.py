from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from backend.app.schemas.resume import ResumeParseResponse

try:
    from PyPDF2 import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None


class ResumeParserService:
    TEXT_EXTENSIONS = {'.txt', '.md', '.markdown'}
    SECTION_KEYWORDS = {
        '教育经历': 'education',
        '项目经历': 'project',
        '实习经历': 'internship',
        '技能': 'skills',
        '专业技能': 'skills',
        '校园经历': 'campus',
        '证书': 'certificates',
        '获奖': 'awards',
        '自我评价': 'self_description',
    }

    def parse(self, file_name: str, content: bytes) -> ResumeParseResponse:
        suffix = Path(file_name).suffix.lower()
        if suffix in self.TEXT_EXTENSIONS:
            text = self._decode_text(content)
            return self._build_response(file_name=file_name, file_type=suffix, text=text)
        if suffix == '.docx':
            text = self._parse_docx(content)
            return self._build_response(file_name=file_name, file_type=suffix, text=text)
        if suffix == '.pdf':
            if PdfReader is None:
                return self._unsupported_response(file_name, suffix, '当前环境未安装 PDF 解析依赖，暂时无法解析 PDF 简历。')
            text = self._parse_pdf(content)
            message = '解析成功' if text.strip() else 'PDF 已读取，但未提取到有效文本，可能是扫描版简历。'
            return self._build_response(file_name=file_name, file_type=suffix, text=text, message=message)
        return self._unsupported_response(file_name, suffix, '当前仅支持 txt、md、docx、pdf 简历解析。')

    @staticmethod
    def _unsupported_response(file_name: str, file_type: str, message: str) -> ResumeParseResponse:
        return ResumeParseResponse(
            file_name=file_name,
            file_type=file_type or 'unknown',
            parsed_success=False,
            extracted_text='',
            preview='',
            char_count=0,
            section_hints=[],
            message=message,
        )

    @staticmethod
    def _decode_text(content: bytes) -> str:
        for encoding in ('utf-8', 'utf-8-sig', 'gbk', 'gb18030'):
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        return content.decode('latin-1', errors='ignore')

    @staticmethod
    def _parse_docx(content: bytes) -> str:
        with ZipFile(BytesIO(content)) as archive:
            xml = archive.read('word/document.xml')
        root = ET.fromstring(xml)
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        paragraphs: list[str] = []
        for node in root.findall('.//w:p', ns):
            parts = [item.text for item in node.findall('.//w:t', ns) if item.text]
            paragraph = ''.join(parts).strip()
            if paragraph:
                paragraphs.append(paragraph)
        return '\n'.join(paragraphs)

    @staticmethod
    def _parse_pdf(content: bytes) -> str:
        reader = PdfReader(BytesIO(content))
        pages: list[str] = []
        for page in reader.pages:
            page_text = page.extract_text() or ''
            if page_text.strip():
                pages.append(page_text.strip())
        return '\n'.join(pages)

    def _build_response(self, file_name: str, file_type: str, text: str, message: str = '') -> ResumeParseResponse:
        normalized_text = text.replace('\r\n', '\n').strip()
        final_message = message or ('解析成功' if normalized_text else '未提取到有效文本')
        return ResumeParseResponse(
            file_name=file_name,
            file_type=file_type,
            parsed_success=bool(normalized_text),
            extracted_text=normalized_text,
            preview=normalized_text[:240],
            char_count=len(normalized_text),
            section_hints=self._detect_sections(normalized_text),
            message=final_message,
        )

    def _detect_sections(self, text: str) -> list[str]:
        result: list[str] = []
        for keyword, section in self.SECTION_KEYWORDS.items():
            if keyword in text and section not in result:
                result.append(section)
        return result

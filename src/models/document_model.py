"""
Minimal structured document model for photo storytelling.

This model is independent of output format (HTML/Markdown).
It only contains what we need:
- Headings (H1-H6)
- Paragraphs with inline formatting (bold, italic, text)
- Unordered lists
- Hothash image references

NO:
- No tables
- No code blocks
- No complex formatting
- Not a word processor

DESIGN PHILOSOPHY:
- Pure Python data structures (@dataclass)
- JSON serialization for storage
- Can render to HTML, Markdown, or Qt widgets
- Validates structure (only allowed elements)
"""
from dataclasses import dataclass, field
from typing import List, Union, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json
from enum import Enum


# ==================== INLINE ELEMENTS ====================

class InlineType(Enum):
    """Types of inline text formatting"""
    TEXT = "text"
    BOLD = "bold"
    ITALIC = "italic"
    BOLD_ITALIC = "bold_italic"


@dataclass
class InlineSpan:
    """
    Inline text with optional formatting.
    
    Examples:
        InlineSpan("Hello", InlineType.TEXT)
        InlineSpan("world", InlineType.BOLD)
        InlineSpan("important", InlineType.ITALIC)
    """
    text: str
    style: InlineType = InlineType.TEXT
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "style": self.style.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InlineSpan':
        return cls(
            text=data["text"],
            style=InlineType(data["style"])
        )
    
    def to_html(self) -> str:
        """Render to HTML"""
        text = self.text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        if self.style == InlineType.BOLD:
            return f"<strong>{text}</strong>"
        elif self.style == InlineType.ITALIC:
            return f"<em>{text}</em>"
        elif self.style == InlineType.BOLD_ITALIC:
            return f"<strong><em>{text}</em></strong>"
        else:
            return text
    
    def to_markdown(self) -> str:
        """Render to Markdown"""
        if self.style == InlineType.BOLD:
            return f"**{self.text}**"
        elif self.style == InlineType.ITALIC:
            return f"*{self.text}*"
        elif self.style == InlineType.BOLD_ITALIC:
            return f"***{self.text}***"
        else:
            return self.text


# ==================== BLOCK ELEMENTS ====================

class BlockType(Enum):
    """Types of block-level elements"""
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    IMAGE = "image"


@dataclass
class HeadingBlock:
    """
    Heading (H1-H6).
    
    Examples:
        HeadingBlock(1, [InlineSpan("My Title")])  # H1
        HeadingBlock(2, [InlineSpan("Section")])   # H2
    """
    level: int  # 1-6
    content: List[InlineSpan] = field(default_factory=list)
    
    def __post_init__(self):
        if not 1 <= self.level <= 6:
            raise ValueError(f"Heading level must be 1-6, got {self.level}")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": BlockType.HEADING.value,
            "level": self.level,
            "content": [span.to_dict() for span in self.content]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HeadingBlock':
        return cls(
            level=data["level"],
            content=[InlineSpan.from_dict(s) for s in data["content"]]
        )
    
    def to_html(self) -> str:
        """Render to HTML"""
        content_html = "".join(span.to_html() for span in self.content)
        return f"<h{self.level}>{content_html}</h{self.level}>"
    
    def to_markdown(self) -> str:
        """Render to Markdown"""
        content_md = "".join(span.to_markdown() for span in self.content)
        prefix = "#" * self.level
        return f"{prefix} {content_md}"
    
    def get_text(self) -> str:
        """Get plain text content"""
        return "".join(span.text for span in self.content)


@dataclass
class ParagraphBlock:
    """
    Paragraph with inline formatting.
    
    Example:
        ParagraphBlock([
            InlineSpan("This is "),
            InlineSpan("bold", InlineType.BOLD),
            InlineSpan(" text.")
        ])
    """
    content: List[InlineSpan] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": BlockType.PARAGRAPH.value,
            "content": [span.to_dict() for span in self.content]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParagraphBlock':
        return cls(
            content=[InlineSpan.from_dict(s) for s in data["content"]]
        )
    
    def to_html(self) -> str:
        """Render to HTML"""
        content_html = "".join(span.to_html() for span in self.content)
        return f"<p>{content_html}</p>"
    
    def to_markdown(self) -> str:
        """Render to Markdown"""
        return "".join(span.to_markdown() for span in self.content)
    
    def get_text(self) -> str:
        """Get plain text content"""
        return "".join(span.text for span in self.content)


@dataclass
class ListBlock:
    """
    Unordered list.
    
    Example:
        ListBlock([
            [InlineSpan("First item")],
            [InlineSpan("Second item with "), InlineSpan("bold", InlineType.BOLD)]
        ])
    """
    items: List[List[InlineSpan]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": BlockType.LIST.value,
            "items": [
                [span.to_dict() for span in item]
                for item in self.items
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ListBlock':
        return cls(
            items=[
                [InlineSpan.from_dict(s) for s in item]
                for item in data["items"]
            ]
        )
    
    def to_html(self) -> str:
        """Render to HTML"""
        items_html = ""
        for item in self.items:
            content = "".join(span.to_html() for span in item)
            items_html += f"<li>{content}</li>"
        return f"<ul>{items_html}</ul>"
    
    def to_markdown(self) -> str:
        """Render to Markdown"""
        lines = []
        for item in self.items:
            content = "".join(span.to_markdown() for span in item)
            lines.append(f"- {content}")
        return "\n".join(lines)
    
    def get_text(self) -> str:
        """Get plain text content"""
        return "\n".join(
            "- " + "".join(span.text for span in item)
            for item in self.items
        )


@dataclass
class ImageBlock:
    """
    Image reference via hothash.
    
    Example:
        ImageBlock("abc123def456...", "Sunset in Rome")
    """
    hothash: str
    alt_text: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": BlockType.IMAGE.value,
            "hothash": self.hothash,
            "alt_text": self.alt_text
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImageBlock':
        return cls(
            hothash=data["hothash"],
            alt_text=data.get("alt_text", "")
        )
    
    def to_html(self) -> str:
        """Render to HTML with custom hothash:// protocol"""
        alt = self.alt_text.replace('"', '&quot;')
        return f'<img src="hothash://{self.hothash}" alt="{alt}" />'
    
    def to_markdown(self) -> str:
        """Render to Markdown with custom hothash: protocol"""
        return f"![{self.alt_text}](hothash:{self.hothash})"


# Type alias for any block element
BlockElement = Union[HeadingBlock, ParagraphBlock, ListBlock, ImageBlock]


# ==================== DOCUMENT ====================

@dataclass
class PhotoDocument:
    """
    Complete structured document with metadata.
    
    A document is a list of block elements (headings, paragraphs, lists, images).
    
    Example:
        doc = PhotoDocument(
            title="Summer Vacation 2024",
            description="Our trip to Italy",
            blocks=[
                HeadingBlock(1, [InlineSpan("Rome")]),
                ParagraphBlock([InlineSpan("Beautiful city!")]),
                ImageBlock("abc123...", "Colosseum"),
                HeadingBlock(2, [InlineSpan("Florence")]),
                ParagraphBlock([InlineSpan("Amazing art.")]),
                ImageBlock("def456...", "David statue")
            ]
        )
    """
    title: str
    description: str = ""
    blocks: List[BlockElement] = field(default_factory=list)
    created: datetime = field(default_factory=datetime.now)
    modified: datetime = field(default_factory=datetime.now)
    filepath: Optional[str] = None
    is_modified: bool = False
    
    # ========== Metadata ==========
    
    @property
    def display_name(self) -> str:
        """Name to show in UI"""
        if self.filepath:
            return Path(self.filepath).stem
        return self.title
    
    def get_referenced_hothashes(self) -> List[str]:
        """Extract all hothash references from document"""
        hothashes = []
        for block in self.blocks:
            if isinstance(block, ImageBlock):
                hothashes.append(block.hothash)
        return hothashes
    
    def count_images(self) -> int:
        """Count number of images in document"""
        return sum(1 for b in self.blocks if isinstance(b, ImageBlock))
    
    def count_words(self) -> int:
        """Rough word count (for text blocks only)"""
        total = 0
        for block in self.blocks:
            if isinstance(block, (HeadingBlock, ParagraphBlock)):
                text = block.get_text()
                total += len(text.split())
            elif isinstance(block, ListBlock):
                text = block.get_text()
                total += len(text.split())
        return total
    
    # ========== Serialization ==========
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON export"""
        return {
            "version": "1.0",
            "title": self.title,
            "description": self.description,
            "created": self.created.isoformat(),
            "modified": self.modified.isoformat(),
            "blocks": [self._block_to_dict(block) for block in self.blocks]
        }
    
    def _block_to_dict(self, block: BlockElement) -> Dict[str, Any]:
        """Convert a block to dict (with type discrimination)"""
        return block.to_dict()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PhotoDocument':
        """Deserialize from dictionary loaded from JSON"""
        version = data.get("version", "1.0")
        if version != "1.0":
            raise ValueError(f"Unsupported PhotoDocument version: {version}")
        
        # Parse timestamps
        created = datetime.fromisoformat(data["created"])
        modified = datetime.fromisoformat(data["modified"])
        
        # Parse blocks
        blocks = []
        for block_data in data.get("blocks", []):
            block_type = BlockType(block_data["type"])
            
            if block_type == BlockType.HEADING:
                blocks.append(HeadingBlock.from_dict(block_data))
            elif block_type == BlockType.PARAGRAPH:
                blocks.append(ParagraphBlock.from_dict(block_data))
            elif block_type == BlockType.LIST:
                blocks.append(ListBlock.from_dict(block_data))
            elif block_type == BlockType.IMAGE:
                blocks.append(ImageBlock.from_dict(block_data))
        
        return cls(
            title=data["title"],
            description=data.get("description", ""),
            blocks=blocks,
            created=created,
            modified=modified,
            filepath=None,
            is_modified=False
        )
    
    def save(self, filepath: str):
        """Save document to JSON file"""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        self.modified = datetime.now()
        
        with path.open('w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        
        self.filepath = str(path)
        self.is_modified = False
    
    @classmethod
    def load(cls, filepath: str) -> 'PhotoDocument':
        """Load document from JSON file"""
        path = Path(filepath)
        
        with path.open('r', encoding='utf-8') as f:
            data = json.load(f)
        
        doc = cls.from_dict(data)
        doc.filepath = str(path)
        doc.is_modified = False
        return doc
    
    # ========== Rendering ==========
    
    def to_html(self, include_css: bool = True) -> str:
        """
        Render entire document to HTML.
        
        Args:
            include_css: If True, includes basic CSS styling
            
        Returns:
            Complete HTML string
        """
        html_parts = []
        
        if include_css:
            html_parts.append(self._get_default_css())
        
        html_parts.append('<div class="photo-document">')
        
        for block in self.blocks:
            html_parts.append(block.to_html())
        
        html_parts.append('</div>')
        
        return "\n".join(html_parts)
    
    def _get_default_css(self) -> str:
        """Default CSS styling for HTML output"""
        return """
<style>
.photo-document {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.6;
    color: #333;
}
.photo-document h1 { font-size: 2.5em; margin-top: 0; }
.photo-document h2 { font-size: 2em; margin-top: 1.5em; }
.photo-document h3 { font-size: 1.5em; margin-top: 1.2em; }
.photo-document p { margin: 1em 0; }
.photo-document ul { margin: 1em 0; padding-left: 2em; }
.photo-document img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 2em auto;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
</style>
"""
    
    def to_markdown(self) -> str:
        """
        Render entire document to Markdown.
        
        Returns:
            Markdown string
        """
        md_parts = []
        
        for block in self.blocks:
            md_parts.append(block.to_markdown())
            md_parts.append("")  # Blank line between blocks
        
        return "\n".join(md_parts)
    
    # ========== Helpers ==========
    
    def __str__(self) -> str:
        """String representation"""
        modified_marker = " *" if self.is_modified else ""
        return (f"PhotoDocument('{self.title}'{modified_marker}, "
                f"{len(self.blocks)} blocks, {self.count_images()} images)")
    
    def __repr__(self) -> str:
        """Debug representation"""
        return (f"PhotoDocument(title={self.title!r}, "
                f"blocks={len(self.blocks)}, "
                f"images={self.count_images()}, "
                f"is_modified={self.is_modified})")

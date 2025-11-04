# PhotoDocument Model - Design Document

## 📐 Konsept

En **minimal strukturert dokumentmodell** for foto-historiefortelling som:
- Er **uavhengig av output-format** (ikke låst til Markdown/HTML)
- Har **kun det vi trenger** (overskrifter, paragrafer, lister, hothash-bilder)
- Kan **eksporteres** til HTML, Markdown, eller rendres direkte til Qt widgets
- **Lagres** i JSON (strukturert, validert, versjonskontrollert)

## 🎯 Hvorfor IKKE Markdown?

| **Kriterium** | **Markdown** | **Vår modell** |
|---|---|---|
| **Parsing** | Må parse hver gang | Allerede strukturert |
| **Validering** | Vanskelig | Automatisk (kun gyldige elementer) |
| **Type safety** | Ingen | Python dataclasses |
| **Programmatisk manipulering** | Regex/string munging | Clean API |
| **Output formats** | Fast | Kan rendre til hva som helst |

## 📊 Datastruktur

### Hierarki

```
PhotoDocument
├── title: str
├── description: str
├── created: datetime
├── modified: datetime
└── blocks: List[BlockElement]
    ├── HeadingBlock (H1-H6)
    │   └── content: List[InlineSpan]
    ├── ParagraphBlock
    │   └── content: List[InlineSpan]
    ├── ListBlock
    │   └── items: List[List[InlineSpan]]
    └── ImageBlock
        ├── hothash: str
        └── alt_text: str

InlineSpan
├── text: str
└── style: InlineType (TEXT, BOLD, ITALIC, BOLD_ITALIC)
```

### Element-typer

**Block Elements:**
- `HeadingBlock` - Overskrifter (H1-H6)
- `ParagraphBlock` - Paragrafer med inline formatering
- `ListBlock` - Unordered lists (bullet points)
- `ImageBlock` - Hothash bildereferanser

**Inline Elements:**
- `InlineSpan` - Tekst med style (TEXT, BOLD, ITALIC, BOLD_ITALIC)

**Det er ALT vi støtter.** Ingen tabeller, kodeblokker, eller kompleks formatering.

## 💾 Lagringsformat: JSON

### Eksempel

```json
{
  "version": "1.0",
  "title": "Summer Vacation 2024 - Italy",
  "description": "Our amazing trip",
  "created": "2025-10-30T21:15:09.701529",
  "modified": "2025-10-30T21:15:09.701854",
  "blocks": [
    {
      "type": "heading",
      "level": 1,
      "content": [
        {"text": "Our ", "style": "text"},
        {"text": "Italian", "style": "italic"},
        {"text": " Adventure", "style": "text"}
      ]
    },
    {
      "type": "paragraph",
      "content": [
        {"text": "We visited ", "style": "text"},
        {"text": "Rome", "style": "bold"}
      ]
    },
    {
      "type": "image",
      "hothash": "abc123def456...",
      "alt_text": "Colosseum"
    },
    {
      "type": "list",
      "items": [
        [{"text": "First item", "style": "text"}],
        [{"text": "Second ", "style": "text"}, 
         {"text": "bold", "style": "bold"}, 
         {"text": " item", "style": "text"}]
      ]
    }
  ]
}
```

**Fordeler:**
- ✅ Menneskelig lesbar
- ✅ Diff-vennlig (Git)
- ✅ Enkel å validere
- ✅ Versjonering innebygd
- ✅ Cross-platform (Python, JS, etc.)

## 🔄 Output Formats

### 1. HTML (med CSS)

```python
doc = PhotoDocument.load("vacation.imatext")
html = doc.to_html(include_css=True)
```

**Output:**
```html
<style>
.photo-document { max-width: 800px; margin: 0 auto; ... }
.photo-document h1 { font-size: 2.5em; ... }
.photo-document img { max-width: 100%; border-radius: 8px; ... }
</style>
<div class="photo-document">
  <h1>Our <em>Italian</em> Adventure</h1>
  <p>We visited <strong>Rome</strong></p>
  <img src="hothash://abc123def456..." alt="Colosseum" />
  <ul>
    <li>First item</li>
    <li>Second <strong>bold</strong> item</li>
  </ul>
</div>
```

**Bruksområde:** 
- Web-visning
- Export til nettside
- Email

### 2. Markdown

```python
markdown = doc.to_markdown()
```

**Output:**
```markdown
# Our *Italian* Adventure

We visited **Rome**

![Colosseum](hothash:abc123def456...)

- First item
- Second **bold** item
```

**Bruksområde:**
- Kompatibilitet med andre verktøy
- GitHub/documentation
- Plain text backup

### 3. Qt Widgets (framtidig)

```python
viewer = PhotoDocumentViewer(doc, api_client, cache)
viewer.render()  # Creates QLabel, QTextEdit, etc.
```

**Bruksområde:**
- Native Qt-visning i applikasjonen

## 🛠️ API Eksempler

### Opprett dokument programmatisk

```python
from src.models.document_model import (
    PhotoDocument, HeadingBlock, ParagraphBlock, 
    ImageBlock, InlineSpan, InlineType
)

# Create document
doc = PhotoDocument(
    title="My Trip",
    description="Summer 2024"
)

# Add heading
doc.blocks.append(
    HeadingBlock(1, [InlineSpan("Rome")])
)

# Add paragraph with formatting
doc.blocks.append(
    ParagraphBlock([
        InlineSpan("We visited the "),
        InlineSpan("Colosseum", InlineType.BOLD),
        InlineSpan("!")
    ])
)

# Add image
doc.blocks.append(
    ImageBlock("abc123...", "Colosseum at sunset")
)

# Save
doc.save("/path/to/trip.imatext")
```

### Last og render

```python
# Load from file
doc = PhotoDocument.load("trip.imatext")

# Check metadata
print(doc.title)
print(f"{doc.count_words()} words")
print(f"{doc.count_images()} images")
print(doc.get_referenced_hothashes())

# Render to HTML
html = doc.to_html()
with open("output.html", "w") as f:
    f.write(html)

# Render to Markdown
md = doc.to_markdown()
with open("output.md", "w") as f:
    f.write(md)
```

### Manipulere dokument

```python
# Add new block at specific position
doc.blocks.insert(2, ParagraphBlock([
    InlineSpan("Additional text")
]))

# Find all images
images = [b for b in doc.blocks if isinstance(b, ImageBlock)]

# Replace a hothash
for block in doc.blocks:
    if isinstance(block, ImageBlock):
        if block.hothash == "old_hash":
            block.hothash = "new_hash"

# Mark as modified
doc.is_modified = True
doc.save(doc.filepath)
```

## 📈 Sammenligning med alternativer

| **Feature** | **Markdown** | **HTML** | **Vår modell** |
|---|---|---|---|
| **Lagringsstørrelse** | 🟢 Liten | 🔴 Stor | 🟡 Medium |
| **Type safety** | 🔴 Ingen | 🔴 Ingen | 🟢 Ja |
| **Validering** | 🔴 Vanskelig | 🟡 OK | 🟢 Automatisk |
| **Programmatisk API** | 🔴 Regex | 🟡 DOM | 🟢 Dataclasses |
| **Diff-vennlig** | 🟢 Ja | 🔴 Nei | 🟢 Ja |
| **Menneskelig lesbar** | 🟢 Ja | 🟡 OK | 🟢 Ja |
| **Cross-platform** | 🟢 Ja | 🟢 Ja | 🟢 Ja |
| **Output formats** | 🔴 Fast | 🔴 Fast | 🟢 Fleksibel |

## 🚀 Implementasjonsstatus

### ✅ Ferdig

- [x] Datamodell (`PhotoDocument`, alle block/inline types)
- [x] JSON serialization (save/load)
- [x] HTML rendering med CSS
- [x] Markdown rendering
- [x] Type validation
- [x] Metadata (word count, image count, hothash extraction)
- [x] Test suite (`test_document_model.py`)

### 🔜 Neste steg (for Qt-integrasjon)

- [ ] Qt viewer widget (`PhotoDocumentViewer`)
- [ ] Qt editor widget (`PhotoDocumentEditor`)
- [ ] Drag-drop bilder fra PhotoGridWidget → editor
- [ ] Toolbar for formatering (Bold/Italic/Heading buttons)
- [ ] Live preview (split editor/viewer)
- [ ] Main window integration (ny view)

## 🎨 Fremtidig Qt Widget Arkitektur

```
PhotoDocumentView (Main Window view)
├── Left Panel: PhotoDocumentEditor (QTextEdit-based)
│   ├── Toolbar (Bold, Italic, H1-H3, Insert Image)
│   ├── Text editing area
│   └── Drop zone (accept PhotoModel from gallery)
└── Right Panel: PhotoDocumentViewer (QScrollArea)
    ├── Render blocks as native Qt widgets
    ├── Images loaded via hothash (from cache/API)
    └── Live update when editor changes
```

## 📦 File Extension

**Anbefaling:** `.imatext`

**Hvorfor:**
- `.md` ville vært misvisende (ikke ren markdown)
- `.json` sier ingenting om innhold
- `.imatext` = ImaLink Text Document (tydelig tilhørighet)

**Alternative:**
- `.imalink-doc` (mer beskrivende)
- `.phototxt` (mindre merkevare-spesifikk)

## 🎯 Konklusjon

**JA, dette er veien å gå!**

**Hovedfordeler:**
1. ✅ **Type-safe og validert** - Kun gyldige elementer kan eksistere
2. ✅ **Uavhengig av output** - Kan rendre til HTML, Markdown, Qt widgets
3. ✅ **Enkel API** - Programmatisk oppbygging og manipulering
4. ✅ **Minimal men kraftig** - Fokusert på foto-historiefortelling
5. ✅ **JSON lagring** - Diff-vennlig, cross-platform, versjonskontrollert

**Kritisk suksessfaktor:**
- God Qt editor med toolbar og drag-drop
- Live preview for umiddelbar tilbakemelding
- Hothash-bilder rendres automatisk (fra cache/API)

---

**Filer:**
- Model: `src/models/document_model.py`
- Test: `test_document_model.py`
- Docs: `PHOTO_DOCUMENT_MODEL.md` (dette dokumentet)

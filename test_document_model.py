#!/usr/bin/env python3
"""
Test/demonstration of PhotoDocument model.

Shows how to:
1. Build a structured document programmatically
2. Save to JSON
3. Load from JSON
4. Render to HTML
5. Render to Markdown
"""
from src.models.document_model import (
    PhotoDocument,
    HeadingBlock,
    ParagraphBlock,
    ListBlock,
    ImageBlock,
    InlineSpan,
    InlineType
)


def create_example_document():
    """Create an example document about a vacation"""
    doc = PhotoDocument(
        title="Summer Vacation 2024 - Italy",
        description="Our amazing trip through Rome and Florence"
    )
    
    # Title
    doc.blocks.append(
        HeadingBlock(1, [
            InlineSpan("Our "),
            InlineSpan("Italian", InlineType.ITALIC),
            InlineSpan(" Adventure")
        ])
    )
    
    # Intro paragraph
    doc.blocks.append(
        ParagraphBlock([
            InlineSpan("We spent two weeks exploring the historic cities of "),
            InlineSpan("Italy", InlineType.BOLD),
            InlineSpan(". The architecture, food, and culture were absolutely breathtaking!")
        ])
    )
    
    # Rome section
    doc.blocks.append(
        HeadingBlock(2, [InlineSpan("Rome - The Eternal City")])
    )
    
    doc.blocks.append(
        ParagraphBlock([
            InlineSpan("Rome was our first stop. We visited the Colosseum, the Forum, and threw coins in the Trevi Fountain.")
        ])
    )
    
    # Image 1
    doc.blocks.append(
        ImageBlock("abc123def456789colosseum", "The magnificent Colosseum")
    )
    
    # Highlights list
    doc.blocks.append(
        HeadingBlock(3, [InlineSpan("Rome Highlights")])
    )
    
    doc.blocks.append(
        ListBlock([
            [InlineSpan("Colosseum - "), InlineSpan("incredible", InlineType.BOLD), InlineSpan(" history")],
            [InlineSpan("Vatican Museums - "), InlineSpan("Sistine Chapel", InlineType.ITALIC), InlineSpan(" was stunning")],
            [InlineSpan("Trevi Fountain - made a wish!")],
            [InlineSpan("Best gelato ever at Giolitti")]
        ])
    )
    
    # Image 2
    doc.blocks.append(
        ImageBlock("def456abc789vatican", "Inside the Vatican Museums")
    )
    
    # Florence section
    doc.blocks.append(
        HeadingBlock(2, [InlineSpan("Florence - Renaissance Beauty")])
    )
    
    doc.blocks.append(
        ParagraphBlock([
            InlineSpan("Florence felt like walking through an "),
            InlineSpan("art museum", InlineType.ITALIC),
            InlineSpan(". Every corner had something beautiful to discover.")
        ])
    )
    
    # Image 3
    doc.blocks.append(
        ImageBlock("789ghi012jkl345duomo", "Florence Cathedral (Duomo)")
    )
    
    # Florence list
    doc.blocks.append(
        HeadingBlock(3, [InlineSpan("Florence Must-See")])
    )
    
    doc.blocks.append(
        ListBlock([
            [InlineSpan("Uffizi Gallery - "), InlineSpan("Botticelli's Birth of Venus!", InlineType.BOLD)],
            [InlineSpan("David statue - even more impressive in person")],
            [InlineSpan("Ponte Vecchio - sunset views")],
            [InlineSpan("Mercato Centrale - "), InlineSpan("amazing", InlineType.ITALIC), InlineSpan(" food market")]
        ])
    )
    
    # Image 4
    doc.blocks.append(
        ImageBlock("456mno789pqr012ponte", "Sunset at Ponte Vecchio")
    )
    
    # Conclusion
    doc.blocks.append(
        HeadingBlock(2, [InlineSpan("Final Thoughts")])
    )
    
    doc.blocks.append(
        ParagraphBlock([
            InlineSpan("This trip will stay with us forever. Italy has a way of capturing your heart. We'll "),
            InlineSpan("definitely", InlineType.BOLD_ITALIC),
            InlineSpan(" be back!")
        ])
    )
    
    return doc


def main():
    print("=" * 70)
    print("PhotoDocument Model - Demonstration")
    print("=" * 70)
    print()
    
    # Create document
    print("1. Creating example document...")
    doc = create_example_document()
    print(f"   Created: {doc}")
    print(f"   - {doc.count_words()} words")
    print(f"   - {doc.count_images()} images")
    print(f"   - Referenced hothashes: {doc.get_referenced_hothashes()}")
    print()
    
    # Save to JSON
    print("2. Saving to JSON...")
    json_path = "/tmp/italy_vacation.imatext"
    doc.save(json_path)
    print(f"   Saved to: {json_path}")
    print()
    
    # Show JSON structure (first 500 chars)
    print("3. JSON structure (excerpt):")
    with open(json_path, 'r') as f:
        content = f.read()
        print("   " + content[:500] + "...")
    print()
    
    # Load from JSON
    print("4. Loading from JSON...")
    loaded_doc = PhotoDocument.load(json_path)
    print(f"   Loaded: {loaded_doc}")
    print(f"   - Filepath: {loaded_doc.filepath}")
    print(f"   - Modified: {loaded_doc.is_modified}")
    print()
    
    # Render to HTML
    print("5. Rendering to HTML...")
    html_path = "/tmp/italy_vacation.html"
    html = loaded_doc.to_html(include_css=True)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"   HTML saved to: {html_path}")
    print(f"   - {len(html)} characters")
    print()
    
    # Render to Markdown
    print("6. Rendering to Markdown...")
    md_path = "/tmp/italy_vacation.md"
    markdown = loaded_doc.to_markdown()
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(markdown)
    print(f"   Markdown saved to: {md_path}")
    print(f"   - {len(markdown)} characters")
    print()
    
    # Show markdown excerpt
    print("7. Markdown excerpt:")
    lines = markdown.split('\n')
    for line in lines[:20]:
        print(f"   {line}")
    print("   ...")
    print()
    
    print("=" * 70)
    print("✓ All operations successful!")
    print("=" * 70)
    print()
    print("Summary:")
    print(f"  - JSON file:     {json_path}")
    print(f"  - HTML file:     {html_path}")
    print(f"  - Markdown file: {md_path}")
    print()
    print("You can open the HTML file in a browser to see the rendered document.")
    print()


if __name__ == "__main__":
    main()

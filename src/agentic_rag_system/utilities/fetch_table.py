import fitz  # PyMuPDF
import json
import os


def pdf_bbox_to_fitz_rect(page, bbox):
    """Convert a PDF-style bbox (origin at bottom-left) to a PyMuPDF rect."""
    if not bbox or len(bbox) != 4:
        raise ValueError(f"Invalid bounding box: {bbox}")

    x0, y0, x1, y1 = bbox
    page_height = page.rect.height
    return fitz.Rect(x0, page_height - y1, x1, page_height - y0)


def extract_tables_as_images(pdf_path, json_path, output_dir):
    """
    Extract all tables from PDF using OpenDataLoader JSON
    and save them as PNG images.
    """

    os.makedirs(output_dir, exist_ok=True)

    # Load JSON
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    table_count = 0
    table_metadata = []

    doc = fitz.open(pdf_path)

    def traverse(node):
        nonlocal table_count

        # ----------------------------
        # 1. Detect table node
        # ----------------------------
        if isinstance(node, dict) and node.get("type", "").lower() == "table":
            page_num = node.get("page number", 1) - 1
            bbox = node.get("bounding box")

            if bbox and 0 <= page_num < len(doc):
                try:
                    page = doc[page_num]
                    rect = pdf_bbox_to_fitz_rect(page, bbox)
                    rect = rect & page.rect

                    # Skip invalid boxes
                    if rect.is_empty or rect.width < 10 or rect.height < 10:
                        return

                    # Crop image
                    pix = page.get_pixmap(clip=rect, dpi=200)

                    table_count += 1
                    image_path = os.path.join(
                        output_dir,
                        f"table_p{page_num+1}_{table_count}.png"
                    )

                    pix.save(image_path)

                    print(f"✅ Saved: {image_path}")

                    # Store metadata
                    table_metadata.append({
                        "table_id": table_count,
                        "page": page_num + 1,
                        "bbox": bbox,
                        "image_path": image_path
                    })

                except Exception as e:
                    print(f"⚠️ Error processing table: {e}")

        # ----------------------------
        # 2. Recursive traversal
        # ----------------------------
        if isinstance(node, dict):
            for value in node.values():
                traverse(value)

        elif isinstance(node, list):
            for item in node:
                traverse(item)

    # Start traversal
    traverse(data)

    doc.close()

    print(f"\n🎯 Total tables extracted: {table_count}")

    return table_metadata


# ----------------------------
# Example Usage
# ----------------------------
if __name__ == "__main__":
    pdf_path = r"E:\LLMOps\agentic-rag\data\raw\Employees' Pension Scheme, 1995.pdf"
    json_path = r"E:\LLMOps\agentic-rag\data\json\input.json"
    output_dir = r"E:\LLMOps\agentic-rag\data\processed\tables"

    metadata = extract_tables_as_images(pdf_path, json_path, output_dir)

    # Save metadata (very useful later)
    with open(os.path.join(output_dir, "table_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("\n📦 Metadata saved.")

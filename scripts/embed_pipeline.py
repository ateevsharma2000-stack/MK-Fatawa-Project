"""
Embedding Pipeline for Fatawa Search

Chunks cleaned text files, generates embeddings via OpenAI,
and uploads to Supabase pgvector.

Usage:
  python3 scripts/embed_pipeline.py              # process all files
  python3 scripts/embed_pipeline.py --dry-run     # chunk only, no API calls
"""

import os
import re
import json
import time
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict

BASE_DIR = Path(__file__).resolve().parent.parent
CLEAN_DIR = BASE_DIR / "data" / "text_clean"
CHECKPOINT_FILE = BASE_DIR / "data" / "embed_checkpoint.json"

# ---------------------------------------------------------------------------
# Chunk dataclass
# ---------------------------------------------------------------------------
@dataclass
class Chunk:
    chunk_id: str
    collection: str
    volume: int
    part_no: int
    page_no_start: int
    page_no_end: int
    section_title: str
    text: str
    token_count: int = 0


# ---------------------------------------------------------------------------
# Collection detection
# ---------------------------------------------------------------------------
def detect_collection(filename: str) -> tuple[str, int]:
    """Returns (collection_name, volume_number)."""
    if filename.startswith("majmoo_al_fatawa_of_ibn_bazz_vol_"):
        vol = int(re.search(r"vol_(\d+)", filename).group(1))
        return "ibn_bazz", vol
    elif filename.startswith("en_") and "majmoo_alfatawa_iftaa" in filename:
        vol = int(re.search(r"en_(\d+)", filename).group(1))
        return "iftaa", vol
    elif filename.startswith("fatawa_noor_ala_al-darb"):
        vol = int(re.search(r"en_(\d+)", filename).group(1))
        return "noor_ala_darb", vol
    else:
        return "unknown", 0


# ---------------------------------------------------------------------------
# Page marker parsing
# ---------------------------------------------------------------------------
# Ibn Bazz format: ( Part No: X, Page No: Y)
IBN_BAZZ_PAGE = re.compile(r"\(\s*Part\s+No\s*:\s*(\d+)\s*,\s*Page\s+No\s*:\s*(\d+)\s*\)")
# Iftaa/Noor format: (Part No. X; Page No. Y)
IFTAA_PAGE = re.compile(r"\(Part\s+No\.\s*(\d+)\s*;\s*Page\s+No\.\s*(\d+)\s*\)")


def parse_page_marker(line: str) -> tuple[int, int] | None:
    """Returns (part_no, page_no) or None."""
    m = IBN_BAZZ_PAGE.search(line)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = IFTAA_PAGE.search(line)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def is_page_marker_line(line: str) -> bool:
    stripped = line.strip()
    return bool(IBN_BAZZ_PAGE.fullmatch(stripped) or IFTAA_PAGE.fullmatch(stripped))


# ---------------------------------------------------------------------------
# Token counting (simple whitespace approximation — tiktoken optional)
# ---------------------------------------------------------------------------
def count_tokens(text: str) -> int:
    """Approximate token count. ~0.75 words per token for English."""
    words = len(text.split())
    return int(words / 0.75)


# ---------------------------------------------------------------------------
# Chunking strategies
# ---------------------------------------------------------------------------
FATWA_MARKER = re.compile(r"^Fatwa\s+[Nn]o\.?\s*[({]?\s*\d+", re.IGNORECASE)
QUESTION_MARKER = re.compile(r"^Q\d*:")


def chunk_iftaa(text: str, filename: str, collection: str, volume: int) -> list[Chunk]:
    """Chunk Iftaa collection by Fatwa No. markers."""
    lines = text.split("\n")
    chunks = []
    current_lines = []
    current_title = "Introduction"
    current_part = 0
    current_page_start = 0
    current_page_end = 0
    chunk_idx = 0

    for line in lines:
        page = parse_page_marker(line)
        if page:
            current_part, pg = page
            if current_page_start == 0:
                current_page_start = pg
            current_page_end = pg
            if is_page_marker_line(line):
                continue

        if FATWA_MARKER.match(line.strip()):
            # Save previous chunk
            chunk_text = "\n".join(current_lines).strip()
            if chunk_text and count_tokens(chunk_text) >= 30:
                chunks.append(Chunk(
                    chunk_id=f"{collection}_v{volume:02d}_c{chunk_idx:04d}",
                    collection=collection,
                    volume=volume,
                    part_no=current_part,
                    page_no_start=current_page_start,
                    page_no_end=current_page_end,
                    section_title=current_title,
                    text=chunk_text,
                    token_count=count_tokens(chunk_text),
                ))
                chunk_idx += 1

            current_title = line.strip()
            current_lines = [line]
            current_page_start = current_page_end
        else:
            current_lines.append(line)

    # Last chunk
    chunk_text = "\n".join(current_lines).strip()
    if chunk_text and count_tokens(chunk_text) >= 30:
        chunks.append(Chunk(
            chunk_id=f"{collection}_v{volume:02d}_c{chunk_idx:04d}",
            collection=collection,
            volume=volume,
            part_no=current_part,
            page_no_start=current_page_start,
            page_no_end=current_page_end,
            section_title=current_title,
            text=chunk_text,
            token_count=count_tokens(chunk_text),
        ))

    return chunks


def chunk_noor(text: str, filename: str, collection: str, volume: int) -> list[Chunk]:
    """Chunk Noor ala al-Darb by Q: markers."""
    lines = text.split("\n")
    chunks = []
    current_lines = []
    current_title = "Introduction"
    current_part = 0
    current_page_start = 0
    current_page_end = 0
    chunk_idx = 0
    q_count = 0

    for line in lines:
        page = parse_page_marker(line)
        if page:
            current_part, pg = page
            if current_page_start == 0:
                current_page_start = pg
            current_page_end = pg
            if is_page_marker_line(line):
                continue

        if QUESTION_MARKER.match(line.strip()):
            # Save previous chunk
            chunk_text = "\n".join(current_lines).strip()
            if chunk_text and count_tokens(chunk_text) >= 30:
                chunks.append(Chunk(
                    chunk_id=f"{collection}_v{volume:02d}_c{chunk_idx:04d}",
                    collection=collection,
                    volume=volume,
                    part_no=current_part,
                    page_no_start=current_page_start,
                    page_no_end=current_page_end,
                    section_title=current_title,
                    text=chunk_text,
                    token_count=count_tokens(chunk_text),
                ))
                chunk_idx += 1

            q_count += 1
            current_title = f"Question {q_count}"
            current_lines = [line]
            current_page_start = current_page_end
        else:
            current_lines.append(line)

    chunk_text = "\n".join(current_lines).strip()
    if chunk_text and count_tokens(chunk_text) >= 30:
        chunks.append(Chunk(
            chunk_id=f"{collection}_v{volume:02d}_c{chunk_idx:04d}",
            collection=collection,
            volume=volume,
            part_no=current_part,
            page_no_start=current_page_start,
            page_no_end=current_page_end,
            section_title=current_title,
            text=chunk_text,
            token_count=count_tokens(chunk_text),
        ))

    return chunks


def chunk_ibn_bazz(text: str, filename: str, collection: str, volume: int) -> list[Chunk]:
    """Chunk Ibn Bazz by page markers with max size splitting."""
    lines = text.split("\n")
    chunks = []
    current_lines = []
    current_part = 0
    current_page_start = 0
    current_page_end = 0
    chunk_idx = 0

    for line in lines:
        page = parse_page_marker(line)
        if page:
            current_part, pg = page
            if current_page_start == 0:
                current_page_start = pg
            current_page_end = pg

            # Check if we should split
            current_text = "\n".join(current_lines).strip()
            if count_tokens(current_text) >= 1200:
                if current_text:
                    chunks.append(Chunk(
                        chunk_id=f"{collection}_v{volume:02d}_c{chunk_idx:04d}",
                        collection=collection,
                        volume=volume,
                        part_no=current_part,
                        page_no_start=current_page_start,
                        page_no_end=current_page_end,
                        section_title=f"Part {current_part}, Pages {current_page_start}-{current_page_end}",
                        text=current_text,
                        token_count=count_tokens(current_text),
                    ))
                    chunk_idx += 1
                    current_lines = []
                    current_page_start = pg

            if is_page_marker_line(line):
                continue

        current_lines.append(line)

    # Last chunk
    chunk_text = "\n".join(current_lines).strip()
    if chunk_text and count_tokens(chunk_text) >= 30:
        chunks.append(Chunk(
            chunk_id=f"{collection}_v{volume:02d}_c{chunk_idx:04d}",
            collection=collection,
            volume=volume,
            part_no=current_part,
            page_no_start=current_page_start,
            page_no_end=current_page_end,
            section_title=f"Part {current_part}, Pages {current_page_start}-{current_page_end}",
            text=chunk_text,
            token_count=count_tokens(chunk_text),
        ))

    return chunks


def chunk_file(filepath: Path) -> list[Chunk]:
    """Chunk a single text file based on its collection type."""
    filename = filepath.name
    collection, volume = detect_collection(filename)
    text = filepath.read_text(encoding="utf-8")

    if collection == "iftaa":
        return chunk_iftaa(text, filename, collection, volume)
    elif collection == "noor_ala_darb":
        return chunk_noor(text, filename, collection, volume)
    elif collection == "ibn_bazz":
        return chunk_ibn_bazz(text, filename, collection, volume)
    else:
        # Fallback: chunk by pages
        return chunk_ibn_bazz(text, filename, collection, volume)


# ---------------------------------------------------------------------------
# Embedding + Upload
# ---------------------------------------------------------------------------
def embed_chunks(chunks: list[Chunk], batch_size: int = 100) -> list[list[float]]:
    """Generate embeddings via OpenAI API."""
    from openai import OpenAI
    client = OpenAI()
    all_embeddings = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [c.text[:8000] for c in batch]  # truncate to stay within limits
        try:
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=texts,
            )
            embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(embeddings)
            print(f"  Embedded batch {i // batch_size + 1} ({len(batch)} chunks)")
        except Exception as e:
            print(f"  Error on batch {i // batch_size + 1}: {e}")
            # Retry once after delay
            time.sleep(5)
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=texts,
            )
            embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(embeddings)

    return all_embeddings


def upload_to_supabase(chunks: list[Chunk], embeddings: list[list[float]], batch_size: int = 100):
    """Upload chunks with embeddings to Supabase."""
    from supabase import create_client
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    client = create_client(url, key)

    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i + batch_size]
        batch_embeddings = embeddings[i:i + batch_size]

        rows = []
        for chunk, embedding in zip(batch_chunks, batch_embeddings):
            rows.append({
                "id": chunk.chunk_id,
                "collection": chunk.collection,
                "volume": chunk.volume,
                "part_no": chunk.part_no,
                "page_no_start": chunk.page_no_start,
                "page_no_end": chunk.page_no_end,
                "section_title": chunk.section_title,
                "content": chunk.text[:10000],  # limit content size
                "token_count": chunk.token_count,
                "embedding": embedding,
            })

        client.table("fatawa_chunks").upsert(rows).execute()
        print(f"  Uploaded batch {i // batch_size + 1} ({len(batch_chunks)} rows)")


# ---------------------------------------------------------------------------
# Checkpoint
# ---------------------------------------------------------------------------
def load_checkpoint() -> set:
    if CHECKPOINT_FILE.exists():
        return set(json.loads(CHECKPOINT_FILE.read_text()))
    return set()


def save_checkpoint(processed_files: set):
    CHECKPOINT_FILE.write_text(json.dumps(list(processed_files)))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Fatawa embedding pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Chunk only, no API calls")
    parser.add_argument("--reset", action="store_true", help="Reset checkpoint and reprocess all")
    args = parser.parse_args()

    if args.reset and CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()

    processed = load_checkpoint() if not args.dry_run else set()
    txt_files = sorted(CLEAN_DIR.glob("*.txt"))
    print(f"Found {len(txt_files)} cleaned text files")

    all_chunks = []
    for txt_file in txt_files:
        if txt_file.name in processed:
            print(f"  Skipping {txt_file.name} (already processed)")
            continue

        chunks = chunk_file(txt_file)
        all_chunks.extend(chunks)
        collection, volume = detect_collection(txt_file.name)
        token_total = sum(c.token_count for c in chunks)
        print(f"  {txt_file.name}: {len(chunks)} chunks, ~{token_total} tokens")

    print(f"\nTotal: {len(all_chunks)} chunks")
    total_tokens = sum(c.token_count for c in all_chunks)
    print(f"Total tokens: ~{total_tokens:,}")
    est_cost = total_tokens * 0.00000002  # $0.02 per 1M tokens
    print(f"Estimated embedding cost: ${est_cost:.4f}")

    if args.dry_run:
        # Print chunk size distribution
        sizes = [c.token_count for c in all_chunks]
        print(f"\nChunk size distribution:")
        print(f"  Min: {min(sizes)} tokens")
        print(f"  Max: {max(sizes)} tokens")
        print(f"  Avg: {sum(sizes) // len(sizes)} tokens")
        print(f"  Median: {sorted(sizes)[len(sizes) // 2]} tokens")

        # Show a few sample chunks
        print(f"\n--- Sample chunks ---")
        for c in all_chunks[:3]:
            print(f"\n[{c.chunk_id}] {c.section_title}")
            print(f"  Collection: {c.collection}, Vol: {c.volume}")
            print(f"  Pages: {c.page_no_start}-{c.page_no_end}")
            print(f"  Tokens: {c.token_count}")
            print(f"  Text preview: {c.text[:150]}...")
        return

    # Embed and upload
    print("\nGenerating embeddings...")
    embeddings = embed_chunks(all_chunks)

    print("\nUploading to Supabase...")
    upload_to_supabase(all_chunks, embeddings)

    # Update checkpoint
    for txt_file in txt_files:
        processed.add(txt_file.name)
    save_checkpoint(processed)

    print(f"\nDone! {len(all_chunks)} chunks embedded and uploaded.")


if __name__ == "__main__":
    main()

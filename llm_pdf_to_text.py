import lmstudio as lms
from pdf2image import convert_from_path
from PIL import Image
import os

PDF_PATH = os.environ.get("LLM_PDF_PATH", "data/pdf/Umdah.pdf")
OUTPUT_PATH = os.environ.get("LLM_OUTPUT_PATH", "vision_model_output.txt")
MODEL_ID = os.environ.get("LLM_MODEL_ID", "qwen/qwen2.5-vl-7b")
start_page = int(os.environ.get("LLM_START_PAGE", "0"))
page_batch_size = int(os.environ.get("LLM_BATCH_SIZE", "1"))

# Load just the desired page range
pages = convert_from_path(PDF_PATH)[start_page : start_page + page_batch_size]

# Init model
model = lms.llm(MODEL_ID)

with open(OUTPUT_PATH, "a", encoding="utf-8") as f:
    for offset, page in enumerate(pages):
        page_num = start_page + offset + 1
        print(f"Processing page {page_num}...")

        image_path = f"temp_page_{page_num}.png"
        page.save(image_path)

        # Prepare image for vision model
        image_handle = lms.prepare_image(image_path)

        chat = lms.Chat()
        chat.add_user_message(
            content=(
                "Extract only the printed English text from this scanned manuscript page. "
                "Ignore Arabic, handwritten notes, and the book title in the header. "
                "Return only the clean English content from the main body of the page."
            ),
            images=[image_handle]
        )

        prediction = model.respond(chat)

        # Append to file
        f.write(f"--- Page {page_num} ---\n{prediction.parsed.strip()}\n\n")

        os.remove(image_path)  # optional: remove temp image

print(f"✅ Done. Pages {start_page+1} to {start_page+len(pages)} appended to: {OUTPUT_PATH}")
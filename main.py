import os
import io
import re
import requests
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
from google.cloud import vision
import arabic_reshaper
from bidi.algorithm import get_display
from dotenv import load_dotenv

# === Setup ===
BASE_DIR = os.path.dirname(__file__)
load_dotenv()
APIDAPI_KEY = "7de8933c79msh1fd64c5ca8d35b2p164614jsne6d48908a4d6"
client = OpenAI(api_key="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")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(BASE_DIR, "static-mile-460504-q5-253eccbdfafa.json")
font_path = os.path.join(BASE_DIR, "Noto_Naskh_Arabic", "NotoNaskhArabic-VariableFont_wght.ttf")


# === Translate with OpenL ===
# def translate_openl(text, target="apc"):
#     url = "https://openl-translate.p.rapidapi.com/translate"
#     payload = {"text": text, "target_lang": target}
#     headers = {
#         "content-type": "application/json",
#         "X-RapidAPI-Key": RAPIDAPI_KEY,
#         "X-RapidAPI-Host": "openl-translate.p.rapidapi.com"
#     }
#     try:
#         response = requests.post(url, json=payload, headers=headers)
#         response.raise_for_status()
#         return response.json()["translatedText"]
#     except Exception as e:
#         print(f"Error translating '{text}': {e}")
#         return text
def translate_openl(text):
    print(text)
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You're an expert Arabic manga translator. Translate English text into spoken Palestinian Shami Arabic, making it sound natural, emotional, and true to the characters' voices, like in a Palestinian dub of an anime.\n\n"
                        "Follow these rules:\n"
                        "- Use only Palestinian Levantine (no Modern Standard Arabic).\n"
                        "- Prioritize natural flow and emotional impact over literal translation.\n"
                        "- Use connectors like: إنو، هاد، هيك، شو، ليش، بقلك، بكون، بدنا، الخ.\n"
                        "- Include expressive interjections like: يا زلمة، والله، يي، يلا، واه، ماشي.\n"
                        "- Match masculine/feminine forms properly.\n"
                        "- Keep the tone dynamic—if the scene is urgent, use short, punchy phrases. If it's calm, relax the flow.\n"
                        "- Never add or invent extra content—stick to what's in the text.\n"
                        "- Add punctuation that matches tone (!؟…)\n\n"
                        "Wrong: 'من كان يخبر الجميع أنهم يهاجموننا؟'\n"
                        "Right: 'مين قال للكل إنو كانوا مهاجمينا؟'\n\n"
                        "Return only the Arabic translation—nothing else."
                    )
                },
                {"role": "user", "content": text}
            ],
            temperature=0.7,
        )
        print(response.choices[0].message.content.strip())
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error translating '{text}': {e}")
        return text
# === Google OCR ===
def google_ocr(image_path):
    client = vision.ImageAnnotatorClient()
    with io.open(image_path, "rb") as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.document_text_detection(image=image)

    if response.error.message:
        raise Exception(f"Google OCR error: {response.error.message}")

    raw_boxes = []
    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                para_text = ""
                x_coords, y_coords = [], []
                for word in paragraph.words:
                    word_text = ''.join([symbol.text for symbol in word.symbols])
                    para_text += word_text + " "
                    for vertex in word.bounding_box.vertices:
                        x_coords.append(vertex.x)
                        y_coords.append(vertex.y)
                if para_text.strip():
                    raw_boxes.append({
                        "text": para_text.strip(),
                        "bbox": [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
                    })
    return raw_boxes

# === GPT Grouping Logic ===
import json

def query_gpt_grouping(sentences_with_boxes):
    prompt = (
        "You are a text grouping assistant for manga translation projects. "
        "You will receive a list of OCR-detected sentences from an English manga page, where each item includes a 'text' field (the detected sentence) and a 'bbox' field (the bounding box in [x0, y0, x1, y1] format). "
        "Your task is to group these sentences logically into dialogue bubbles by spatial proximity (within 50 pixels) and natural reading order.\n\n"
        "Apply these **filtering rules BEFORE grouping**:\n"
        "- **Keep all valid English dialogue sentences, even short phrases, single words (like 'shit', 'huh', 'ha ha', 'the idiot who said it'), and cuss words.**\n"
        "- **Only remove clear sound effect onomatopoeias, like 'BANG!', 'SWISH!', 'KRAK!', 'WHOOSH!', 'BZZT!', 'SLAM!'.**\n"
        "- Do NOT remove short English dialogue lines that could appear in speech, such as exclamations ('hey!', 'wow!', 'idiot!') or expressions ('ha ha', 'huh?', 'shit', 'damn').\n"
        "- Keep **all valid English text** that could appear in a conversation.\n\n"
        "After filtering, group the remaining sentences by proximity.\n\n"
        "Return ONLY a valid JSON array of groups, where each group is a list of 0-based indices of the sentences that belong together. No explanation, no extra text, no comments. Example:\n"
        "[[0, 1], [2, 3], [4]]\n\n"
        "Here are the sentences and their bounding boxes:\n"
    )
    
    for i, item in enumerate(sentences_with_boxes):
        prompt += f"{i}. \"{item['text']}\" (bbox: {item['bbox']})\n"

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a JSON output generator for manga sentence grouping."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    try:
        answer = response.choices[0].message.content.strip()
        answer = answer.strip("```json").strip("```").strip()
        groups = json.loads(answer)
        return groups
    except Exception as e:
        print(f"Error parsing GPT response: {e}")
        return [[i] for i in range(len(sentences_with_boxes))]






# === Merge Boxes Based on GPT Groups ===
def merge_boxes(sentences, groups):
    merged = []
    for group in groups:
        combined_text = ' '.join(sentences[i]['text'] for i in group)
        x0 = min(sentences[i]['bbox'][0] for i in group)
        y0 = min(sentences[i]['bbox'][1] for i in group)
        x1 = max(sentences[i]['bbox'][2] for i in group)
        y1 = max(sentences[i]['bbox'][3] for i in group)
        merged.append({'text': combined_text, 'bbox': [x0, y0, x1, y1]})
    return merged

# === Wrap Arabic Text ===
def wrap_text(text, draw, font, max_width):
    words = text.split()
    lines = []
    current_line = ''
    for word in words:
        test_line = word if not current_line else f"{current_line} {word}"
        width = draw.textbbox((0, 0), test_line, font=font)[2]
        if width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines

# === Erase & Draw Text ===
def erase_sentences_from_image(image_path, sentence_boxes, output_path):
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    padding_x, padding_y = 5, 5

    for box in sentence_boxes:
        print(f"🔍 Sentence to translate: {box['text']}")
        x0, y0, x1, y1 = box["bbox"]
        x0 = max(0, x0 - padding_x)
        y0 = max(0, y0 - padding_y)
        x1 += padding_x
        y1 += padding_y
        draw.rectangle([(x0, y0), (x1, y1)], fill="white")

        text = translate_openl(box["text"])
        text = re.sub(r'[A-Za-z]', '', text).strip()
        if not text or text.isspace():
            continue

        font_size = 23
        min_font_size = 18
        chosen_font = None

        while font_size >= min_font_size:
            font = ImageFont.truetype(font_path, font_size)
            wrapped = wrap_text(text, draw, font, x1 - x0)
            #reshaped = [get_display(arabic_reshaper.reshape(line)) for line in wrapped]
            reshaped = wrapped
            line_height = draw.textbbox((0, 0), "Test", font=font)[3]
            total_height = line_height * len(reshaped) + (len(reshaped) - 1) * 4
            if total_height <= (y1 - y0):
                chosen_font = font
                break
            font_size -= 2

        font = chosen_font if chosen_font else ImageFont.truetype(font_path, min_font_size)
        current_y = y0 + ((y1 - y0 - total_height) // 2)
        for line in reshaped:
            line_width = draw.textbbox((0, 0), line, font=font)[2]
            center_x = x0 + ((x1 - x0 - line_width) // 2)
            draw.text((center_x, current_y), line, fill="black", font=font)
            current_y += line_height + 4

    image.save(output_path)
    print(f"Translated and saved: {output_path}")

# === Batch Processor ===
def process_folder(folder_path, output_folder):
    supported_exts = [".jpg", ".jpeg", ".png", ".webp"]
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(folder_path):
        if any(filename.lower().endswith(ext) for ext in supported_exts):
            input_path = os.path.join(folder_path, filename)
            output_path = os.path.join(output_folder, f"translated_{filename}")
            print(f"Processing: {filename}")

            sentence_boxes = google_ocr(input_path)
            print(sentence_boxes)
            groups = query_gpt_grouping(sentence_boxes)
            merged_boxes = merge_boxes(sentence_boxes, groups)

            for box in merged_boxes:
                print(f"Final Grouped Sentence: {box['text']}")

            erase_sentences_from_image(input_path, merged_boxes, output_path)

# === Run ===
input_folder = os.path.join(BASE_DIR, "input")
output_folder = os.path.join(BASE_DIR, "output")
process_folder(input_folder, output_folder)

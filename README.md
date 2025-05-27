📚 Tarjim: Arabic Manga Translator

Tarjim is a Python tool that extracts English text from manga images, translates it into natural spoken Palestinian Shami Arabic, and overlays the translation back onto the images. It uses Google OCR for text detection, OpenAI GPT for translation, and handles Arabic text layout for proper rendering.
🚀 Features

    🖼️ Extracts text from manga panels using Google Vision OCR.

    🧠 Groups sentences into logical dialogue bubbles using GPT-4o.

    🌍 Translates English text into Palestinian Shami Arabic (spoken style, not formal MSA).

    🎨 Overlays translations onto manga images with proper font, alignment, and layout.

    📂 Batch processing of entire folders.

🛠️ Installation

    Clone the repo:

git clone https://github.com/al-layl/tarjim.git
cd tarjim

Install dependencies:

    

    Set up credentials:

        Google Cloud Vision: Place your service account JSON key file and update the path in os.environ["GOOGLE_APPLICATION_CREDENTIALS"].

        OpenAI API: Add your OpenAI API key in the code (client = OpenAI(api_key="...")).

    Add the Arabic font:

        Place the font file (e.g., NotoNaskhArabic-VariableFont_wght.ttf) in a Noto_Naskh_Arabic folder inside the project directory.

📂 Usage

    Create an input folder and add your manga images (.jpg, .jpeg, .png, or .webp).

    Run the script:

python main.py

Translated images will appear in the output folder.

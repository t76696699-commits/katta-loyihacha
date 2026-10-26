import io
import os
import time
import tempfile
from flask import Flask, jsonify, render_template, request, send_file
import google.generativeai as genai
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

app = Flask(__name__)


genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

model = genai.GenerativeModel('gemini-3.5-flash-lite')

words_db = [
    {"id": 1, "term": "augment", "category": "Vocabulary",
     "definition": "To increase or make something greater by adding to it (ko'paytirmoq, kengaytirmoq). Misol: She sought to augment her income."},
    {"id": 2, "term": "benevolent", "category": "Vocabulary",
     "definition": "Well meaning and kindly; generous (saxiy, mehribon, xayrixoh). Misol: A benevolent donor paid for the hospital."},
    {"id": 3, "term": "Candid", "category": "Vocabulary",
     "definition": "Truthful and straightforward; frank (ochiqko'ngil, samimiy). Misol: To be candid, I didn't like the movie."},
    {"id": 4, "term": "Diligent", "category": "Vocabulary",
     "definition": "Having or showing care and conscientiousness in one's work (tirishqoq, mehnatsevar). Misol: He is a diligent student."},
    {"id": 5, "term": "Eloquent", "category": "Vocabulary",
     "definition": "Fluent or persuasive in speaking or writing (notiq, ta'sirli gapiradigan). Misol: Her eloquent speech moved the audience."},
    {"id": 6, "term": "Frivolous", "category": "Vocabulary",
     "definition": "Not having any serious purpose or value (yengil-elpi, be'mani). Misol: Spending money on frivolous things."},
    {"id": 7, "term": "Gargantuan", "category": "Vocabulary",
     "definition": "Enormous; gigantic (juda ulkan, katta). Misol: A gargantuan meal of meat and potatoes."},
    {"id": 8, "term": "Haphazard", "category": "Vocabulary",
     "definition": "Lacking any obvious principle of organization (tartibsiz, tasodifiy). Misol: The books were piled in a haphazard way."},
    {"id": 9, "term": "Innovative", "category": "Vocabulary",
     "definition": "Featuring new methods; advanced and original (innovatsion, yangilik yaratuvchi). Misol: An innovative approach to teaching."},
    {"id": 10, "term": "Juxtapose", "category": "Vocabulary",
     "definition": "Place or deal with close together for contrasting effect (yonma-yon qo'yib solishtirmoq)."},
    {"id": 11, "term": "Kindle", "category": "Vocabulary",
     "definition": "Arouse or inspire (an emotion or idea) (uyg'otmoq, yoqmoq). Misol: To kindle an interest in science."},
    {"id": 12, "term": "Lucid", "category": "Vocabulary",
     "definition": "Expressed Clearly; easy to understand (tiniq, tushunarli, ravshan). Misol: A lucid explanation of the theory."},
    {"id": 13, "term": "Meticulous", "category": "Vocabulary",
     "definition": "Showing great attention to detail; very careful and precise (o'ta sinchkov, puxta)."},
    {"id": 14, "term": "Nostalgia", "category": "Vocabulary",
     "definition": "A sentimental longing for the past (o'tmishni sog'inish, nostalji)."},
    {"id": 15, "term": "Pragmatic", "category": "Vocabulary",
     "definition": "Dealing with things sensibly and realistically (amaliy, real hayotga asoslangan)."},

    {"id": 16, "term": "Fluent", "category": "Speaking",
     "definition": "Able to express oneself easily and articulately (ravon, erkin gaplashadigan)."},
    {"id": 17, "term": "Articulate", "category": "Speaking",
     "definition": "Having or showing the ability to speak fluently and coherently (o'z fikrini aniq va ravshan yetkaza oladigan)."},
    {"id": 18, "term": "To break the ice", "category": "Speaking",
     "definition": "To make people feel more relaxed in a social gathering (suhbatni boshlash, noqulaylikni yo'qotish)."},
    {"id": 19, "term": "Spontaneous", "category": "Speaking",
     "definition": "Performed or occurring as a result of a sudden inner impulse (oldindan rejalashtirilmagan, erkin nutq)."},
    {"id": 20, "term": "Outspoken", "category": "Speaking",
     "definition": "Frank; candid; expressing opinions freely (o'z fikrini ochiq aytadigan)."},
    {"id": 21, "term": "To beat around the bush", "category": "Speaking",
     "definition": "Avoiding the main topic; speaking indirectly (mavzuni chalg'itib, aylanib gapirmoq)."},
    {"id": 22, "term": "Eloquence", "category": "Speaking",
     "definition": "Fluent or persuasive speaking skill (notiqlik san'ati)."},
    {"id": 23, "term": "Hesitate", "category": "Speaking",
     "definition": "Pause before saying or doing something, often due to uncertainty (ikkilanmoq, to'xtalib qolmoq)."},
    {"id": 24, "term": "Persuade", "category": "Speaking",
     "definition": "Induce (someone) to do something through reasoning or argument (ko'ndirmoq, ishontirmoq)."},
    {"id": 25, "term": "To voice an opinion", "category": "Speaking",
     "definition": "To express your thoughts or feelings clearly (o'z fikrini bildirmoq)."},

    {"id": 26, "term": "Present Simple Tense", "category": "Grammar",
     "definition": "Hozirgi oddiy zamon. Doimiy takrorlanadigan harakatlar uchun ishlatiladi. Formula: V1 / V(s/es). Misol: I work every day."},
    {"id": 27, "term": "Present Continuous Tense", "category": "Grammar",
     "definition": "Hozirgi davomiy zamon. Hozirgi paytda sodir bo'layotgan ish-harakat. Formula: am/is/are + V-ing. Misol: She is reading a book."},
    {"id": 28, "term": "Present Perfect Tense", "category": "Grammar",
     "definition": "Hozirgi tugallangan zamon. Natijasi hozir ko'rinib turgan harakat. Formula: have/has + V3. Misol: I have finished my homework."},
    {"id": 29, "term": "Past Simple Tense", "category": "Grammar",
     "definition": "O'tgan oddiy zamon. O'tmishda aniq vaqtda bo'lib o'tgan ish-harakat. Formula: V2 / did. Misol: They went to London yesterday."},
    {"id": 30, "term": "Past Continuous Tense", "category": "Grammar",
     "definition": "O'tgan davomiy zamon. O'tmishda ma'lum bir vaqtda davom etib turgan harakat. Formula: was/were + V-ing."},
    {"id": 31, "term": "Future Simple Tense", "category": "Grammar",
     "definition": "Kelasi oddiy zamon. Kelajakda bajariladigan ishlar. Formula: will + V1. Misol: We will win the match."},
    {"id": 32, "term": "Conditional Sentences (Type 1)", "category": "Grammar",
     "definition": "1-shart ergash gap. Real ehtimol: If + Present Simple, will + V1. Misol: If it rains, I will stay home."},
    {"id": 33, "term": "Passive Voice", "category": "Grammar",
     "definition": "Majhul nisbat. Ega harakatni o'zi bajarmaydi, unga nisbatan bajariladi. Formula: to be + V3."},
    {"id": 34, "term": "Modal Verbs (Can, Must, Should)", "category": "Grammar",
     "definition": "Modal fe'llar. Imkoniyat, majburiyat va maslahat bildirish uchun qo'llaniladi."},
    {"id": 35, "term": "Gerund vs Infinitive", "category": "Grammar",
     "definition": "Fe'lning -ing shakli va 'to' qo'shimchali shaklining gapdagi vazifalari."},

    {"id": 36, "term": "Breathtaking", "category": "Idioms & Phrases",
     "definition": "Astonishing or awe-inspiring in quality (nafasni qisib qo'yadigan darajada ajoyib)."},
    {"id": 37, "term": "A piece of cake", "category": "Idioms & Phrases",
     "definition": "Very easy to do (juda oson, hech gap emas)."},
    {"id": 38, "term": "Break a leg", "category": "Idioms & Phrases",
     "definition": "Good luck (omad tilayman, chiqishda o'zingni ko'rsat)."},
    {"id": 39, "term": "Cost an arm and a leg", "category": "Idioms & Phrases",
     "definition": "To be extremely expensive (juda qimmat turmoq)."},
    {"id": 40, "term": "Hit the sack", "category": "Idioms & Phrases", "definition": "Go to sleep (uxlashga yotmoq)."},
    {"id": 41, "term": "Under the weather", "category": "Idioms & Phrases",
     "definition": "Feeling slightly ill (ozroq tobi qochgan, o'zini yaxshi his qilmayotgan)."},
    {"id": 42, "term": "Once in a blue moon", "category": "Idioms & Phrases",
     "definition": "Very rarely (juda kamdan-kam hollarda)."},
    {"id": 43, "term": "Spill the beans", "category": "Idioms & Phrases",
     "definition": "Reveal a secret (sirni fosh qilmoq, aytib yubormoq)."},
    {"id": 44, "term": "Through thick and thin", "category": "Idioms & Phrases",
     "definition": "Through good times and bad times (har qanday og'ir va yaxshi kunlarda birga)."},
    {"id": 45, "term": "The ball is in your court", "category": "Idioms & Phrases",
     "definition": "It is up to you to make the next decision (endi navbat sizga, qaror o'zingizda)."}
]


def build_and_send_pdf(story, filename, margin=30):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=margin, leftMargin=margin, topMargin=margin,
                            bottomMargin=margin)
    doc.build(story)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')


@app.route('/')
def index():
    return render_template('index.html', words=words_db)


@app.route('/api/ai-define', methods=['POST'])
def ai_define():
    data = request.get_json() or {}
    term = data.get('term', '')
    if not term:
        return jsonify({"error": "So'z kiritilmadi"}), 400

    prompt = f"""
    Sen ingliz tilini o'zbek tiliga tarjima qiluvchi va tushuntiruvchi yordamchisan.
    Quyidagi inglizcha so'z yoki matnni tahlil qil: "{term}"
    Vazifang: O'zbekcha aniq tarjimasi, qoidalari va misollar keltirish.
    """

    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            return jsonify({"definition": response.text})
        except Exception as e:
            err_str = str(e)
            if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str) and attempt < 2:
                time.sleep(3)
                continue
            elif "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                return jsonify({
                    "definition": "API so'rovlar limiti tugadi (429 Error). Iltimos, AI Studio'dan yangi API Key oling va kodingizga qo'ying."}), 429
            return jsonify({"definition": f"Xatolik yuz berdi: {err_str}"}), 500


@app.route('/api/translate-book', methods=['POST'])
def translate_book():
    data = request.get_json() or {}
    text = data.get('text', '')
    if not text:
        return jsonify({"error": "Matn kiritilmadi"}), 400

    prompt = f"""
    Sen professional tarjimon va muharrirsan. Quyidagi inglizcha kitob matnini o'zbek tiliga adabiy, ravon va to'liq tarjima qil:

    "{text}"
    """

    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            return jsonify({"translation": response.text})
        except Exception as e:
            err_str = str(e)
            if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str) and attempt < 2:
                time.sleep(3)
                continue
            elif "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                return jsonify({
                    "translation": "API so'rovlar limiti tugadi (429 Error). Iltimos, birozdan so'ng urinib ko'ring yoki API Key'ni yangilang."}), 429
            return jsonify({"translation": f"Tarjima qilishda xatolik yuz berdi: {err_str}"}), 500


# PDF Kitobni Avtomatik Tarjima qilish va yangi PDF yaratish endpointi
@app.route('/api/translate-pdf', methods=['POST'])
def translate_pdf():
    if 'pdf_file' not in request.files:
        return jsonify({"error": "PDF fayl yuklanmadi"}), 400

    file = request.files['pdf_file']
    if file.filename == '':
        return jsonify({"error": "Fayl tanlanmadi"}), 400

    try:
        reader = PdfReader(file)
        translated_story = []
        styles = getSampleStyleSheet()
        body_style = ParagraphStyle(
            'TranslatedText',
            parent=styles['Normal'],
            fontSize=11,
            leading=16,
            textColor=colors.HexColor('#1e293b')
        )

        # Sahifalarni bittalab o'qib tarjima qilish
        for idx, page in enumerate(reader.pages):
            text = page.extract_text()
            if not text or not text.strip():
                continue

            prompt = f"""
            Quyidagi inglizcha kitob sahifasini o'zbek tiliga ravon, adabiy tarjima qil:
            "{text}"
            """
            response = model.generate_content(prompt)
            translated_text = response.text.replace('\n', '<br/>')

            translated_story.append(Paragraph(f"<b>Sahifa {idx + 1}</b>", styles['Heading2']))
            translated_story.append(Spacer(1, 8))
            translated_story.append(Paragraph(translated_text, body_style))
            translated_story.append(Spacer(1, 15))

        out_name = f"translated_{file.filename}"
        return build_and_send_pdf(translated_story, out_name, margin=36)

    except Exception as e:
        return jsonify({"error": f"PDF-ni tarjima qilishda xatolik: {str(e)}"}), 500


@app.route('/api/words', methods=['POST'])
def add_word():
    data = request.get_json() or {}
    new_id = max([w['id'] for w in words_db], default=0) + 1
    new_item = {
        "id": new_id,
        "term": data.get('term'),
        "category": data.get('category', 'Vocabulary'),
        "definition": data.get('definition')
    }
    words_db.append(new_item)
    return jsonify({"success": True, "word": new_item})


@app.route('/api/words/<int:word_id>', methods=['DELETE'])
def delete_word(word_id):
    global words_db
    words_db = [w for w in words_db if w["id"] != word_id]
    return jsonify({"success": True})


@app.route('/api/chat', methods=['POST'])
def ai_chat():
    data = request.get_json() or {}
    message = data.get('message', '')
    if not message:
        return jsonify({"error": "Xabar kiritilmadi"}), 400

    prompt = f"""
    Sen ingliz tili va dasturlash bo'yicha yordamchi sun'iy intellektchasan. Foydalanuvchining savoliga o'zbek tilida aniq, tushunarli va do'stona javob ber:
    "{message}"
    """

    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            return jsonify({"reply": response.text})
        except Exception as e:
            err_str = str(e)
            if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str) and attempt < 2:
                time.sleep(3)
                continue
            return jsonify({"reply": f"Xatolik yuz berdi: {err_str}"}), 500


@app.route('/api/export-word-pdf/<int:word_id>', methods=['GET'])
def export_single_word_pdf(word_id):
    word = next((w for w in words_db if w["id"] == word_id), None)
    if not word:
        return jsonify({"error": "So'z topilmadi"}), 404

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('T', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#0ea5e9'),
                                 spaceAfter=6)
    cat_style = ParagraphStyle('C', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#64748b'),
                               spaceAfter=15)
    body_style = ParagraphStyle('B', parent=styles['Normal'], fontSize=11, leading=16,
                                textColor=colors.HexColor('#1e293b'))

    clean_definition = word['definition'].replace('\n', '<br/>')
    content_text = f"<b>To'liq Ma'lumot, Qoidalar va Izoh:</b><br/><br/>{clean_definition}"

    table = Table([[Paragraph(content_text, body_style)]], colWidths=[540])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f9ff')),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#38bdf8')),
        ('PADDING', (0, 0), (-1, -1), 16),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story = [
        Paragraph(f"Mavzu/Atama: <b>{word['term']}</b>", title_style),
        Paragraph(f"Bo'lim: <b>{word['category']}</b>", cat_style),
        Spacer(1, 10),
        table
    ]

    return build_and_send_pdf(story, f"{word['term']}_detail.pdf", margin=36)


if __name__ == '__main__':
    app.run(debug=True)

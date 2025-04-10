from flask import Flask, request, jsonify, render_template, send_file, Response
import moviepy.editor as mp
import whisper
import os
import tempfile
import concurrent.futures
from functools import lru_cache

app = Flask(__name__)

# إعدادات
CLIP_DURATION = 7  # مدة كل مقطع مهم بالثواني

# تحميل نموذج Whisper لتحليل التعليق الصوتي (باستخدام الذاكرة المؤقتة)
@lru_cache(maxsize=1)
def load_whisper_model():
    return whisper.load_model("small")

# قاموس الكلمات المفتاحية لكل رياضة
SPORT_KEYWORDS = {
    'Handball': ["goal", "save", "penalty", "fast break", "turnover", "block"],
    'Martial Arts': ["knockout", "submission", "takedown", "punch", "kick", "roundhouse"],
    'Car Racing': ["overtake", "crash", "fastest lap", "pit stop", "final lap", "victory"],
    'Basketball': ["3-pointer", "slam dunk", "fast break", "steal", "assist", "foul"],
    'Football': ["goal", "penalty kick", "shot", "dangerous attack", "corner kick", "yellow card", "red card"]
}

def process_audio_segment(segment, keywords):
    """معالجة قطعة الصوت للبحث عن الكلمات المفتاحية"""
    return any(keyword in segment["text"].lower() for keyword in keywords)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    sport_type = request.form.get('sport_type', 'Football')
    keywords = SPORT_KEYWORDS.get(sport_type, [])

    video_path = None
    audio_path = None
    final_video_path = None

    try:
        # استخدام ملف مؤقت للفيديو
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
            file.save(temp_video.name)
            video_path = temp_video.name

        # استخراج الصوت من الفيديو
        clip = mp.VideoFileClip(video_path)
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            audio_path = temp_audio.name
            clip.audio.write_audiofile(audio_path, logger=None)

        # تحميل النموذج
        model = load_whisper_model()
        result = model.transcribe(audio_path, fp16=False, verbose=None)

        # تحديد اللحظات المهمة
        with concurrent.futures.ThreadPoolExecutor() as executor:
            important_moments = [
                segment["start"] for segment, keep in zip(
                    result["segments"],
                    executor.map(lambda s: process_audio_segment(s, keywords), result["segments"])
                ) if keep
            ]

        if important_moments:
            if len(important_moments) > 10:
                important_moments = important_moments[:10]

            subclips = [
                clip.subclip(max(0, t), min(t + CLIP_DURATION, clip.duration))
                for t in important_moments
            ]

            final_video = mp.concatenate_videoclips(subclips, method="compose")
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_final:
                final_video_path = temp_final.name

            final_video.write_videofile(
                final_video_path,
                codec="libx264",
                audio_codec="aac",
                threads=4,
                preset='fast',
                ffmpeg_params=['-movflags', '+faststart']
            )

            # ✨ إغلاق الكائنات لتحرير الملفات
            final_video.close()
            for sub in subclips:
                sub.close()
            clip.close()

            # إرسال الملف
            response = send_file(
                final_video_path,
                as_attachment=False,
                mimetype='video/mp4',
                download_name=f'{sport_type}_highlights.mp4'
            )

            # حذف الملف النهائي بعد الإرسال
            @response.call_on_close
            def cleanup():
                try: os.unlink(final_video_path)
                except: pass

            # حذف الملفات المؤقتة الأخرى
            try: os.unlink(video_path)
            except: pass
            try: os.unlink(audio_path)
            except: pass

            return response
        else:
            clip.close()
            os.unlink(video_path)
            os.unlink(audio_path)
            return jsonify({"error": "No important moments found."}), 404

    except Exception as e:
        for path in [video_path, audio_path, final_video_path]:
            try:
                if path and os.path.exists(path):
                    os.unlink(path)
            except:
                pass
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(threaded=True, debug=False)

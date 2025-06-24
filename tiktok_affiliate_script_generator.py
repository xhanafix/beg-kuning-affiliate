import streamlit as st
import requests
import json
from math import floor

def calculate_timestamps(video_length, num_scenes):
    timestamps = []
    seconds_per_scene = video_length / num_scenes
    for i in range(num_scenes):
        start_sec = floor(i * seconds_per_scene)
        end_sec = floor((i + 1) * seconds_per_scene) - 1
        if i == num_scenes - 1:
            end_sec = video_length - 1
        start_min, start_s = divmod(start_sec, 60)
        end_min, end_s = divmod(end_sec, 60)
        timestamps.append(f"{start_min:02d}:{start_s:02d} - {end_min:02d}:{end_s:02d}")
    return timestamps

def build_gemini_prompt(product_name, product_category, target_audience, desired_tone, video_length):
    prompt = f"""
Anda adalah penulis skrip TikTok Affiliate yang pakar dalam menghasilkan skrip promosi produk dalam Bahasa Malaysia colloquial. Sila hasilkan skrip video TikTok untuk produk berikut:

Nama Produk: {product_name}
Kategori Produk: {product_category}

Tugas anda:
- Fikirkan dan senaraikan sendiri 3-5 manfaat/ciri utama produk/servis ini (andaian logik berdasarkan nama dan kategori produk, dalam Bahasa Malaysia colloquial, satu per baris).
- Gunakan manfaat/ciri ini sebagai asas untuk membina skrip TikTok.
"""
    if target_audience:
        prompt += f"\nSasaran Audiens: {target_audience}"
    if desired_tone:
        prompt += f"\nNada Dikehendaki: {desired_tone}"
    prompt += f"\nPanjang Video: {video_length} saat\n"
    prompt += """

Arahan penting:
- Skrip mesti dalam Bahasa Malaysia colloquial (bukan formal, gunakan gaya santai dan mesra TikTok).
- Bahagikan skrip kepada beberapa babak (scene) yang logik untuk video TikTok, setiap babak dengan:
    - scene_description: gambaran visual babak (dalam BM colloquial)
    - text_overlay: teks ringkas yang muncul di skrin (dalam BM colloquial)
    - voiceover: narasi suara untuk babak itu (dalam BM colloquial)
- Jangan sebut atau promosikan produk terlarang (senarai: senjata api, dadah, rokok/vape, kandungan dewasa, judi, alat perubatan tidak diluluskan, susu formula bayi, pil/servis kurus yang buat tuntutan melampau).
- Elakkan tuntutan palsu/berlebihan ("100% semulajadi", "dijamin berkesan dalam X hari", "menyembuhkan penyakit"). Jangan buat tuntutan perubatan atau cadangkan produk ganti rawatan profesional. Jangan buat demo harga palsu.
- Jangan bandingkan produk secara negatif dengan pesaing. Fokus pada kelebihan produk ini sahaja.
- Jangan cadangkan penggunaan muzik berhak cipta, logo jenama, gambar selebriti, atau kandungan tidak asli tanpa izin. Anggap pengguna akan pilih elemen bebas royalti.
- Jangan libatkan kanak-kanak dalam skrip.
- Elakkan kandungan sensasi, grafik, mempromosi self-harm, diskriminasi, atau ucapan kebencian.
- Skrip perlu galakkan penonton untuk semak beg kuning (yellow bag) secara tersirat, tanpa sebut "affiliate link" secara langsung.

Format output WAJIB dalam JSON array seperti berikut:
[
  {
    "scene_description": "Deskripsi visual dalam BM colloquial",
    "text_overlay": "Teks atas skrin dalam BM colloquial",
    "voiceover": "Narasi suara dalam BM colloquial"
  },
  ...
]

Pastikan setiap medan diisi dalam Bahasa Malaysia colloquial. Jangan tambah medan lain. Jangan balas apa-apa selain JSON.
"""
    return prompt

def main():
    st.title("🇲🇾 TikTok Affiliate Script Generator (Bahasa Malaysia)")
    st.write("Bina skrip TikTok affiliate yang patuh garis panduan, dalam BM colloquial!")

    # Settings tab: store in session_state
    if 'ai_model' not in st.session_state:
        st.session_state['ai_model'] = 'gemini-2.0-flash'
    if 'api_key' not in st.session_state:
        st.session_state['api_key'] = ''

    tab1, tab2 = st.tabs(["Script Generator", "Settings"])

    with tab2:
        st.subheader("Settings")
        ai_model = st.text_input("AI Model", value=st.session_state['ai_model'], help="e.g. gemini-2.0-flash")
        api_key = st.text_input("Gemini API Key", value=st.session_state['api_key'], type="password")
        save_clicked = st.button("Save Settings")
        if save_clicked:
            st.session_state['ai_model'] = ai_model
            st.session_state['api_key'] = api_key
            st.success("Settings saved to browser session!")
        st.info("Your settings are saved in your browser session (not on server). Reloading the page will keep them unless you clear browser data.")

    with tab1:
        with st.form("tiktok_script_form"):
            product_name = st.text_input("Product Name", max_chars=100)
            product_category = st.text_input("Product Category", max_chars=100)
            target_audience = st.text_input("Target Audience (Optional)", max_chars=100)
            desired_tone = st.text_input("Desired Tone (Optional)", max_chars=100)
            video_length = st.number_input("Video Length (seconds)", min_value=15, max_value=60, value=30)
            submitted = st.form_submit_button("Generate TikTok Script")

        if submitted:
            if not product_name or not product_category:
                st.error("Please fill in all required fields: Product Name and Product Category.")
                return
            prompt = build_gemini_prompt(product_name, product_category, target_audience, desired_tone, video_length)
            ai_model = st.session_state.get('ai_model', 'gemini-2.0-flash')
            api_key = st.session_state.get('api_key', '')
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{ai_model}:generateContent?key={api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "responseSchema": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "scene_description": {"type": "string"},
                                "text_overlay": {"type": "string"},
                                "voiceover": {"type": "string"}
                            },
                            "required": ["scene_description", "text_overlay", "voiceover"]
                        }
                    }
                }
            }
            with st.spinner("Generating script... Please wait! 😉"):
                try:
                    response = requests.post(api_url, headers=headers, data=json.dumps(payload), timeout=60)
                    response.raise_for_status()
                    data = response.json()
                    # Gemini returns the content in a nested structure
                    script_json = None
                    if "candidates" in data and data["candidates"]:
                        content = data["candidates"][0]["content"]["parts"][0]["text"]
                        try:
                            script_json = json.loads(content)
                        except Exception:
                            st.error("Failed to parse AI response as JSON. Please try again.")
                            return
                    else:
                        st.error("No script generated. Please try again.")
                        return
                    if not isinstance(script_json, list) or not all(isinstance(scene, dict) for scene in script_json):
                        st.error("AI response format is invalid. Please try again.")
                        return
                    num_scenes = len(script_json)
                    timestamps = calculate_timestamps(video_length, num_scenes)
                    # Build Markdown table
                    table_md = "| Timestamp | Scene Description | Text Overlay | Voiceover Recommendation |\n"
                    table_md += "|---|---|---|---|\n"
                    for i, scene in enumerate(script_json):
                        table_md += f"| {timestamps[i]} | {scene.get('scene_description','')} | {scene.get('text_overlay','')} | {scene.get('voiceover','')} |\n"
                    st.markdown("### Generated TikTok Script")
                    st.markdown(table_md)
                except requests.exceptions.RequestException as e:
                    st.error(f"API request failed: {e}")
                except Exception as e:
                    st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main() 
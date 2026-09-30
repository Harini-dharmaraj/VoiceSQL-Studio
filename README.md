# ⚡ VoiceSQL Studio • AI Voice-to-SQL Assistant

An intelligent, voice-powered AI database assistant built with **Streamlit**, **OpenAI Whisper**, **Google Gemini**, and **MySQL/SQLite**. Speak naturally in plain English, and the AI translates your voice into SQL, executes it against the database, generates smart charts, and speaks the results aloud.

---

## 🌟 Key Features

* **🎙️ Voice-to-SQL Pipeline**: Real-time microphone capture with noise reduction (Spectral Gating) and OpenAI Whisper speech transcription.
* **🔊 Spoken AI Responses (TTS)**: Summarizes database query results into natural English and speaks them aloud via native speech synthesis and Web Speech API.
* **🧠 Multi-Model Generative AI**:
  * **Google Gemini (Free API)**: Dynamically reads any database schema and generates complex multi-table SQL queries with joins.
  * **OpenAI (GPT-3.5/4)**: High-accuracy enterprise SQL generation.
  * **Offline Rules**: Instant, local query generation without requiring internet or API keys.
* **📊 Smart Visualizations**: Auto-detects numeric and categorical columns to generate Altair bar charts and distributions.
* **🗄️ Multi-Database Support**:
  * **MySQL Server** (XAMPP / Local / Cloud AWS RDS / Aiven).
  * **Embedded SQLite** (`database/demo.db`) for zero-configuration instant local and cloud deployment.
* **📤 Custom CSV Import**: Drag-and-drop any CSV dataset to create and query new tables instantly.
* **🛒 Production E-Commerce Dataset**: Pre-seeded with 50 customers, 30 products, 120 orders, and 225 order items.

---

## 🚀 Quick Start (Local Setup)

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/AI-Voice-to-SQL-Project.git
cd AI-Voice-to-SQL-Project
```

### 2. Create Virtual Environment & Install Dependencies
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Run the Application
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## ☁️ Deployment (Streamlit Community Cloud)

1. Push your repository to **GitHub**.
2. Sign in to [share.streamlit.io](https://share.streamlit.io).
3. Click **"New app"** $\rightarrow$ select your repository $\rightarrow$ branch `main` $\rightarrow$ Main file `app.py`.
4. Click **Deploy!**

---

## 🛠️ Tech Stack

* **Frontend**: Streamlit, Custom Glassmorphism CSS, Altair
* **Speech Recognition**: OpenAI Whisper, SoundDevice, SoundFile, NoiseReduce
* **Speech Synthesis**: Windows SAPI (Offline), HTML5 Web Speech API
* **Database**: MySQL, SQLite, Pandas
* **AI Models**: Google Gemini 1.5 Flash, OpenAI GPT

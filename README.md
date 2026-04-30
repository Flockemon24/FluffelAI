# 🤖 FluffelAI

Eine moderne Chat-Web-App mit Benutzer-Login, Datenbank und KI-Anbindung über OpenRouter.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Flask](https://img.shields.io/badge/Flask-WebApp-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Features

- 🔐 Benutzer-Registrierung & Login
- 💬 Chat mit KI (OpenRouter API)
- 🧠 Chat-Verlauf pro User gespeichert
- 👤 Profilseite
- 🛡️ Admin-Funktion (Datenbank leeren)
- 🍪 Sichere Sessions (HTTPOnly, SameSite)

---

## 🛠️ Tech Stack

- **Backend:** Flask  
- **Datenbank:** SQLite + SQLAlchemy  
- **Auth:** Flask-Login  
- **AI:** OpenRouter API  
- **Frontend:** HTML + Bootstrap  

---

## ⚙️ Installation

### 1. Repository klonen
```bash
git clone https://github.com/Flockemon24/FluffelAI.git
cd FluffelAI
```
### 2. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```
### 3. .env-Datei erstellen
Erstelle eine .env datei im Projekt-Ordner:
```env
OPENROUTER_API_KEY=dein_api_key
SECRET_KEY=irgendein_geheimer_key
```
### 4. App starten und im Browser öffnen
```bash
python main.py
```
Im Browser:
    localhost:5000/register
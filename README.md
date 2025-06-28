# 🚀 groMO Samudaay Connect

> **Intelligent Community Platform for Grassroots Partners**

A cutting-edge web application that intelligently connects grassroots partners (GPs) through AI-powered features including real-time chat analysis, sentiment detection, sales intent analysis, and personalized recommendations.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)
![Socket.IO](https://img.shields.io/badge/Socket.IO-5.3.6-purple.svg)

## ✨ Key Features

- **🤖 AI-Powered Intelligence** - Real-time sentiment analysis, intent detection, sales analysis
- **💬 Smart Chat System** - Real-time messaging, room-based conversations, Q&A system
- **👥 Community Features** - User authentication, leaderboards, room suggestions
- **📊 Analytics & Insights** - Conversation analytics, user metrics, sales intelligence
- **🛡️ Security & Moderation** - Content filtering, user management, data protection

## 🛠️ Tech Stack

- **Backend**: Python, Flask, Flask-SocketIO, SQLAlchemy, MySQL
- **AI/ML**: NLTK, scikit-learn, sentence-transformers, BERTopic, spaCy
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap, Chart.js
- **DevOps**: Gunicorn, Flask-Migrate, pytest, Black, Flake8

## 🚀 Quick Start

### Installation

1. **Clone & Setup**
   ```bash
   git clone https://github.com/trilokdhakad/groMO-samudaay-connect.git
   cd groMO-samudaay-connect
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # macOS/Linux
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   # Create .env file with your settings
   SECRET_KEY=your-secret-key
   DATABASE_URL=mysql+pymysql://username:password@localhost/samudaay_connect
   MAIL_SERVER=smtp.gmail.com
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   GROQ_API_KEY=your-groq-api-key
   ```

3. **Setup Database**
   ```bash
   python init_db.py
   flask db upgrade
   ```

4. **Run Application**
   ```bash
   python run.py
   ```
   Visit `http://localhost:5000`

## 📁 Project Structure

```
groMO-samudaay-connect/
├── app/                          # Main application
│   ├── auth/                     # Authentication
│   ├── chat/                     # Chat functionality
│   ├── gp/                       # Grassroots Partner features
│   ├── static/ & templates/      # Frontend assets
│   ├── models.py                 # Database models
│   ├── text_analysis.py          # AI text analysis
│   ├── sentiment.py              # Sentiment analysis
│   ├── sales_analysis.py         # Sales intent detection
│   └── moderation.py             # Content moderation
├── migrations/                   # Database migrations
├── tests/                        # Test suite
├── config.py                     # Configuration
└── run.py                        # Entry point
```

## 🧪 Testing

```bash
python run_tests.py
# or
pytest tests/test_moderation.py
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request


---

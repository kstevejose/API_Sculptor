# app.py
from src.routes import app

if __name__ == '__main__':
    print("🚀 Starting API Bundler UI...")
    print("✅ Open http://127.0.0.1:5000 in your browser.")
    app.run(port=5000, debug=True)
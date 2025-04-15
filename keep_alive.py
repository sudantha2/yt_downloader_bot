from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "🎉 Telegram bot is running on Render!"

def keep_alive():
    def run():
        app.run(host='0.0.0.0', port=3000)
    Thread(target=run).start()

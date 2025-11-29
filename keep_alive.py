from waitress import serve
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Tao đang chạy bot Discord 24/7" 

def run():
    # --- THÊM DÒNG NÀY ĐỂ NHÌN THẤY LOG ---
    print("🟢 Đang khởi động Web Server Waitress trên cổng 8080...") 
    serve(app, host='0.0.0.0', port=8080) 

def keep_alive():
    t = Thread(target=run)
    t.start()

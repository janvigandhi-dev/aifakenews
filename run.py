import uvicorn
import webbrowser
import threading
import time

def open_browser():
    time.sleep(1.5)
    print("\n[TruthLens] Opening browser at http://127.0.0.1:8000 ...")
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    print("=" * 70)
    print("TruthLens — Explainable AI Fake News Detection System")
    print("“Don’t just detect misinformation. Understand why.”")
    print("=" * 70)
    print("Starting FastAPI Backend & Single-Page Client...")
    print("Web Interface & API available at: http://127.0.0.1:8000")
    print("Interactive API Docs available at: http://127.0.0.1:8000/docs")
    print("=" * 70)
    
    # Open browser automatically on launch
    threading.Thread(target=open_browser, daemon=True).start()
    
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=False)

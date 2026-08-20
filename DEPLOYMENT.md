# 🚀 TruthLens Deployment Guide

TruthLens is fully packaged and ready to deploy to any cloud platform in just a few clicks.

Because FastAPI directly serves the pre-compiled frontend from `frontend/dist/`, **the entire app (Backend + Frontend) runs as a single unified service!**

---

## 🌟 Method 1: Deploy Free on Render (Recommended)

[Render.com](https://render.com) offers a 100% free web service tier that works out-of-the-box with TruthLens.

### Step-by-Step:
1. **Push your code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Deploy TruthLens"
   git branch -M main
   git remote add origin https://github.com/<your-username>/truthlens.git
   git push -u origin main
   ```

2. **Create New Web Service on Render**:
   - Go to [dashboard.render.com](https://dashboard.render.com) and click **"New +"** → **"Web Service"**.
   - Connect your GitHub repository.

3. **Configure Settings**:
   - **Name**: `truthlens` (or your preferred name)
   - **Language / Environment**: `Python`
   - **Branch**: `main`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && python -m backend.models.trainer
     ```
   - **Start Command**:
     ```bash
     uvicorn backend.app:app --host 0.0.0.0 --port $PORT
     ```

4. **Environment Variables**:
   Under **Environment Variables**, add:
   - `GROQ_API_KEY`: `<your_groq_api_key>`
   - `PYTHON_VERSION`: `3.11.8`

5. Click **"Create Web Service"**.
   Your application will be live at `https://truthlens.onrender.com` in 2-3 minutes!

---

## 🚆 Method 2: Deploy on Railway

1. Go to [railway.app](https://railway.app) and sign in with GitHub.
2. Click **"New Project"** → **"Deploy from GitHub repo"**.
3. Select your repository. Railway will detect the `Procfile` and `requirements.txt` automatically.
4. Add the environment variable:
   - `GROQ_API_KEY` = `<your_groq_api_key>`
5. Railway will deploy and generate a public domain (e.g. `https://truthlens.up.railway.app`).

---

## 🐳 Method 3: Deploy with Docker (Any Cloud / VPS / AWS / DigitalOcean)

A multi-stage `Dockerfile` is included in the project root.

### 1. Build Docker Image:
```bash
docker build -t truthlens:latest .
```

### 2. Run Docker Container Locally or on Cloud VPS:
```bash
docker run -d -p 8000:8000 -e GROQ_API_KEY="your_groq_api_key" truthlens:latest
```
Access at `http://localhost:8000` or `http://your-server-ip:8000`.

---

## 🤗 Method 4: Deploy Free on Hugging Face Spaces

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces) and click **"Create new Space"**.
2. Select **"Docker"** as the Space SDK.
3. Push your repository files to the Hugging Face Space repository.
4. Add `GROQ_API_KEY` under Space **Settings** → **Variables and secrets**.
5. The space will automatically build the container and provide a free permanent URL.

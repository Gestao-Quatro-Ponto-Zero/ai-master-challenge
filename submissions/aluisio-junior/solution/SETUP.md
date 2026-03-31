# Setup — Churn Intelligence System

This guide explains how to run the backend and access the API.

---

## 1. Clone the repository

```bash
git clone https://github.com/AluisioJr/ai-master-challenge.git
cd ai-master-challenge/submissions/aluisio-junior/solution
```

---

## 2. Create virtual environment

```bash
python -m venv venv
```

---

## 3. Activate environment

### Windows (PowerShell)

```bash
venv\Scripts\Activate.ps1
```

### Linux / Mac

```bash
source venv/bin/activate
```

---

## 4. Install Python dependencies

```bash
pip install -r requirements.txt
```

The project uses the following key libraries:

- FastAPI (API layer)
- XGBoost (churn prediction)
- SHAP (model explainability)
- Google Gen AI SDK (`google-genai`) for Gemini integration

Ensure all dependencies are installed before running the API.

---

## 5. Configure environment variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_api_key_here
```

This key is required for the Gemini AI integration.

### Optional: Kaggle dataset download

If you want to download the dataset directly from Kaggle, configure:

```env
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_key
```

Install Kaggle CLI:

```bash
pip install kaggle
```

Place your credentials in:

```text
~/.kaggle/kaggle.json
```

> Note: This step is optional. The project can run using the dataset already included.

---

## 6. Run the API locally

```bash
uvicorn api.main:app --reload
```

---

## 7. Access API documentation

### Local

http://127.0.0.1:8000/docs

### Public (ngrok)

https://postoral-stan-salamandrine.ngrok-free.dev/docs

---

## 8. Expose API with ngrok (optional)

This project uses the **ngrok Agent CLI**, which must be installed separately.

After installation, run:

```bash
ngrok http 8000
```

This allows external access to the API (used for frontend integration).

---

## 9. Project structure

```text
solution/
├── api/
├── services/
├── data/
├── requirements.txt
└── SETUP.md
```

---

## Notes

- Dataset is based on RavenStack (synthetic data)
- Model retrains on each API start (can be optimized in production)
- LTV is calculated as a proxy (not real lifetime billing)
- API is designed for integration with frontend and AI layer

---

## Expected result

After running the API, you should be able to access:

- Local: http://127.0.0.1:8000/docs
- Public: https://postoral-stan-salamandrine.ngrok-free.dev/docs

All endpoints should be available and operational.

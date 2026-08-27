from fastapi import FastAPI

app = FastAPI(title="RazorRecover")

@app.get("/")
def home():
    return {"message": "RazorRecover API is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}
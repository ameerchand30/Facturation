from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    print("Root endpoint accessed")
    return {"message": "Welcome to the Facturation API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

print("FastAPI application is running...")
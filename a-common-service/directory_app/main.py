from fastapi import FastAPI
from mangum import Mangum
  
# Initialise the app
app = FastAPI()

@app.get("/")
async def root(q: str):
    return {"endpoint": f"{q}"}

lambda_handler = Mangum(app)
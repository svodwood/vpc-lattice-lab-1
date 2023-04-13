from fastapi import FastAPI
from mangum import Mangum
  
# Initialise the app
app = FastAPI()

@app.get("/green-team")
async def go_green():
    return {'endpoint': 'green'}

@app.get("/blue-team")
async def go_blue():
    return {'endpoint': 'blue'}

lambda_handler = Mangum(app)
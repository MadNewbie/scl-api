import uvicorn
from fastapi import FastAPI
from .routers import auth, stock, booking

app = FastAPI()

app.include_router(auth.router)
app.include_router(stock.router)
app.include_router(booking.router)

@app.get("/")
async def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.1.7", port=80)
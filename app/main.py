import uvicorn
from fastapi import FastAPI
from .routers import auth, stock, booking
from pydantic_settings import BaseSettings
import os

class AppSetting(BaseSettings):
    UOM_DEFAULT: str = os.getenv("UOM_DEFAULT")
    SLOC_DEFAULT: str = os.getenv("SLOC_DEFAULT")
    ALL_UOM: bool = os.getenv("ALL_UOM")
    ACCESS_OTHER_SLOC: bool = os.getenv("ACCESS_OTHER_SLOC")

app = FastAPI()

app.state.settings = AppSetting()

app.include_router(auth.router)
app.include_router(stock.router)
app.include_router(booking.router)

@app.get("/")
async def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.1.7", port=80)
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, status
from datetime import datetime, timezone
from ..models import token as MToken
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..database import get_db
import jwt
from ..errors import authError400, generalError404

class RequestGenerateModel(BaseModel):
    client_id: str=Field(alias="client-id")
    client_secret: str=Field(alias="client-secret")
    grant_type: str

class Token(BaseModel):
    class Config:
        orm_mode = True

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={status.HTTP_404_NOT_FOUND:generalError404()}
)

@router.post("/token")
async def generate_token(request: RequestGenerateModel, db:Session = Depends(get_db), status_code = status.HTTP_200_OK):
    if (request.grant_type == 'client_credentials') :
        now = int(datetime.now(timezone.utc).timestamp())
        timeToExpire = 900
        exp = now + timeToExpire
        secret = request.client_secret
        payload = {
            "client_id": request.client_id,
            "exp": exp,
            "iat": now
        }
        print(payload)
        token = jwt.encode(payload,secret,algorithm="HS256")
        token_type = "Bearer"
        # cek apakah user sudah punya token sebelumnya
        statement = select(MToken.Token).where(MToken.Token.user_id == request.client_id, MToken.Token.secret == request.client_secret)
        
        userToken = db.scalars(statement=statement).first()
        # print(f"userToken: {userToken.token}, new token: {token}")

        if userToken is None :
            modelToken =  MToken.Token(user_id=request.client_id, secret=request.client_secret, token=token)
            db.add(modelToken)
            db.commit()
        else:
            userToken.token = token
            db.commit()
        return {"access_token": token, "expires_in": timeToExpire, "token_type": token_type}
    else :
        return authError400()
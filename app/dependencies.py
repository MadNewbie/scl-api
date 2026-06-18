import jwt
from typing import Annotated
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.sql import text
from sqlalchemy.orm import Session
from .database import get_db


def check_token_header(authorization: Annotated[str, Header()], db: Session = Depends(get_db)):
    token = authorization[7:]
    stmtUser = text("SELECT * FROM public.fc_api_csbs_get_user_secret_by_token(:token)")
    secret = db.execute(stmtUser,{"token": token}).mappings().all()[0].secret
    dbUser = db.execute(stmtUser,{"token": token}).mappings().all()[0].user_id
    # print(secret, dbUser)
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"],options={
            "verify_exp": True,
            "require": ["exp"]
        })
        user = payload.get("client_id")
        if (user != dbUser):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail = {
                    "code": 401,
                    "status": "Unauthorized",
                    "external_code": -100011,
                    "external_desc": "Authentication Fail",
                    "errors": ["Invalid Token"]
                }
            )
        # logging
    except jwt.ExpiredSignatureError as e:
        print("Expired", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = {
                "code": 401,
                "status": "Unauthorized",
                "external_code": -100011,
                "external_desc": "Authentication Fail",
                "errors": ["Invalid Token"]
            }
        )
    except jwt.InvalidSignatureError as e:
        print("Invalid", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = {
                "code": 401,
                "status": "Unauthorized",
                "external_code": -100011,
                "external_desc": "Authentication Fail",
                "errors": ["Invalid Token"]
            }
        )
    except jwt.DecodeError as e:
        print("Decode Error:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = {
                "code": 401,
                "status": "Unauthorized",
                "external_code": -100011,
                "external_desc": "Authentication Fail",
                "errors": ["Invalid Token"]
            }
        )
    except Exception as e:
        print("Exception:", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail = {
                "code": 401,
                "status": "Unauthorized",
                "external_code": -100011,
                "external_desc": "Authentication Fail",
                "errors": ["Invalid Token"]
            }
        )

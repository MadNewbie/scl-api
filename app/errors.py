from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

def authError400():
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, 
        content=jsonable_encoder({
            "error":"invalid_request",
            "error_description": "The request is missing a required parameter, includes an invalid parameter value, includes a parameter more than once, or is otherwise malformed."
        })
    )

def authError401():
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=jsonable_encoder({
            "error":"unauthorized",
            "error_description":"Client secret or ID invalid"
        })
    )

def generalError404():
    return {
        "code":404,
        "description":"Not Found"
    }

def generalError409():
    return {
        "code":409,
        "description":"WHM technical issue"
    }

def error401():
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=jsonable_encoder({
            "Response":{
                "code":"401",
                "description":"No Authorization"
            }
        })
    )

def error405():
    return JSONResponse(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        content=jsonable_encoder({
            "Response":{
                "code":"405",
                "description":"Plant Code Invalid"
            }
        })
    )

def error406():
    return JSONResponse(
        status_code=status.HTTP_406_NOT_ACCEPTABLE,
        content=jsonable_encoder({
            "Response":{
                "code":"406",
                "description":"Stock Location Invalid"
            }
        })
    )

def error413(data):
    return JSONResponse(
        status_code=status.HTTP_406_NOT_ACCEPTABLE,
        content=jsonable_encoder({
            "stock-booking-id":"null",
            "product": data.productDict,
            "Response":{
                "code":"413",
                "description":f"{data.productCodeList} Insufficient Stock"
            }
        })
    )

def error414():
    return JSONResponse(
        status_code=status.HTTP_414_URI_TOO_LONG,
        content=jsonable_encoder({
            "Response":{
                "code":"414",
                "description":"Stock Booking ID invalid"
            }
        })
    )

def error416():
    return JSONResponse(
        status_code=status.HTTP_416_RANGE_NOT_SATISFIABLE,
        content=jsonable_encoder({
            "Response":{
                "code":"416",
                "description":"Booking ID has been cancelled before"
            }
        })
    )
from pydantic import BaseModel, Field
from datetime import datetime,date
from fastapi import APIRouter,Depends, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from ..errors import generalError404, error405, error406, error414, error416
from ..database import autocommit_db, get_db
from ..dependencies import check_token_header
import random
import string
import json

class RequestCustomer(BaseModel):
    code: str
    owner: str
    name: str

class RequestCancelCustomer(BaseModel):
    code: str
    owner: str

class RequestProduct(BaseModel):
    code: str
    qty_booked: int = Field(alias="qty-booked")

class RequestBooking(BaseModel):
    customer: RequestCustomer
    product: list[RequestProduct]
    reference_code: str = Field(alias="reference-code")
    source_application: str = Field(alias="source-application")
    uom_level: str
    quantity_level: str = Field(default=None)
    delivery_time: datetime
    customer_type: str = Field(default=None)
    plant_code: str
    stock_location: str
    courier_code: str

class RequestCancelBooking(BaseModel):
    customer: RequestCancelCustomer
    reference_code: str = Field(alias="reference-code")
    stock_booking_id: str = Field(alias="stock-booking-id")
    plant_code: str
    stock_location: str
    courier_code: str = Field(default=None)

def formatProductCode(product_code, db_res, uom):
    default_product_codes = list(map(lambda x: {"code": x.code, "qty-available":0}, product_code))

    dict_db_pack = {item['code']:item['qty-available-pack'] for item in db_res}
    dict_db_slop = {item['code']:item['qty-available-slop'] for item in db_res}
    dict_db_bal = {item['code']:item['qty-available-bal'] for item in db_res}
    dict_db_box = {item['code']:item['qty-available-box'] for item in db_res}

    match uom.lower():
        case "pack":
            result = list(map(lambda x:{
                "code": x['code'],
                "qty-available": dict_db_pack.get(x['code'], 0)
                },default_product_codes))
        case "slop":
            result = list(map(lambda x:{
                "code": x['code'],
                "qty-available": dict_db_slop.get(x['code'], 0)
                },default_product_codes))
        case "bal":
            result = list(map(lambda x:{
                "code": x['code'],
                "qty-available": dict_db_bal.get(x['code'], 0)
                },default_product_codes))
        case "box":
            result = list(map(lambda x:{
                "code": x['code'],
                "qty-available": dict_db_box.get(x['code'], 0)
                },default_product_codes))

    return result

router = APIRouter(
    responses={status.HTTP_404_NOT_FOUND: generalError404()}
)

@router.post("/booking", dependencies=[Depends(check_token_header)])
async def create_booking(request: RequestBooking, db: Session = Depends(get_db), db_autocommit: Session = Depends(autocommit_db), status_code= status.HTTP_200_OK):
    if request.plant_code == "":
        return error405()
    
    if not request.stock_location.isdigit():
        return error406()
    
    # cek wh
    stmt = text("SELECT * FROM public.fc_api_csbs_get_warehouse_sloc()")
    all_warehouse_sloc = db.execute(stmt).mappings().all()
    product_codes = list(map(lambda x: x.code,request.product))
    warehouse_sloc = list(filter(lambda data: (data.wh_code == request.plant_code) and (data.sloc_name == request.stock_location), all_warehouse_sloc))
    product_with_book_qty = list(map(lambda x: {"code":x.code,"qty":x.qty_booked},request.product))

    if warehouse_sloc is None or warehouse_sloc == [] :
        return error406()
    else :
        stmtStock = text("SELECT * FROM public.fc_api_csbs_check_stock(:items,:wh,:sloc)")
        raw_product_stock_from_db = db.execute(stmtStock,{"items": product_codes, "wh": warehouse_sloc[0].wh_code, "sloc": warehouse_sloc[0].sloc_name}).mappings().all()
        db_product_codes = list(map(lambda x: {
                    "product-id":x.product_id,
                    "code":x.code, 
                    "qty-available-pack":x.qty_available_pack,
                    "qty-available-slop":x.qty_available_slop,
                    "qty-available-bal":x.qty_available_bal,
                    "qty-available-box":x.qty_available_box,
                },raw_product_stock_from_db))
        available_product_on_wh = formatProductCode(request.product, db_product_codes,request.uom_level)

        dict_available_product_on_wh = {item['code']: item['qty-available'] for item in available_product_on_wh}
        dict_available_product_on_wh_product_id = {item['code']: item['product-id'] for item in db_product_codes}

        # cek stok apakah ada yg tidak memenuhi
        check_fulfilled = True
        unfulfilled_product_code = []
        booked_product_id = []
        res_product_codes = []

        for item in product_with_book_qty:
            if dict_available_product_on_wh.get(item["code"]) < item["qty"] :
                unfulfilled_product_code.append(item["code"])
                res_product_codes.append({
                    "availability": False,
                    "code": item["code"],
                    "qty-available": dict_available_product_on_wh.get(item["code"])
                })
                check_fulfilled = False
            else :
                booked_product_id.append({
                    "product_id": dict_available_product_on_wh_product_id.get(item["code"]),
                    "qty-order": item["qty"]
                })
                res_product_codes.append({
                    "availability": True,
                    "code": item["code"],
                    "qty-order": item["qty"]
                })

        if check_fulfilled :
            randomize_string = "".join(random.choices(string.ascii_uppercase+string.digits,k=5))
            booking_code = "SB"+date.today().strftime('%Y%m%d')+randomize_string
            stmtAddBooking = text("SELECT * FROM public.fc_api_csbs_add_booking(:wh_code, :sloc, :customer_code, :reference_code, :booking_code, :uom_level, :header_quantity, :details)")
            try:
                raw_booking = db_autocommit.execute(stmtAddBooking,{
                    "wh_code":warehouse_sloc[0].wh_code,
                    "sloc": warehouse_sloc[0].sloc_name,
                    "customer_code": request.customer.code,
                    "reference_code": request.reference_code,
                    "booking_code": booking_code,
                    "uom_level": request.uom_level,
                    "header_quantity": 1000,
                    "details": json.dumps(booked_product_id)
                }).mappings().all()
                print(raw_booking)
            except SQLAlchemyError as e:
                print(e)
            except IntegrityError as e:
                print(e)
            return {
                "stock-booking-id": raw_booking[0].booking_code,
                "product": res_product_codes,
                "Response": {
                    "code": "00",
                    "description": "Success"
                }
            }
        else:
            str_product_code_not_fulfilled = ", ".join(unfulfilled_product_code)
            return JSONResponse(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                content= jsonable_encoder({
                "stock-booking-id": "null",
                "product": res_product_codes,
                "Response": {
                        "code": "413",
                        "description": f'{str_product_code_not_fulfilled} Insufficient Stock'
                    }
                })
            )
        
@router.post("/cancel-booking", dependencies=[Depends(check_token_header)])
async def cancel_booking(request: RequestCancelBooking, db: Session = Depends(get_db), db_autocommit: Session = Depends(autocommit_db), status_code = status.HTTP_200_OK):
    stock_booking_id = request.stock_booking_id
    stmt_get_stock_booking = text("SELECT * FROM public.fc_api_csbs_get_booking_stock(:booking_code)")
    raw_stock_booking = db.execute(stmt_get_stock_booking, {
        "booking_code": stock_booking_id
    }).mappings().all()

    # cek jika kode booking tak valid
    if raw_stock_booking == []:
        return error414()
    
    stock_booking = raw_stock_booking[0]
    print(stock_booking)
    # cek status booking tidak aktif
    if stock_booking.status != 1 or not(stock_booking.is_active):
        return error416()
    
    ref_code = request.reference_code
    stmt_cancel = text("SELECT * FROM public.fc_api_csbs_cancel_booking(:booking_code, :reference_code)")
    raw_cancel_booking = db_autocommit.execute(stmt_cancel, {
        "booking_code": stock_booking.booking_code,
        "reference_code": ref_code
    }).mappings().all()
    cancel_booking = raw_cancel_booking[0]
    print(cancel_booking)

    return {
        "reference-code": cancel_booking.reference_code,
        "Response": {
            "code" : "00",
            "description": "Success"
        }
    }

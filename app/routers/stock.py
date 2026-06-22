from pydantic import BaseModel, Field
from fastapi import APIRouter,Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from ..dependencies import check_token_header
from ..errors import generalError404, error405, error406, generalError409
from ..database import get_db

class RequestCustomerModel(BaseModel):
    code: str
    owner: str

class RequestProductModel(BaseModel):
    code: str

class RequestCheckStockModel(BaseModel):
    customer: RequestCustomerModel
    product: list[RequestProductModel]
    source_application: str = Field(alias="source-application")
    plant_code: str
    stock_location: str
    courier_code: str
    uom_level: str
    quantity_level: str
    customer_type: str

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
    tags=["stock"],
    responses={status.HTTP_404_NOT_FOUND:generalError404()}
)

@router.post("/check-stock", dependencies=[Depends(check_token_header)])
async def check_stock(request: RequestCheckStockModel, db:Session = Depends(get_db), status_code=status.HTTP_200_OK):
    if request.plant_code == "":
        return error405()
    
    if not request.stock_location.isdigit():
        return error406()
    
    # cek wh
    stmt = text("SELECT * FROM public.fc_api_csbs_get_warehouse_sloc()")
    all_warehouse_sloc = db.execute(stmt).mappings().all()
    product_codes = list(map(lambda x: x.code,request.product))
    warehouse_sloc = list(filter(lambda data: (data.wh_code == request.plant_code) and (data.sloc_name == request.stock_location), all_warehouse_sloc))

    if warehouse_sloc is None or warehouse_sloc == [] :
        return error406()
    else :
        stmtStock = text("SELECT * FROM public.fc_api_csbs_check_stock(:items,:wh,:sloc)")
        raw_product_stock_from_db = db.execute(stmtStock,{"items": product_codes, "wh": warehouse_sloc[0].wh_code, "sloc": warehouse_sloc[0].sloc_name}).mappings().all()
        # print(raw_product_stock_from_db)
        db_product_codes = list(map(lambda x: {
                    "code":x.code, 
                    "qty-available-pack": x.qty_available_pack,
                    "qty-available-slop": x.qty_available_slop,
                    "qty-available-bal": x.qty_available_bal,
                    "qty-available-box": x.qty_available_box,
                },raw_product_stock_from_db))
        res_product_codes = formatProductCode(request.product, db_product_codes, request.uom_level)

        return {
            "product": res_product_codes,
            "Response": {
                "code": "00",
                "description": "Success"
            },
        }
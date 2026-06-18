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

def formatProductCode(product_code, db_res):
    default_product_codes = list(map(lambda x: {"code": x.code, "qty-available":0}, product_code))

    dict_db = {item['code']:item['qty-available'] for item in db_res}

    result = list(map(lambda x:{
        "code": x['code'],
        "qty-available": dict_db.get(x['code'], x['qty-available'])
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
        db_product_codes = list(map(lambda x: {
                    "code":x.code, 
                    "qty-available":x.qty_available
                },raw_product_stock_from_db))
        res_product_codes = formatProductCode(request.product, db_product_codes)

        return {
            "product": res_product_codes,
            "Response": {
                "code": "00",
                "description": "Success"
            },
        }
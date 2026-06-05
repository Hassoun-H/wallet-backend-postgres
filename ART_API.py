from fastapi import FastAPI,HTTPException,Depends
from fastapi.security import HTTPBearer
from decimal import Decimal
from pydantic import BaseModel,Field
from typing import Optional
from typing import Literal
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime,date
import database_server
app=FastAPI()
security_bearer=HTTPBearer()
conn=psycopg2.connect(**database_server.connection_params)
cursor=conn.cursor(cursor_factory=RealDictCursor)
database_server.creat_table(cursor)
conn.commit()
class LoginRequest(BaseModel):
    id_employee: int
    plain_password:str
class CreateAccount(BaseModel):
    username:str
    numberphone:str
    national_id:str
    mother_name:str
    full_name:str
class TransformationMoney(BaseModel):
    sender_id:int
    sender_pin:str
    amount:Decimal
    account_id:Optional[int]=None
    number_phone:Optional[str]=None
    national_id:Optional[str]=None
class CreateEmployee(BaseModel):
    full_name:str
    password_hash:str
class Withdrawal(BaseModel):
    id_customer:int
    customer_pin:str
    national_customer:str
    amount:Decimal
class TopUpBalance(BaseModel):
    account_id:Optional[int]=None
    national_id:Optional[str]=None
    number_phone:Optional[str]=None
    amount:Decimal
#**************************************************************************************************************************************************************************************************************************************************************************
@app.post("/create account")
def create(data: CreateAccount, token_data=Depends(security_bearer)):
    result=database_server.create_an_account(cursor,token_data.credentials,data.username,data.numberphone,data.national_id,data.mother_name,data.full_name)
    if result is None:
        raise HTTPException(status_code=403,detail="you do not have permission to create an account")
    conn.commit()
    return result
@app.post("/Login")
def Login(data: LoginRequest):
    result=database_server.login_employee(cursor,data.plain_password,data.id_employee)
    if result =="user not found":
        raise HTTPException(status_code=404,detail="user not found")
    elif result=="you are blocked":
        raise HTTPException(status_code=403,detail="you are blocked")
    elif result=="your password is false":
        raise HTTPException(status_code=401,detail="your password is false")
    conn.commit()
    return result
@app.post("/create employee")
def create_employee(data: CreateEmployee,token_data=Depends(security_bearer)):
    result=database_server.create_employee(cursor,token_data.credentials,data.full_name,data.password_hash)
    if result is False:
        raise HTTPException(status_code=403,detail="Only Admin can create new employee")
    conn.commit()
    return {"message":"Employee added successfully"}
@app.get("/show customer")
def get_customers(national_id: str,token_data=Depends(security_bearer)):
    result=database_server.get_customers(cursor,token_data.credentials,national_id=national_id)
    if result=="invalid token":
        raise HTTPException(status_code=404,detail=result)
    elif result=="user not found":
        raise HTTPException(status_code=404,detail="user not found")
    return result
@app.put("/make admin")
def make_admin(employee_id: int, token_data=Depends(security_bearer)):
    result=database_server.make_employee_Admin(cursor,token_data.credentials,employee_id)
    if result=="not admin or invalid token":
        raise HTTPException(status_code=403,detail="Only Admin can change employee roles")
    elif result=="employee not found":
        raise HTTPException(status_code=404,detail="the employee you want to upgrade was not found")
    elif result=="success":
        conn.commit()
        return {"msg":f"employee {employee_id} has been successfully upgraded to Admin"}
@app.put("/chang pin")
def chang_pin(customer_national: str,token_data=Depends(security_bearer)):
    result=database_server.change_pin(cursor,token_data.credentials,national_id=customer_national)
    if result=="invalid token":
        raise HTTPException(status_code=401,detail="Invalid or expired token")
    elif result=="customer not found":
        raise HTTPException(status_code=404,detail="Customer not found")
    elif result.startswith("success"):
        pure_pin=result.split(":")[1]
        conn.commit()
        return {"msg":"PIN update successfully","new_pin":pure_pin}
@app.put("/Top up balance")
def Top_up(data: TopUpBalance,token_data=Depends(security_bearer)):
    result=database_server.top_up_created(cursor,token_data.credentials,data.amount,national_id=data.national_id,id_account=data.account_id,number_phone=data.number_phone)
    if result=="Select to search":
        raise HTTPException(status_code=400,detail="Select national_id or numberphone or account_id to search")
    elif result=="invalid token":
        raise HTTPException(status_code=401,detail="invalid token")
    else:
        conn.commit()
        return {"msg":"success"}
@app.get("/show employee")
def show_employee(employee_id: int, token_data=Depends(security_bearer)):
    result=database_server.show_employee(cursor,token_data.credentials,id=employee_id)
    if result=="Invalid token":
        raise HTTPException(status_code=401,detail="Invalid token")
    elif result=="customer not found":
        raise HTTPException(status_code=404,detail="Customer not found")
    else:
        return result
@app.post("/transformation money")
def tramsformation_money(data: TransformationMoney, token_data=Depends(security_bearer)):
    result=database_server.transformation_money(cursor,token_data.credentials,data.sender_id,data.amount,data.sender_pin,receiver_phone=data.number_phone,recieiver_id=data.account_id,national_receiver=data.national_id)
    if result=="Invalid token":
        raise HTTPException(status_code=404,detail="Invalid token")
    elif result=="your account is blocked":
        raise HTTPException(status_code=403,detail="your account is blocked")
    elif isinstance(result, str) and result.startswith("error, id:"):
        raise HTTPException(status_code=400,detail=result)
    elif result=="Sorry, user not found":
        raise HTTPException(status_code=404, detail=result)
    elif result=="the account is blocked":
        raise HTTPException(status_code=403,detail=result)
    elif isinstance(result, str) and result.startswith("Sorry, the amount"):
        raise HTTPException(status_code=400,detail=result)
    else:
        conn.commit()
        return {"msg":"success"}
@app.get("/show transactions")
def get_transaction(user_id: int,period: Literal['day','week','month'],token_data=Depends(security_bearer)):
    result=database_server.get_user_transactions(cursor,token_data.credentials,user_id,period,)
    if result=="Invalid token":
        raise HTTPException(status_code=404,detail=result)
    elif result=="error: invalid period":
        raise HTTPException(status_code=400,detail=f"{result}, inter dey or week or month")
    else:
        return result
@app.get("/Monthly audit presentation of operations")
def get_monthly_audit(token_data=Depends(security_bearer)):
    result=database_server.get_manager_monthly_audit(cursor,token_data.credentials)
    if result==None:
        raise HTTPException(status_code=404,detail="Invalid token")
    return result
@app.put("/balance withdrawal")
def balance_withdrawal(data: Withdrawal,token_data=Depends(security_bearer)):
    result=database_server.balance_withdrawal(cursor,token_data.credentials,data.id_customer,data.customer_pin,data.national_customer,data.amount)
    if result=="invalid token":
        raise HTTPException(status_code=404,detail=result)
    elif result=="customer not found":
        raise HTTPException(status_code=404,detail=result)
    elif result=="the account is blocked":
        raise HTTPException(status_code=403,detail=result)
    elif result=="your pin is false":
        raise HTTPException(status_code=401,detail=result)
    elif result=="the national_id is false":
        raise HTTPException(status_code=401,detail=result)
    elif isinstance(result, str) and result.startswith("the amount"):
        raise HTTPException(status_code=400,detail=result)
    else:
        conn.commit()
        return result
@app.put("/Ban")
def ban(employee_id: int,token_data=Depends(security_bearer)):
    result=database_server.ban(cursor,token_data.credentials,employee_id=employee_id)
    if result=="invalid token":
        raise HTTPException(status_code=404,detail=result)
    elif result=="this account is alredy banned":
        raise HTTPException(status_code=422,detail=result)
    elif result=="you can't block Admin":
        raise HTTPException(status_code=403,detail=result)
    else:
        conn.commit()
        return result
@app.put("/Unblok")
def Unblock(employee_id: int,token_data=Depends(security_bearer)):
    result=database_server.Unblock(cursor,token_data.credentials,employee_id=employee_id)
    if result=="invalid token":
        raise HTTPException(status_code=404,detail=result)
    elif result=="user not found":
        raise HTTPException(status_code=404,detail=result)
    elif result=="this account is not blocked":
        raise HTTPException(status_code=422,detail=result)
    else:
        conn.commit()
        return result
@app.get("/transactions/by_date")
def get_transactions_by_dte(target_date: date, token_data=Depends(security_bearer)):
    today=date.today()
    if target_date > today:
        raise HTTPException(status_code=422,detail="Date noy yet available")
    min_date=date(2026, 1, 1)
    if target_date < min_date:
        raise HTTPException(status_code=422,detail="the date is very old om the system")
    result=database_server.get_transactions_by_specific_date(cursor,token_data.credentials,target_date)
    return result
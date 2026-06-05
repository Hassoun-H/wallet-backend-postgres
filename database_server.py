import random
import os
from auth_handler import create_access_token, verify_access_token
import bcrypt
import hashlib
from cryptography.fernet import Fernet
BASE_DIR=os.path.dirname(os.path.abspath(__file__))
db_path=os.path.join(BASE_DIR,"database_server")
from dotenv import load_dotenv
load_dotenv()
connection_params={
"host":"127.0.0.1",
"database":"my_project",
"user":"postgres",
"password":"1784",
"port":"5432"
}
def creat_table(cur):
    users="""
CREATE TABLE IF NOT EXISTS customers
(
id SERIAL PRIMARY KEY,
username TEXT NOT NULL,
pin TEXT NOT NULL,
number_phone_index TEXT NOT NULL,
national_id_index TEXT NOT NULL,
national_id TEXT NOT NULL UNIQUE,
employee_id INT,
FOREIGN KEY (employee_id)
REFERENCES employees(id),
is_active BOOLEAN DEFAULT FALSE,
mother_name TEXT NOT NULL,
full_name TEXT NOT NULL,
numberphone TEXT NOT NULL UNIQUE,
balance NUMERIC(15, 2) DEFAULT 0.00
);"""
    employees="""
CREATE TABLE IF NOT EXISTS employees
(
id SERIAL PRIMARY KEY,
full_name TEXT NOT NULL,
role TEXT DEFAULT 'staff',
password_hash TEXT NOT NULL,
is_blocked BOOLEAN DEFAULT FALSE
);"""
    transactions="""
CREATE TABLE IF NOT EXISTS transactions
(
id SERIAL PRIMARY KEY,
sender_id INT ,
receiver_id INT NOT NULL,
employee_id INT NOT NULL,
amount NUMERIC(15, 2) NOT NULL,
timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
FOREIGN  KEY (sender_id)
REFERENCES customers(id),
FOREIGN KEY (receiver_id)
REFERENCES customers(id),
FOREIGN KEY (employee_id)
REFERENCES employees(id),
CONSTRAINT check_different_user CHECK (sender_id <> receiver_id)

);"""

    cur.execute(employees)
    cur.execute(users)
    cur.execute(transactions)
    

#one
def hash_password(password: str) -> str:
    password_bytes=password.encode('utf-8')
    salt=bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')
def verify_password(plain_password:str,stored_hash:str) -> bool: 
   plain_bytes=plain_password.encode('utf-8')
   stored_bytes=stored_hash.encode('utf-8')
   return bcrypt.checkpw(plain_bytes,stored_bytes)
#two
raw_key=os.getenv("FERNET_SECRET_KEY")
SECRET_KEY=raw_key.encode('utf-8')
cipher_suite=Fernet(SECRET_KEY)
def encrypt_data(data:str) -> str:
    return cipher_suite.encrypt(data.encode("utf-8")).decode("utf-8")
def decrypt_data(encrypted_data:str) -> str:
    return cipher_suite.decrypt(encrypted_data.encode("utf-8")).decode("utf-8")

def generate_blind_index(national_id: str) -> str:
    salt="My_Super_Secret_Salt_123!"
    mixad_data = national_id + salt
    return hashlib.sha256(mixad_data.encode("utf-8")).hexdigest()

def generate_phone_index(number_phone: str) -> str:
    salt = "My_Super_Secret_Salt_123!"
    mixed_data=number_phone+salt
    return hashlib.sha3_256(mixed_data.encode("utf-8")).hexdigest()

def check_permission(cur, token, required_role=None):
    user_data=verify_access_token(token)
    if not user_data:
        return None
    emp_id=user_data['employee_id']
    emp_role=user_data['role']
    cur.execute("SELECT is_blocked FROM employees WHERE id=%s",(emp_id,))
    emp=cur.fetchone()
    if not emp or emp['is_blocked']:
        print("this account not found or blocked")
        return None
    if required_role and emp_role != required_role:
        print("you are not Admin")
        return None
    return emp_id
#**************************************************************************************************************#  Hasson 🤫🤫😉
def login_employee(cur,plain_password,id_employee):
    query="SELECT id,password_hash,role,is_blocked FROM employees WHERE id=%s"
    cur.execute(query,(id_employee,))
    result=cur.fetchone()
    if not result:
        print("user not found")
        return "user not found" 
    if result['is_blocked']:
        print("you are blocked")
        return "you are blocked"
    if not verify_password(plain_password,result['password_hash']):
        print("your password is false")
        return "your password is false"
    token=create_access_token(employee_id=result ['id'], role=result['role'])
    return {"access_token":token, "token_tybe": "bearer"}
def create_an_account(cur,token,username,numberphone,national_id,mother_name,full_name):
    emp_id=check_permission(cur,token)
    if not emp_id:
        return None
    camputer_PIN=random.randint(1000,9999)
    blocked=[1111,1234,4321,9999]
    while camputer_PIN in blocked:
        camputer_PIN=random.randint(1000,9999)
    pin_hash=hash_password(str(camputer_PIN))
    encrypted_phone=encrypt_data(numberphone)
    index_phone=generate_phone_index(numberphone)
    index_national=generate_blind_index(national_id)
    encrypted_national_id=encrypt_data(national_id)
    account="INSERT INTO customers (username, pin, numberphone, number_phone_index, national_id, national_id_index, mother_name, full_name, employee_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
    cur.execute(account,(username, pin_hash, encrypted_phone, index_phone, encrypted_national_id, index_national, mother_name, full_name, emp_id))
    print(f"your name: {username} and pin: {camputer_PIN} your number: {numberphone}")
    return {"your name":username,"your pin":camputer_PIN,"your number":numberphone}
def create_employee(cur,token,full_name,password_hash):
    admin_id=check_permission(cur,token,required_role="Admin")
    if not admin_id:
        return False
    employee_password_hash=hash_password(str(password_hash))
    employee="INSERT INTO employees (full_name,password_hash) VALUES (%s,%s)"
    cur.execute(employee,(full_name,employee_password_hash))
    print("user added successfully")
    return True
def get_customers(cur,token,national_id):
   emp_id=check_permission(cur,token)
   if not emp_id:
       return "invalid token"
   searsh_index=generate_blind_index(national_id)
   show="SELECT * FROM customers WHERE national_id_index=%s"
   cur.execute(show,(searsh_index,))
   result=cur.fetchone()
   if not result:
       print("user not found")
       return "user not found"
   print("result")
   return result
def top_up_created(cur,token,amount,national_id=None,id_account=None,number_phone=None):
    if id_account and number_phone and national_id is None:
        return "Select to search"
    emp_id=check_permission(cur,token)
    if not emp_id:
        return "invalid token"
    result=None
    if national_id:
        searsh_index=generate_blind_index(national_id)
        add="SELECT * FROM customers WHERE national_id_index=%s"
        cur.execute (add,(searsh_index,))
        result=cur.fetchone()
    elif id_account:
        add="SELECT * FROM customers WHERE id=%s"
        cur.execute(add,(id_account,))
        result=cur.fetchone()
    elif number_phone:
        searsh_phone_index=generate_phone_index(number_phone)
        add="select * FROM customers WHERE number_phone_index=%s"
        cur.execute(add,(searsh_phone_index,))
        result=cur.fetchone()
    if not result:
        return "user not found"
    customer_id=result['id']
    update_customer="UPDATE customers SET balance=balance+%s WHERE id=%s"
    cur.execute(update_customer,(amount,customer_id))
    insert="INSERT INTO transactions (receiver_id,employee_id,amount) VALUES (%s,%s,%s)"
    cur.execute(insert,(customer_id,emp_id,amount))
    return "nice "
def show_employee(cur,token,id):
    emp_id=check_permission(cur,token,required_role="Admin")
    if not emp_id:
        return "Invalid token"
    cur.execute("SELECT * FROM employees WHERE id=%s",(id,))
    result=cur.fetchall()
    if result:
        clean_result=[dict(row) for row in result]
        print(clean_result)
        return clean_result
    return "customer not found"
def transformation_money(cur,token,sender_id,amount,sender_pin,receiver_phone=None,recieiver_id=None,national_receiver=None):
    emp_id=check_permission(cur,token)
    if not emp_id:
        return "Invalid token"
    sender="SELECT balance, pin, is_active FROM customers WHERE id=%s"
    cur.execute(sender,(sender_id,))
    sender_result=cur.fetchone()
    if sender_result['is_active']:
        print("your account is blocked")
        return "your account is blocked"
    if not sender_result or not verify_password(str(sender_pin), sender_result['pin']):
        return f"error, id:{sender_id} Unknown with pin:{sender_pin} or wrong pin!"
    result_balance=sender_result['balance']
    receiver_row=None
    if receiver_phone:
        searsh_phone=generate_phone_index(receiver_phone)
        receiver="SELECT id, is_active FROM customers WHERE number_phone_index=%s"
        cur.execute(receiver,(searsh_phone,))
        receiver_row=cur.fetchone()
    elif recieiver_id:
        receiver="SELECT id, is_active FROM customers WHERE id=%s"
        cur.execute(receiver,(recieiver_id,))
        receiver_row=cur.fetchone()
    elif national_receiver:
        searsh_national_id=generate_blind_index(national_receiver)
        receiver="SELECT id, is_active FROM customers WHERE national_id_index=%s"
        cur.execute(receiver,(searsh_national_id,))
        receiver_row=cur.fethone()
    else:
        print("sorry user not found")
        return "Sorry, user not found"
    if receiver_row["is_active"]:
        print("the account is blocked")
        return "the account is blocked"
    receiver_id_row=receiver_row['id']
    if amount >= result_balance:
        return f"Sorry, the amount {amount} more than or equals:{result_balance}"
    transaction="INSERT INTO transactions (sender_id,receiver_id,amount,employee_id) VALUES (%s,%s,%s,%s)"
    cur.execute(transaction,(sender_id,receiver_id_row,amount,emp_id))
    update_customers_sender="UPDATE customers SET balance = balance - %s WHERE id=%s"
    cur.execute(update_customers_sender,(amount,sender_id))
    update_customers_receiver="UPDATE customers SET balance = balance + %s WHERE id=%s"
    cur.execute(update_customers_receiver,(amount,receiver_id_row))
    return True
def get_user_transactions(cur,token,user_id,period):
    emp_id=check_permission(cur,token,required_role="Admin")
    if not emp_id:
        return "Invalid token"
    if period=="day":
        query=" SELECT * FROM transactions WHERE sender_id = %s OR receiver_id = %s AND timestamp >= CURRENT_DATE"
    elif period=='week':
        query="SELECT * FROM transactions WHERE sender_id = %s OR receiver_id = %s AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days' "
    elif period =='month':
        query="SELECT * FROM transactions WHERE sender_id = %s OR receiver_id = %s  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '1 month' "
    else:
        return "error: invalid period"
    cur.execute(query,(user_id,user_id)) 
    result=cur.fetchall()
    clean_result=[dict(row) for row in result]
    print(clean_result)
    return clean_result
def get_manager_monthly_audit(cur,token):
    emp_id=check_permission(cur,token,required_role="Admin")
    if not emp_id:
        return None
    query="""SELECT 
    DATE(timestamp) AS audit_date,
    COUNT(id) AS total_transactions,
    SUM(amount) AS total_money_moved
    FROM transactions WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '1 month'
    GROUP BY DATE(timestamp)
    ORDER BY audit_date DESC;"""
    cur.execute(query)
    result=cur.fetchall()
    clean_result=[dict(row) for row in result]
    for day in clean_result:
        return f" DATE: {day['audit_date']} | operations: {day['total_transactions']} | total volume:${day["total_money_moved"]}"
def balance_withdrawal(cur,token,id_customer,pin,national_id,amount):
    emp_id=check_permission(cur,token)
    if not emp_id:
        return "Invalid token"
    customer="SELECT pin, is_active, national_id, balance FROM customers WHERE id=%s"
    cur.execute(customer,(id_customer,))
    result=cur.fetchone()
    if not result:
        return "customer not found"
    if result['is_active']:
        return "the account is blocked"
    if not verify_password(pin,result['pin']):
        return "your PIN is false"
    if national_id and decrypt_data(result['national_id'])!=(national_id):
        return "the national_id is False"
    if amount > result['balance']:
        return f"the amount:{amount} more than balance:{result['balance']}"
    update="UPDATE customers SET balance=balance-%s WHERE id=%s"
    cur.execute(update,(amount,id_customer))
    print("update successfully")
    return "success"
def ban(cur,token,employee_id):
    emp_id=check_permission(cur,token,required_role="Admin")
    if not emp_id:
        return "invalid token"
    employee="SELECT role, is_blocked FROM employees WHERE id=%s"
    cur.execute(employee,(employee_id,))
    result=cur.fetchone()
    if result['is_blocked']:
        return "this account is alredy banned"
    if result['role']=="Admin":
        return "you can't block Admin"
    update_bloked="UPDATE employees SET is_bloked=%s WHERE id=%s"
    cur.execute(update_bloked,(True,employee_id))
    return "success"
def Unblock(cur,token,employee_id):
    emp_id=check_permission(cur,token,required_role="Admin")
    if not emp_id:
        return "invalid token"
    employee="SELECT is_blocked FROM employees WHERE id=%s"
    cur.execute(employee,(employee_id,))
    result=cur.fetchone()
    if not result:
        return "user not found"
    if not result['is_blocked']:
        return "this account is not blocked"
    employee_update="UPDATE employees SET is_blocked=%s WHERE id=%s"
    cur.execute(employee_update,(False,employee_id))
    return "success"
def get_transactions_by_specific_date(cur,token,target_date):
    emp_id=check_permission(cur,token,required_role="Admin")
    if not emp_id:
        return "invalid token"
    query="""SELECT * FROM transactions WHERE DATE(timestamp)=%s
        ORDER BY timestamp ASC;"""
    cur.execute(query,[target_date])
    result=cur.fetchall()
    clean_result=[dict(row) for row in result]
    print(clean_result)
    print("_"*50 + "\n")
    return clean_result
def make_employee_Admin(cur,token,employee_id):
    admin_id=check_permission(cur,token,required_role="Admin")
    if not admin_id:
        return "not admin or invalid token"
    cur.execute("SELECT id FROM employees WHERE id=%s",(employee_id,))
    target_emp=cur.fetchone()
    if not target_emp:
        return "employee not found"
    query="UPDATE employees SET role='Admin' WHERE id=%s"
    cur.execute(query,(employee_id,))
    return "success"
def change_pin(cur,token,national_id):
    emp_id=check_permission(cur,token)
    if not emp_id:
        return "invalid token"
    searsh_index_national=generate_blind_index(national_id)
    cur.execute("SELECT * FROM customers WHERE national_id_index=%s",(searsh_index_national,))
    result=cur.fetchone()
    if not result:
        return "customer not found"
    new_pin=random.randint(1000,9999)
    blocked=[1111,1234,4321,9999]
    while new_pin in blocked:
        new_pin=random.randint(1000,9999)
    pin_hash=hash_password(new_pin)
    update="UPDATE customers SET pin=%s WHERE national_id_index=%s"
    cur.execute(update,(pin_hash,searsh_index_national))
    return{"msg":f"pin update successfully new pin: {new_pin}, please don't forget"}

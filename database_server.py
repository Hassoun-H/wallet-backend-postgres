import psycopg2
from psycopg2.extras import RealDictCursor
import random
import os
from auth_handler import create_access_token, verify_access_token
import bcrypt
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
national_id TEXT NOT NULL UNIQUE,
employee_id INT,
FOREIGN KEY (employee_id)
REFERENCES employees(id),
is_active BOOLEAN DEFAULT FALSE
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
def login_employee(cur,plain_password,id_employee):
    query="SELECT id,password_hash,role,is_blocked FROM employees WHERE id=%s"
    cur.execute(query,(id_employee,))
    result=cur.fetchone()
    if not result:
        print("user not found")
        return None
    if result['is_blocked']:
        print("you are blocked")
        return False
    if not verify_password(plain_password,result['password_hash']):
        print("your password is false")
        return None
    token=create_access_token(employee_id=result ['id'], role=result['role'])
    return {"access_token":token, "token_tybe": "bearer"}
#**************************************************************************************************************#  Hasson 🤫🤫😉
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
    encrypted_national_id=encrypt_data(national_id)
    account="INSERT INTO customers (username, pin, numberphone, national_id, mother_name, full_name, employee_id) VALUES (%s, %s, %s, %s, %s, %s, %s);"
    cur.execute(account,(username, pin_hash, encrypted_phone, encrypted_national_id, mother_name, full_name, emp_id))
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
def get_all_customers(cur):
   show="SELECT * FROM customers"
   cur.execute(show)
   result=cur.fetchall()
   clean_result=[dict(row) for row in(result)]
   try:
       clean_result['numberphone'] = decrypt_data(clean_result['numberphone'])
       clean_result['national'] = decrypt_data(clean_result['national'])
   except Exception:
       pass
   print(clean_result)
def top_up_created(cur,amount,token,national_id=None,id_account=None,number_phone=None):
    if id_account and number_phone and national_id is None:
        print("Select to search")
        return None
    emp_id=check_permission(cur,token)
    if not emp_id:
        return None
    result=None
    if national_id:
        add="SELECT * FROM customers WHERE national_id=%s"
        encrypted_national_id=encrypt_data(national_id)
        cur.execute (add,(encrypted_national_id,))
        result=cur.fetchone()
    elif id_account:
        add="SELECT * FROM customers WHERE id=%s"
        cur.execute(add,(id_account,))
        result=cur.fetchone()
    elif number_phone:
        add="select * FROM customers WHERE numberphone=%s"
        cur.execute(add,(number_phone,))
        result=cur.fetchone()
    if not result:
        print("user not found")
        return False
    customer_id=result['id']
    update_customer="UPDATE customers SET balance=balance+%s WHERE id=%s"
    cur.execute(update_customer,(amount,customer_id))
    insert="INSERT INTO transactions (receiver_id,employee_id,amount) VALUES (%s,%s,%s)"
    cur.execute(insert,(customer_id,emp_id,amount))
    return True
def transactions(cur):
    show="SELECT * FROM transactions"
    cur.execute(show)
    result=cur.fetchall()
    clean_result=[dict(row) for row in result]
    print (clean_result)
def show_employee(cur):
    cur.execute("SELECT * FROM employees")
    result=cur.fetchall()
    if result:
        clean_result=[dict(row) for row in result]
        print(clean_result)
        return True
    print("no one her")
    return False
def transformation_money(cur,sender_id,amount,sender_pin,token,receiver_phone=None,recieiver_id=None,national_receiver=None):
    emp_id=check_permission(cur,token)
    if not emp_id:
        return None
    sender="SELECT balance, pin, is_active FROM customers WHERE id=%s"
    cur.execute(sender,(sender_id,))
    sender_result=cur.fetchone()
    if sender_result['is_active']:
        print("your account is blocked")
        return False
    if not sender_result or not verify_password(str(sender_pin), sender_result['pin']):
        print(f"error, id:{sender_id} Unknown with pin:{sender_pin} or wrong pin!")
        return False
    result_balance=sender_result['balance']
    encrypted_receiver_phone=encrypt_data(receiver_phone)
    receiver_row=None
    if receiver_phone:
        receiver="SELECT id, is_active FROM customers WHERE numberphone=%s"
        cur.execute(receiver,(encrypted_receiver_phone,))
        receiver_row=cur.fetchone()
    elif recieiver_id:
        receiver="SELECT id, is_active FROM customers WHERE id=%s"
        cur.execute(receiver,(recieiver_id,))
        receiver_row=cur.fetchone()
    elif national_receiver:
        receiver="SELECT id, is_active FROM customers WHERE national_id=%s"
        cur.execute(receiver,(national_receiver,))
    else:
        print("sorry user not found")
        return False
    if receiver_row["is_active"]:
        print("the account is blocked")
        return False
    receiver_id_row=receiver_row['id']
    if amount >= result_balance:
        print(f"Sorry, the amount {amount} more than or equals:{result_balance}")
        return False
    transaction="INSERT INTO transactions (sender_id,receiver_id,amount,employee_id) VALUES (%s,%s,%s,%s)"
    cur.execute(transaction,(sender_id,receiver_id_row,amount,emp_id))
    update_customers_sender="UPDATE customers SET balance = balance - %s WHERE id=%s"
    cur.execute(update_customers_sender,(amount,sender_id))
    update_customers_receiver="UPDATE customers SET balance = balance + %s WHERE id=%s"
    cur.execute(update_customers_receiver,(amount,receiver_id_row))
    return True
def get_user_transactions(cur,user_id,period,token):
    emp_id=check_permission(cur,token,required_role="Admin")
    if not emp_id:
        return None
    if period=="day":
        query=" SELECT * FROM transactions WHERE sender_id = %s OR receiver_id = %s AND timestamp >= CURRENT_DATE"
    elif period=='week':
        query="SELECT * FROM transactions WHERE sender_id = %s OR receiver_id = %s AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days' "
    elif period =='month':
        query="SELECT * FROM transactions WHERE sender_id = %s OR receiver_id = %s  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '1 month' "
    cur.execute(query,(user_id,user_id)) 
    result=cur.fetchall()
    clean_result=[dict(row) for row in result]
    print(clean_result)
    return True
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
        print(f" DATE: {day['audit_date']} | operations: {day['total_transactions']} | total volume:${day["total_money_moved"]}")
    return True
def balance_withdrawal(cur,token,id_customer,pin,national_id,amount):
    emp_id=check_permission(cur,token)
    if not emp_id:
        return None
    customer="SELECT pin, is_active, national_id, balance FROM customers WHERE id=%s"
    cur.execute(customer,(id_customer,))
    result=cur.fetchone()
    if not result:
        print("customer not found")
        return False
    if result['is_active']:
        print("the account is blocked")
        return False
    if not verify_password(pin,result['pin']):
        print("your PIN is false")
        return False
    if national_id and encrypt_data(national_id)!=result['national_id']:
        print("the national_id is False")
        return False
    if amount > result['balance']:
        print(f"the amount:{amount} more than balance:{result['balance']}")
        return False
    update="UPDATE customers SET balance=balance-%s WHERE id=%s"
    cur.execute(update,(amount,id_customer))
    print("update successfully")
    return True
def ban(cur,employee_id,token):
    emp_id=check_permission(cur,token,required_role="Admin")
    if not emp_id:
        return None
    employee="SELECT role, is_blocked FROM employees WHERE id=%s"
    cur.execute(employee,(employee_id,))
    result=cur.fetchone()
    if result['is_blocked']:
        print("this account is alredy banned")
        return False
    if result['role']=="Admin":
        print("you can't block Admin")
        return False
    update_bloked="UPDATE employees SET is_bloked=%s WHERE id=%s"
    cur.execute(update_bloked,(True,employee_id))
    return True
def Unblock(cur,token,employee_id):
    emp_id=check_permission(cur,token,required_role="Admin")
    if not emp_id:
        return None
    employee="SELECT is_blocked FROM employees WHERE id=%s"
    cur.execute(employee,(employee_id,))
    result=cur.fetchone()
    if not result:
        print("user not found")
        return False
    if not result['is_blocked']:
        print("this account is not blocked")
        return False
    employee_update="UPDATE employees SET is_blocked=%s WHERE id=%s"
    cur.execute(employee_update,(False,employee_id))
    return True
def get_transactions_by_specific_date(cur, target_date,token):
    emp_id=check_permission(cur,token,required_role="Admin")
    if not emp_id:
        return None
    query="""SELECT * FROM transactions WHERE DATE(timestamp)=%s
        ORDER BY timestamp ASC;"""
    cur.execute(query,[target_date])
    result=cur.fetchall()
    clean_result=[dict(row) for row in result]
    print(clean_result)
    print("_"*50 + "\n")
    return clean_result
try:
    conn=psycopg2.connect(**connection_params)
    cursor=conn.cursor(cursor_factory=RealDictCursor)
    print("connected successfully")
    creat_table(cursor)
    #cursor.execute("DROP TABLE IF EXISTS transactions CASCADE;")
    #cursor.execute("DROP TABLE IF EXISTS customers CASCADE;")
    #cursor.execute("DROP TABLE IF EXISTS employees CASCADE;")
    #create_an_account(cursor,"Ali","0994688717","543210","nha","greb",1,"Admin123")
    #top_up_created(cursor,"012345","0993384496",7364,100)
    #get_all_customers(cursor)
    #create_employee(cursor,"Ahmed","Ahmed2026",1,"Admin123")
    #delete_employee(cursor,2,1,"Admin123")
    show_employee(cursor)
    #transactions(cursor)
    #transformation_money(cursor,1,7364,"0981092427",100)
    #get_user_transactions(cursor,1,"week")
    #get_manager_monthly_audit(cursor)
    #get_transactions_by_specific_date(cursor,"2026-5-20")
    conn.commit()
    
except Exception as e:
    conn.rollback()
    if "customers_numberphone_key" in str(e):
        print("Sorry, this number is already registered.")
    elif "customers_national_id_key" in str(e):
        print("Sorry,the national ID number is already registered")
    else:
        print(e)
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
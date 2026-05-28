import psycopg2
from psycopg2.extras import RealDictCursor
import random
import os
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

def create_an_account(cur,username,numberphone,national_id,mother_name,full_name,user_id,password):
    employee="SELECT is_blocked, password_hash FROM employees WHERE id=%s"
    cur.execute(employee,(user_id,))
    result=cur.fetchone()
    if not result:
        print("the id not compatible with password")
        return False
    if result['is_blocked']:
        print("your are blocked")
        return False
    if not verify_password(password,result['password_hash']):
        print("Sorry,the password is False")
        return False
    camputer_PIN=random.randint(1000,9999)
    blocked=[1111,1234,4321,9999]
    while camputer_PIN in blocked:
        camputer_PIN=random.randint(1000,9999)
    pin_hash=hash_password(str(camputer_PIN))
    encrypted_phone=encrypt_data(numberphone)
    encrypted_national_id=encrypt_data(national_id)
    account="INSERT INTO customers (username, pin, numberphone, national_id, mother_name, full_name, employee_id) VALUES (%s, %s, %s, %s, %s, %s, %s);"
    cur.execute(account,(username, pin_hash, encrypted_phone, encrypted_national_id, mother_name, full_name, user_id))
    print(f"your name: {username} and pin: {camputer_PIN} your number: {numberphone}")
    return {"your name":username,"your pin":camputer_PIN,"your number":numberphone}
def create_employee(cur,full_name,password_hash,Admin_id,password_Admin):
    employee_password_hash=hash_password(str(password_hash))
    Admin="SELECT role, password_hash FROM employees WHERE id=%s"
    cur.execute(Admin,(Admin_id,))
    result=cur.fetchone()
    if not result:
        print("the ID is not available")
        return False
    Admin_role=result['role']
    Admin_password=result['password_hash']
    if Admin_role != "Admin":
        print("Sorry, you are not Admin")
        return False
    if not verify_password(password_Admin, Admin_password):
        print("your password is false")
        return False
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
def top_up_created(cur,national_id,pin,amount,id_employee,password):
    employee="SELECT is_blocked, password_hash FROM employees WHERE id=%s"
    cur.execute(employee,(id_employee,))
    result=cur.fetchone()
    if not result:
        print("user not found")
        return False
    if result['is_blocked']:
        print("you are blocked")
        return False
    if not verify_password(password,result['passwword_hash']):
        print("you password is false")
        return False
    encrypted_national_id=encrypt_data(national_id)
    add="SELECT * FROM customers WHERE national_id=%s"
    cur.execute(add,(encrypted_national_id,))
    user=cur.fetchone()
    if user["is_active"]:
        print("the account is blocked")
        return False
    if user:
        if verify_password(str(pin),user['pin']):
         receiver_id=user['id']
         add_balance="INSERT INTO transactions (receiver_id,amount,employee_id) VALUES (%s,%s,%s)"
         update_balance="UPDATE customers SET balance = balance + %s WHERE id = %s"
         cur.execute (add_balance,(receiver_id,amount,id_employee))
         print(f"Successfully deposited {amount} to user ID {receiver_id}")
         cur.execute(update_balance,(amount,receiver_id))
         return True
        print("your password is false")
        return False
    print("Error: Customer data is incorrect or does not exist.")
    return False
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
def transformation_money(cur,sender_id,sender_pin,receiver_phone,amount,employee_id,password):
    employee="SELECT is_blocked, password_hash FROM employees WHERE id=%s"
    cur.execute(employee,(employee_id,))
    result=cur.fetchone()
    if not result:
        print("user not found")
        return False
    if result['is_blocked']:
        print("the password is blocked")
        return False
    if not verify_password(password,result['password_hash']):
        print("the password is false")
        return False
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
    receiver="SELECT id, is_active FROM customers WHERE numberphone=%s"
    cur.execute(receiver,(encrypted_receiver_phone,))
    receiver_row=cur.fetchone()
    if not receiver_row:
        print(f"sorry,{receiver_phone} it's not found")
        return False
    if receiver_row["is_active"]:
        print("the account is blocked")
        return False
    receiver_id_row=receiver_row['id']
    if amount >= result_balance:
        print(f"Sorry, the amount {amount} more than or equals:{result_balance}")
        return False
    transaction="INSERT INTO transactions (sender_id,receiver_id,amount) VALUES (%s,%s,%s)"
    cur.execute(transaction,(sender_id,receiver_id_row,amount))
    update_customers_sender="UPDATE customers SET balance = balance - %s WHERE id=%s"
    cur.execute(update_customers_sender,(amount,sender_id))
    update_customers_receiver="UPDATE customers SET balance = balance + %s WHERE id=%s"
    cur.execute(update_customers_receiver,(amount,receiver_id_row))
def get_user_transactions(cur,user_id,period):
    if period=="day":
        query=" SELECT * FROM transactions WHERE sender_id = %s OR receiver_id = %s AND timestamp >= CURRENT_DATE"
    elif period=='week':
        query="SELECT * FROM transactions WHERE sender_id = %s OR receiver_id = %s AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days' "
    elif period =='month':
        query="SELECT * FROM transactions WHERE sender_id = %s OR receiver_id = %s  AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '1 month' "
    else:
        query=("SELECT * FROM transactions WHERE sender_id = %s OR receiver_id = %s ")
    cur.execute(query,(user_id,user_id)) 
    result=cur.fetchall()
    clean_result=[dict(row) for row in result]
    print(clean_result)
    return True
def get_manager_monthly_audit(cur):
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
def delete_employee(cur,employee_id,Admin_id,password):
    Admin="SELECT role, password_hash FROM employees WHERE id=%s"
    cur.execute(Admin,(Admin_id,))
    result=cur.fetchone()
    if not result:
        print("user not found")
        return False
    if result['role'] != "Admin":
        print("you are not Admin")
        return False
    if not verify_password(password,result['password_hash']):
        print("password is false")
        return False
    employee="DELETE FROM employees WHERE id=%s"
    cur.execute(employee,(employee_id,))
    return True
def balance_withdrawal(cur,id_customer,pin,national_id,amount):
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
    if encrypt_data(national_id)!=result['national_id']:
        print("the national_id is False")
        return False
    if amount > result['balance']:
        print(" the amount more than balance")
        return False
    update="UPDATE customers SET balance=balance-%s WHERE id=%s"
    cur.execute(update,(amount,id_customer))
    print("update successfully")
    return True
def ban(cur,employee_id):
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
def Unblock(cur,employee_id):
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
def get_transactions_by_specific_date(cur, target_date):
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
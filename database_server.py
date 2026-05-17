import psycopg2
from psycopg2.extras import RealDictCursor
import random
import os
BASE_DIR=os.path.dirname(os.path.abspath(__file__))
db_path=os.path.join(BASE_DIR,"database_server")
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
pin INT NOT NULL,
national_id TEXT NOT NULL UNIQUE,
mother_name TEXT NOT NULL,
full_name TEXT NOT NULL,
numberphone TEXT NOT NULL UNIQUE,
balance NUMERIC(15, 2) DEFAULT 0.00
);"""
    transactions="""
CREATE TABLE IF NOT EXISTS transactions
(
id SERIAL PRIMARY KEY,
sender_id INT ,
receiver_id INT ,
amount NUMERIC(15, 2) NOT NULL,
timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
FOREIGN  KEY (sender_id)
REFERENCES customers(id),
FOREIGN KEY (receiver_id)
REFERENCES customers(id),
CONSTRAINT check_different_user
CHECK (sender_id <> receiver_id)
);"""

    cur.execute(users)
    cur.execute(transactions)
def create_an_account(cur,username,numberphone,national_id,mother_name,full_name):
    camputer_PIN=random.randint(1000,9999)
    blocked=[1111,1234,4321,9999]
    while camputer_PIN in blocked:
        camputer_PIN=random.randint(1000,9999)
    
    account="INSERT INTO customers (username, pin, numberphone, national_id, mother_name, full_name) VALUES (%s, %s, %s, %s, %s, %s);"
    cur.execute(account,(username, camputer_PIN, numberphone, national_id, mother_name, full_name))
    print(f"your name: {username} and pin: {camputer_PIN} your number: {numberphone}")
    return {"your name":username,"your pin":camputer_PIN,"your number":numberphone}
def get_all_customers(cur):
   show="SELECT * FROM customers"
   cur.execute(show)
   result=cur.fetchall()
   clean_result=[dict(row) for row in(result)]
   print(clean_result)
     
try:
    conn=psycopg2.connect(**connection_params)
    cursor=conn.cursor(cursor_factory=RealDictCursor)
    print("connected successfully")
    creat_table(cursor)
    create_an_account(cursor,"hasson","0993384496","012345","lma","hasan")
    get_all_customers(cursor)
    conn.commit()
except Exception as e:
    conn.rollback()
    if "customers_numberphone_key" in str(e):
        print("Sorry, this number is already registered.")
    elif "customers_national_key" in str(e):
        print("Sorry,the national ID number is already registered")
    else:
        print(e)
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()

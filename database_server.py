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
receiver_id INT NOT NULL,
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
def top_up_credit(cur,national_id,numberphone,pin,amount):
    add="SELECT * FROM customers WHERE national_id=%s and numberphone=%s and pin=%s"
    cur.execute(add,(national_id,numberphone,pin))
    user=cur.fetchone()
    if user:
        receiver_id=user['id']
        add_balance="INSERT INTO transactions (receiver_id,amount) VALUES (%s,%s)"
        update_balance="UPDATE customers SET balance = balance + %s WHERE id = %s"
        cur.execute (add_balance,(receiver_id,amount))
        print(f"Successfully deposited {amount} to user ID {receiver_id}")
        cur.execute(update_balance,(amount,receiver_id))
        return True
    else:
        print("Error: Customer data is incorrect or does not exist.")
        return False
def transactions(cur):
    show="SELECT * FROM transactions"
    cur.execute(show)
    result=cur.fetchall()
    clean_result=[dict(row) for row in result]
    print (clean_result)
def transformation_money(cur,sender_id,sender_pin,receiver_phone,amount):
    sender="SELECT balance FROM customers WHERE id=%s AND pin=%s"
    cur.execute(sender,(sender_id,sender_pin))
    result=cur.fetchone()
    if not result:
        print(f"error, id:{sender_id} Unknown with pin:{sender_pin}")
        return False
    result_balance=result['balance']
    receiver="SELECT id FROM customers WHERE numberphone=%s"
    cur.execute(receiver,(receiver_phone,))
    receiver_id=cur.fetchone()
    if not receiver_id:
        print(f"sorry,{receiver_phone} it's not found")
        return False
    receiver_id_row=receiver_id['id']
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
    #create_an_account(cursor,"Ahmed","0981092427","543210","nha","greb")
    #top_up_credit(cursor,"012345","0993384496",7364,100)
    get_all_customers(cursor)
    #transactions(cursor)
    #transformation_money(cursor,1,7364,"0981092427",100)
    #get_user_transactions(cursor,1,"week")
    get_manager_monthly_audit(cursor)
    get_transactions_by_specific_date(cursor,"2026-5-20")
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

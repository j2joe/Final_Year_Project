import mysql.connector

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Naomi@12345", 
        database="nexgen"
    )

try:
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT email, full_name, created_at FROM users")
    
    print("\n📦 Registered Users:")
    print("-"*40)
    for user in cursor.fetchall():
        print(f"👤 {user['full_name']}")
        print(f"📧 {user['email']}")
        print(f"🕒 {user['created_at']}")
        print("-"*40)
        
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    if conn.is_connected():
        cursor.close()
        conn.close()
import sqlite3
import os

def fix_block_final():
    db_path = os.path.join('instance', 'hotel.db')
    
    if not os.path.exists(db_path):
        print("Database not found")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check customers
        cursor.execute("SELECT id, name, is_blocked FROM customers LIMIT 3")
        customers = cursor.fetchall()
        print("Customers found:")
        for customer in customers:
            print(f"ID: {customer[0]}, Blocked: {customer[2]}")
        
        if customers:
            customer_id = customers[0][0]
            print(f"Testing with customer ID: {customer_id}")
            
            # Test block
            cursor.execute("""
                UPDATE customers 
                SET is_blocked = 1, 
                    block_reason = 'Test block', 
                    blocked_at = datetime('now'), 
                    blocked_by = 'Admin'
                WHERE id = ?
            """, (customer_id,))
            
            conn.commit()
            
            # Check result
            cursor.execute("SELECT is_blocked, block_reason FROM customers WHERE id = ?", (customer_id,))
            result = cursor.fetchone()
            
            if result and result[0] == 1:
                print("Block test: SUCCESS")
                
                # Unblock
                cursor.execute("""
                    UPDATE customers 
                    SET is_blocked = 0, 
                        block_reason = NULL, 
                        blocked_at = NULL, 
                        blocked_by = NULL
                    WHERE id = ?
                """, (customer_id,))
                
                conn.commit()
                print("Unblock test: SUCCESS")
                return True
            else:
                print("Block test: FAILED")
                return False
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == '__main__':
    print("Testing block system...")
    success = fix_block_final()
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")

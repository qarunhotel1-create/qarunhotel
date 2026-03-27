#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
from datetime import datetime

def test_block_direct():
    """اختبار مباشر لنظام الحظر"""
    
    # مسار قاعدة البيانات
    db_path = os.path.join('instance', 'hotel.db')
    
    if not os.path.exists(db_path):
        print("Database not found")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # فحص العملاء الموجودين
        cursor.execute("SELECT id, name, is_blocked FROM customers LIMIT 5")
        customers = cursor.fetchall()
        print("Existing customers:")
        for customer in customers:
            print(f"ID: {customer[0]}, Name: {customer[1]}, Blocked: {customer[2]}")
        
        if customers:
            # اختبار حظر العميل الأول
            customer_id = customers[0][0]
            print(f"\nTesting block for customer ID: {customer_id}")
            
            # حظر العميل
            cursor.execute("""
                UPDATE customers 
                SET is_blocked = 1, 
                    block_reason = 'اختبار النظام', 
                    blocked_at = datetime('now'), 
                    blocked_by = 'Admin Test'
                WHERE id = ?
            """, (customer_id,))
            
            conn.commit()
            
            # التحقق من النتيجة
            cursor.execute("SELECT is_blocked, block_reason FROM customers WHERE id = ?", (customer_id,))
            result = cursor.fetchone()
            
            if result and result[0] == 1:
                print(f"SUCCESS: Customer blocked. Reason: {result[1]}")
                
                # إلغاء الحظر
                cursor.execute("""
                    UPDATE customers 
                    SET is_blocked = 0, 
                        block_reason = NULL, 
                        blocked_at = NULL, 
                        blocked_by = NULL
                    WHERE id = ?
                """, (customer_id,))
                
                conn.commit()
                print("SUCCESS: Customer unblocked")
                return True
            else:
                print("FAILED: Could not block customer")
                return False
        else:
            print("No customers found")
            return False
            
        conn.close()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == '__main__':
    print("Testing block system directly...")
    success = test_block_direct()
    print(f"Test result: {'SUCCESS' if success else 'FAILED'}")

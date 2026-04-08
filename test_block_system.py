#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار نظام حظر العملاء
"""

import requests
import json

def test_block_system():
    """اختبار نظام الحظر"""
    
    base_url = "http://localhost:5000"
    
    # اختبار الوصول للصفحة
    try:
        response = requests.get(f"{base_url}/customers-new/1/edit")
        print(f"Status code for edit page: {response.status_code}")
        
        if response.status_code == 200:
            print("Edit page accessible")
            
            # محاولة اختبار طلب الحظر
            block_url = f"{base_url}/customers-new/block/1"
            
            # بيانات الطلب
            data = {
                "reason": "اختبار النظام"
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # إرسال طلب الحظر
            block_response = requests.post(block_url, 
                                         json=data, 
                                         headers=headers)
            
            print(f"Block request status: {block_response.status_code}")
            print(f"Block response: {block_response.text}")
            
        else:
            print(f"Cannot access edit page: {response.status_code}")
            
    except Exception as e:
        print(f"Error testing block system: {str(e)}")

if __name__ == '__main__':
    print("Testing block system...")
    test_block_system()

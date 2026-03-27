#!/usr/bin/env python3
"""
اختبار بسيط لإصلاح مشكلة التوجيه
Simple test for routing fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hotel import create_app

def test_routes_exist():
    """اختبار وجود الروابط"""
    print("🔧 اختبار وجود الروابط...")
    
    app = create_app()
    
    # Get all registered routes
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'rule': rule.rule
        })
    
    # Check for specific routes
    endpoints_to_check = [
        'main.index',
        'main.user_dashboard',
        'admin.dashboard',
        'auth.login'
    ]
    
    print("\n📋 الروابط المسجلة:")
    found_endpoints = []
    
    for route in routes:
        endpoint = route['endpoint']
        if any(endpoint.startswith(prefix) for prefix in ['main.', 'admin.', 'auth.']):
            print(f"✅ {endpoint}: {route['rule']}")
            found_endpoints.append(endpoint)
    
    print("\n🔍 اختبار الروابط المطلوبة:")
    all_found = True
    for endpoint in endpoints_to_check:
        if endpoint in found_endpoints:
            print(f"✅ {endpoint}: موجود")
        else:
            print(f"❌ {endpoint}: غير موجود")
            all_found = False
    
    # Check that main.dashboard does NOT exist
    if 'main.dashboard' in found_endpoints:
        print(f"❌ main.dashboard: موجود (لا يجب أن يكون موجود)")
        all_found = False
    else:
        print(f"✅ main.dashboard: غير موجود (هذا صحيح)")
    
    return all_found

if __name__ == '__main__':
    print("🚀 بدء اختبار الروابط...")
    
    if test_routes_exist():
        print("\n🎉 جميع الروابط صحيحة!")
        print("\n📝 الإصلاح:")
        print("   • main.dashboard غير موجود (صحيح)")
        print("   • main.user_dashboard موجود (صحيح)")
        print("   • admin.dashboard موجود (صحيح)")
        print("\n✅ تم حل مشكلة werkzeug.routing.exceptions.BuildError")
    else:
        print("\n❌ هناك مشاكل في الروابط")
    
    print("\n" + "="*50)
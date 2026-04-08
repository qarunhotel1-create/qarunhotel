
def format_arabic_text_v2(text):
    """دالة محسنة لتنسيق النص العربي - الإصدار الثاني"""
    import arabic_reshaper
    from bidi.algorithm import get_display
    
    if not text or not isinstance(text, str):
        return str(text) if text else ""
    
    try:
        # التحقق من وجود نص عربي
        has_arabic = any('\u0600' <= char <= '\u06FF' for char in text)
        
        if has_arabic:
            # الحل الأكثر فعالية: تجربة عدة طرق
            
            # الطريقة الأولى: إعدادات كاملة
            try:
                config = {
                    'delete_harakat': False,
                    'support_zwj': True,
                    'use_unshaped_instead_of_isolated': False,
                    'shift_harakat_position': False,
                    'support_ligatures': True,
                    'delete_tatweel': False,
                    'support_arabic_digits': True,
                    'support_persian_digits': True,
                    'force_unicode': True,
                    'shift_harakat_position': False,
                    'delete_shadda': False,
                    'support_arabic_letters': True
                }
                
                reshaped = arabic_reshaper.reshape(text, configuration=config)
                bidi_text = get_display(reshaped, base_dir='RTL', upper_is_rtl=True)
                return bidi_text
                
            except Exception:
                # الطريقة الثانية: إعدادات مبسطة
                try:
                    reshaped = arabic_reshaper.reshape(text, configuration={
                        'support_ligatures': True,
                        'delete_harakat': False
                    })
                    bidi_text = get_display(reshaped, base_dir='RTL')
                    return bidi_text
                except Exception:
                    # الطريقة الثالثة: الحد الأدنى
                    reshaped = arabic_reshaper.reshape(text)
                    return get_display(reshaped)
        else:
            return text
            
    except Exception as e:
        print(f"Error in Arabic formatting: {e}")
        return text

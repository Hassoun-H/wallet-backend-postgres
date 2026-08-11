from nicegui import ui, app
import requests
import base64
import json

API_URL = "http://127.0.0.1:8000"

def safe_json(res):
    try:
        return res.json()
    except Exception:
        return res.text or "تمت العملية بنجاح"

# سحب اسم الموظف ومعرفه من الـ Token بkفاءة عالية
def get_employee_info_from_token(token):
    try:
        if not token:
            return "موظف", "1"
        parts = token.split('.')
        if len(parts) > 1:
            payload = parts[1]
            payload += '=' * (-len(payload) % 4)
            data = json.loads(base64.urlsafe_b64decode(payload).decode('utf-8'))
            creds = data.get('credentials', {})
            name = creds.get('full_name', creds.get('username', 'موظف المحفظة'))
            emp_id = str(creds.get('employee_id', creds.get('id', '1')))
            return name, emp_id
    except Exception:
        pass
    return "حسون", "1"

@ui.page('/login')
def login_page():
    with ui.card().classes('w-full max-w-xl mx-auto mt-24 p-14 bg-slate-900 border border-slate-800 shadow-2xl rounded-3xl'):
        ui.label('تسجيل دخول الموظف').classes('text-3xl font-bold text-slate-100 mb-8 text-center')
        
        id_input = ui.input('معرف الموظف (ID)').classes('w-full mb-6 text-lg')
        pass_input = ui.input('كلمة المرور', password=True, password_toggle_button=True).classes('w-full mb-8 text-lg')
        
        def handle_login():
            try:
                response = requests.post(f"{API_URL}/Login", json={
                    "id_employee": id_input.value,
                    "plain_password": pass_input.value
                })
                if response.status_code == 200:
                    data = safe_json(response)
                    token = data.get('access_token') if isinstance(data, dict) else None
                    app.storage.user['token'] = token
                    ui.notify('تم تسجيل الدخول بنجاح', type='positive')
                    ui.navigate.to('/')
                else:
                    err_msg = safe_json(response)
                    detail = err_msg.get('detail', 'فشل الدخول') if isinstance(err_msg, dict) else err_msg
                    ui.notify(f'خطأ: {detail}', type='negative')
            except Exception as e:
                ui.notify(f'تعذر الاتصال بالسيرفر: {e}', type='negative')

        ui.button('دخول', on_click=handle_login).classes('w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 text-lg rounded-xl')

@ui.page('/')
def dashboard():
    token = app.storage.user.get('token')
    if not token:
        ui.navigate.to('/login')
        return

    emp_name, emp_id = get_employee_info_from_token(token)

    # الشريط العلوي يعرض اسم الموظف ومعرفه بوضوح
    with ui.row().classes('w-full justify-between items-center bg-slate-900 border-b border-slate-800 px-8 py-5 shadow-lg'):
        with ui.row().classes('items-center gap-3'):
            ui.icon('person', size='md').classes('text-blue-400')
            ui.label(f"الموظف: {emp_name}  |  المعرف (ID): {emp_id}").classes('text-xl font-bold text-slate-100')
        ui.button('تسجيل خروج', on_click=lambda: (app.storage.user.clear(), ui.navigate.to('/login')), icon='logout').classes('bg-red-600 text-white')

    with ui.column().classes('w-full max-w-5xl mx-auto p-8 mt-6'):
        ui.label('لوحة التحكم والعمليات المالية الأساسية').classes('text-3xl font-bold text-slate-200 mb-8')

        headers = {'Authorization': f"Bearer {token}"}

        # دالة لفتح النوافذ الفردية للعمليات (1 إلى 5)
        def open_form(title, action_type):
            with ui.dialog() as dialog, ui.card().classes('bg-slate-900 p-8 w-[600px] border border-slate-700 flex flex-col rounded-2xl'):
                
                with ui.row().classes('w-full justify-between items-center mb-6'):
                    ui.label(title).classes('text-2xl font-bold text-slate-100')
                    ui.button('رجوع', on_click=dialog.close, icon='arrow_back').classes('bg-slate-800 text-slate-200')

                if action_type == 'create_account':
                    u_name = ui.input('اسم المستخدم').classes('w-full mb-3')
                    n_phone = ui.input('رقم الهاتف').classes('w-full mb-3')
                    nat_id = ui.input('الرقم الوطني').classes('w-full mb-3')
                    m_name = ui.input('اسم الأم').classes('w-full mb-3')
                    f_name = ui.input('الاسم الكامل').classes('w-full mb-6')
                    def submit():
                        res = requests.post(f"{API_URL}/create_account", json={
                            "username": u_name.value, "numberphone": n_phone.value,
                            "national_id": nat_id.value, "mother_name": m_name.value, "full_name": f_name.value
                        }, headers=headers)
                        ui.notify(str(safe_json(res)), type='info')
                        dialog.close()
                    ui.button('تنفيذ', on_click=submit).classes('w-full bg-blue-600 text-white py-3 text-lg')

                elif action_type == 'chang_pin':
                    c_nat = ui.input('الرقم الوطني للزبون').classes('w-full mb-6 text-lg')
                    def submit():
                        res = requests.put(f"{API_URL}/chang pin", params={"customer_national": c_nat.value}, headers=headers)
                        data = safe_json(res)
                        if res.status_code == 200:
                            new_pin_val = data.get('new_pin', data) if isinstance(data, dict) else data
                            ui.notification(f"تم التحديث بنجاح! الرمز الجديد هو: {new_pin_val}", type='positive', timeout=15000)
                            dialog.close()
                        else:
                            detail = data.get('detail', data) if isinstance(data, dict) else data
                            ui.notify(str(detail), type='negative')
                    ui.button('استبدال PIN بالهوية', on_click=submit).classes('w-full bg-amber-600 text-white py-3 text-lg')

                elif action_type == 'withdrawal':
                    c_id = ui.input('معرف الزبون (ID)').classes('w-full mb-3')
                    c_pin = ui.input('رمز PIN', password=True).classes('w-full mb-3')
                    c_nat = ui.input('الرقم الوطني').classes('w-full mb-3')
                    amount = ui.number('المبلغ').classes('w-full mb-6')
                    def submit():
                        res = requests.put(f"{API_URL}/balance withdrawal", json={
                            "id_customer": int(c_id.value or 0), "customer_pin": c_pin.value,
                            "national_customer": c_nat.value, "amount": float(amount.value or 0)
                        }, headers=headers)
                        ui.notify(str(safe_json(res)), type='info')
                        dialog.close()
                    ui.button('سحب', on_click=submit).classes('w-full bg-red-600 text-white py-3 text-lg')

                elif action_type == 'transformation_money':
                    s_id = ui.number('معرف المرسل (ID)').classes('w-full mb-3')
                    s_pin = ui.input('رمز PIN للمرسل', password=True).classes('w-full mb-3')
                    amount = ui.number('المبلغ').classes('w-full mb-3')
                    r_phone = ui.input('رقم هاتف المستقبل (اختياري)').classes('w-full mb-3')
                    r_nat = ui.input('الرقم الوطني للمستقبل (اختياري)').classes('w-full mb-6')
                    def submit():
                        res = requests.post(f"{API_URL}/transformation_money", json={
                            "sender_id": int(s_id.value or 0), "sender_pin": s_pin.value,
                            "amount": float(amount.value or 0),
                            "number_phone": r_phone.value if r_phone.value else None,
                            "national_id": r_nat.value if r_nat.value else None
                        }, headers=headers)
                        ui.notify(str(safe_json(res)), type='info')
                        dialog.close()
                    ui.button('إرسال الرصيد', on_click=submit).classes('w-full bg-emerald-600 text-white py-3 text-lg')

                elif action_type == 'top_up':
                    amount = ui.number('المبلغ المراد شحنه').classes('w-full mb-3')
                    nat_id = ui.input('الرقم الوطني (اختياري)').classes('w-full mb-3')
                    phone = ui.input('رقم الهاتف (اختياري)').classes('w-full mb-3')
                    acc_id = ui.number('معرف الحساب (اختياري)').classes('w-full mb-6')
                    def submit():
                        res = requests.put(f"{API_URL}/TopUpBalance", json={
                            "amount": float(amount.value or 0),
                            "national_id": nat_id.value if nat_id.value else None,
                            "number_phone": phone.value if phone.value else None,
                            "account_id": int(acc_id.value) if acc_id.value else None
                        }, headers=headers)
                        ui.notify(str(safe_json(res)), type='info')
                        dialog.close()
                    ui.button('شحن الرصيد', on_click=submit).classes('w-full bg-teal-600 text-white py-3 text-lg')

            dialog.open()

        # نافذة الآدمن الكبرى رقم (6) التي تحتوي بداخلها على شبكة أزرار فرعية متعددة
        def open_admin_grid():
            with ui.dialog() as admin_dialog, ui.card().classes('bg-slate-900 p-8 w-[750px] max-h-[85vh] border border-purple-500/50 flex flex-col rounded-3xl'):
                
                with ui.row().classes('w-full justify-between items-center mb-6'):
                    ui.label('6. لوحة عمليات الآدمن والإدارة الشاملة').classes('text-2xl font-bold text-purple-400')
                    ui.button('رجوع للقائمة الرئيسية', on_click=admin_dialog.close, icon='arrow_back').classes('bg-slate-800 text-slate-200')

                # دالة فرعية لفتح استمارة العملية المحددة داخل الآدمن
                def open_admin_action_form(sub_title, sub_type):
                    with ui.dialog() as sub_dialog, ui.card().classes('bg-slate-900 p-6 w-[450px] border border-slate-700'):
                        ui.label(sub_title).classes('text-xl font-bold text-slate-100 mb-4')
                        
                        if sub_type == 'create_emp':
                            e_fullname = ui.input('الاسم الكامل للموظف').classes('w-full mb-2')
                            e_pass = ui.input('كلمة المرور', password=True).classes('w-full mb-4')
                            def sub():
                                res = requests.post(f"{API_URL}/create_employee", json={"full_name": e_fullname.value, "password_hash": e_pass.value}, headers=headers)
                                ui.notify(str(safe_json(res)), type='info')
                                sub_dialog.close()
                            ui.button('إضافة', on_click=sub).classes('w-full bg-purple-600 text-white')

                        elif sub_type == 'make_admin':
                            a_id = ui.number('معرف الموظف للترقية لآدمن').classes('w-full mb-4')
                            def sub():
                                res = requests.put(f"{API_URL}/make admin", params={"employee_id": int(a_id.value or 0)}, headers=headers)
                                ui.notify(str(safe_json(res)), type='info')
                                sub_dialog.close()
                            ui.button('ترقية', on_click=sub).classes('w-full bg-indigo-600 text-white')

                        elif sub_type == 'ban_emp':
                            t_id = ui.number('معرف الموظف للحظر').classes('w-full mb-4')
                            def sub():
                                res = requests.put(f"{API_URL}/Ban", params={"employee_id": int(t_id.value or 0)}, headers=headers)
                                ui.notify(str(safe_json(res)), type='info')
                                sub_dialog.close()
                            ui.button('حظر', on_click=sub).classes('w-full bg-red-600 text-white')

                        elif sub_type == 'unblock_emp':
                            t_id = ui.number('معرف الموظف لفك الحظر').classes('w-full mb-4')
                            def sub():
                                res = requests.put(f"{API_URL}/Unblock", params={"employee_id": int(t_id.value or 0)}, headers=headers)
                                ui.notify(str(safe_json(res)), type='info')
                                sub_dialog.close()
                            ui.button('فك الحظر', on_click=sub).classes('w-full bg-green-600 text-white')

                        elif sub_type == 'show_emp':
                            s_id = ui.number('معرف الموظف للاستعلام').classes('w-full mb-4')
                            def sub():
                                res = requests.get(f"{API_URL}/show employee", params={"employee_id": int(s_id.value or 0)}, headers=headers)
                                ui.notify(str(safe_json(res)), type='info')
                                sub_dialog.close()
                            ui.button('استعلام', on_click=sub).classes('w-full bg-blue-600 text-white')

                        elif sub_type == 'show_cust':
                            c_nat = ui.input('الرقم الوطني للزبون').classes('w-full mb-4')
                            def sub():
                                res = requests.get(f"{API_URL}/show customer", params={"national_id": c_nat.value}, headers=headers)
                                ui.notify(str(safe_json(res)), type='info')
                                sub_dialog.close()
                            ui.button('استعلام', on_click=sub).classes('w-full bg-blue-600 text-white')

                        elif sub_type == 'show_tx':
                            tx_uid = ui.number('معرف المستخدم').classes('w-full mb-2')
                            tx_per = ui.select(['day', 'week', 'month'], label='الفترة').classes('w-full mb-4')
                            def sub():
                                res = requests.get(f"{API_URL}/show transactions", params={"user_id": int(tx_uid.value or 0), "period": tx_per.value}, headers=headers)
                                ui.notify(str(safe_json(res)), type='info')
                                sub_dialog.close()
                            ui.button('عرض الحركات', on_click=sub).classes('w-full bg-teal-600 text-white')

                        elif sub_type == 'monthly_audit':
                            res = requests.get(f"{API_URL}/Monthly audit presentation of operations", headers=headers)
                            ui.notify(str(safe_json(res)), type='info')
                            sub_dialog.close()

                        elif sub_type == 'by_date':
                            d_in = ui.input('التاريخ (YYYY-MM-DD)').classes('w-full mb-4')
                            def sub():
                                res = requests.get(f"{API_URL}/transactions_by_date", params={"target_date": d_in.value}, headers=headers)
                                ui.notify(str(safe_json(res)), type='info')
                                sub_dialog.close()
                            ui.button('بحث', on_click=sub).classes('w-full bg-slate-600 text-white')

                        ui.button('إغلاق النافذة', on_click=sub_dialog.close).classes('w-full mt-3 bg-slate-800 text-xs text-slate-300')
                    sub_dialog.open()

                # شبكة أزرار الآدمن الفرعية (تفتح مثل أزرار القائمة الرئيسية تماماً)
                with ui.scroll_area().classes('w-full max-h-[60vh] pr-2'):
                    with ui.grid(columns=3).classes('gap-4 w-full'):
                        
                        with ui.card().classes('bg-slate-800 hover:bg-slate-700 cursor-pointer p-4 flex flex-col items-center rounded-xl').on('click', lambda: open_admin_action_form('إنشاء موظف جديد', 'create_emp')):
                            ui.icon('person_add_alt_1', size='md').classes('text-purple-400 mb-2')
                            ui.label('إضافة موظف').classes('text-sm font-semibold text-slate-100 text-center')

                        with ui.card().classes('bg-slate-800 hover:bg-slate-700 cursor-pointer p-4 flex flex-col items-center rounded-xl').on('click', lambda: open_admin_action_form('ترقية لآدمن', 'make_admin')):
                            ui.icon('verified_user', size='md').classes('text-indigo-400 mb-2')
                            ui.label('ترقية لآدمن').classes('text-sm font-semibold text-slate-100 text-center')

                        with ui.card().classes('bg-slate-800 hover:bg-slate-700 cursor-pointer p-4 flex flex-col items-center rounded-xl').on('click', lambda: open_admin_action_form('حظر موظف', 'ban_emp')):
                            ui.icon('block', size='md').classes('text-red-400 mb-2')
                            ui.label('حظر موظف').classes('text-sm font-semibold text-slate-100 text-center')

                        with ui.card().classes('bg-slate-800 hover:bg-slate-700 cursor-pointer p-4 flex flex-col items-center rounded-xl').on('click', lambda: open_admin_action_form('فك حظر موظف', 'unblock_emp')):
                            ui.icon('lock_open', size='md').classes('text-green-400 mb-2')
                            ui.label('فك الحظر').classes('text-sm font-semibold text-slate-100 text-center')

                        with ui.card().classes('bg-slate-800 hover:bg-slate-700 cursor-pointer p-4 flex flex-col items-center rounded-xl').on('click', lambda: open_admin_action_form('استعلام عن موظف', 'show_emp')):
                            ui.icon('badge', size='md').classes('text-blue-400 mb-2')
                            ui.label('استعلام موظف').classes('text-sm font-semibold text-slate-100 text-center')

                        with ui.card().classes('bg-slate-800 hover:bg-slate-700 cursor-pointer p-4 flex flex-col items-center rounded-xl').on('click', lambda: open_admin_action_form('استعلام عن زبون', 'show_cust')):
                            ui.icon('person_search', size='md').classes('text-amber-400 mb-2')
                            ui.label('استعلام زبون').classes('text-sm font-semibold text-slate-100 text-center')

                        with ui.card().classes('bg-slate-800 hover:bg-slate-700 cursor-pointer p-4 flex flex-col items-center rounded-xl').on('click', lambda: open_admin_action_form('حركات المستخدم', 'show_tx')):
                            ui.icon('history', size='md').classes('text-teal-400 mb-2')
                            ui.label('حركات مستخدم').classes('text-sm font-semibold text-slate-100 text-center')

                        with ui.card().classes('bg-slate-800 hover:bg-slate-700 cursor-pointer p-4 flex flex-col items-center rounded-xl').on('click', lambda: open_admin_action_form('التدقيق الشهري', 'monthly_audit')):
                            ui.icon('assessment', size='md').classes('text-indigo-300 mb-2')
                            ui.label('التدقيق الشهري').classes('text-sm font-semibold text-slate-100 text-center')

                        with ui.card().classes('bg-slate-800 hover:bg-slate-700 cursor-pointer p-4 flex flex-col items-center rounded-xl').on('click', lambda: open_admin_action_form('عمليات تاريخ معين', 'by_date')):
                            ui.icon('calendar_month', size='md').classes('text-slate-300 mb-2')
                            ui.label('حسب التاريخ').classes('text-sm font-semibold text-slate-100 text-center')

            admin_dialog.open()

        # الأزرار الستة الرئيسية الكبرى في القائمة الرئيسية
        with ui.grid(columns=2).classes('gap-8 w-full'):
            
            with ui.card().classes('bg-slate-900 hover:bg-slate-800 border border-slate-800 cursor-pointer p-8 flex flex-col items-center justify-center rounded-2xl shadow-xl').on('click', lambda: open_form('1. إنشاء حساب جديد', 'create_account')):
                ui.icon('person_add', size='xl').classes('text-blue-400 mb-4')
                ui.label('1. إنشاء حساب').classes('text-2xl font-bold text-slate-100')

            with ui.card().classes('bg-slate-900 hover:bg-slate-800 border border-slate-800 cursor-pointer p-8 flex flex-col items-center justify-center rounded-2xl shadow-xl').on('click', lambda: open_form('2. استبدال رمز PIN', 'chang_pin')):
                ui.icon('lock_reset', size='xl').classes('text-amber-400 mb-4')
                ui.label('2. استبدال رمز PIN (بالهوية)').classes('text-2xl font-bold text-slate-100 text-center')

            with ui.card().classes('bg-slate-900 hover:bg-slate-800 border border-slate-800 cursor-pointer p-8 flex flex-col items-center justify-center rounded-2xl shadow-xl').on('click', lambda: open_form('3. سحب أموال', 'withdrawal')):
                ui.icon('money_off', size='xl').classes('text-red-400 mb-4')
                ui.label('3. سحب أموال').classes('text-2xl font-bold text-slate-100')

            with ui.card().classes('bg-slate-900 hover:bg-slate-800 border border-slate-800 cursor-pointer p-8 flex flex-col items-center justify-center rounded-2xl shadow-xl').on('click', lambda: open_form('4. إرسال رصيد', 'transformation_money')):
                ui.icon('send', size='xl').classes('text-emerald-400 mb-4')
                ui.label('4. إرسال رصيد').classes('text-2xl font-bold text-slate-100')

            with ui.card().classes('bg-slate-900 hover:bg-slate-800 border border-slate-800 cursor-pointer p-8 flex flex-col items-center justify-center rounded-2xl shadow-xl').on('click', lambda: open_form('5. شحن رصيد', 'top_up')):
                ui.icon('account_balance_wallet', size='xl').classes('text-teal-400 mb-4')
                ui.label('5. شحن رصيد').classes('text-2xl font-bold text-slate-100')

            # الزر رقم 6 يفتح شبكة أزرار الآدمن بالكامل
            with ui.card().classes('bg-slate-900 hover:bg-slate-800 border border-purple-500/40 cursor-pointer p-8 flex flex-col items-center justify-center rounded-2xl shadow-xl').on('click', open_admin_grid):
                ui.icon('admin_panel_settings', size='xl').classes('text-purple-400 mb-4')
                ui.label('6. عمليات الآدمن والإدارة').classes('text-2xl font-bold text-slate-100 text-center')

ui.run(port=8080, title='المحفظة المالية', dark=True, storage_secret='secret_wallet_key_2026')
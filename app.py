from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
from database import Database
from datetime import datetime, timedelta
from auth import login_required, check_login

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')
db = Database()

# ==================== TRANG ĐĂNG NHẬP ====================
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if check_login(username, password):
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Sai tên đăng nhập hoặc mật khẩu!')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# ==================== TRANG CHỦ ====================
@app.route('/')
@login_required
def index():
    return render_template('index.html')

# ==================== CÁC TRANG KHÁC ====================
@app.route('/products')
@login_required
def products_page():
    return render_template('products.html')

@app.route('/customers')
@login_required
def customers_page():
    return render_template('customers.html')

@app.route('/reports')
@login_required
def reports_page():
    return render_template('reports.html')

@app.route('/invoices')
@login_required
def invoices_page():
    return render_template('invoices.html')

# ==================== API SẢN PHẨM ====================
@app.route('/api/products', methods=['GET'])
@login_required
def get_products():
    products = db.get_all_products()
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
@login_required
def add_product():
    try:
        data = request.json
        product_data = {
            'name': data['name'],
            'price': int(data['price']),
            'cost_price': int(data.get('cost_price', 0)),
            'stock': int(data.get('stock', 0)),
            'category': data.get('category', '')
        }
        product_id = db.add_product(product_data)
        if product_id:
            return jsonify({'success': True, 'id': product_id})
        else:
            return jsonify({'success': False, 'error': 'Không thể thêm sản phẩm'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    try:
        data = request.json
        product_data = {
            'name': data['name'],
            'price': int(data['price']),
            'cost_price': int(data.get('cost_price', 0)),
            'stock': int(data.get('stock', 0)),
            'category': data.get('category', '')
        }
        success = db.update_product(product_id, product_data)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    success = db.delete_product(product_id)
    return jsonify({'success': success})

# ==================== API KHÁCH HÀNG ====================
@app.route('/api/customers', methods=['GET'])
@login_required
def get_customers():
    customers = db.get_all_customers()
    return jsonify(customers)

@app.route('/api/customers', methods=['POST'])
@login_required
def add_customer():
    try:
        data = request.json
        customer_data = {
            'name': data['name'],
            'phone': data.get('phone', ''),
            'email': data.get('email', ''),
            'address': data.get('address', ''),
            'total_spent': 0
        }
        customer_id = db.add_customer(customer_data)
        if customer_id:
            return jsonify({'success': True, 'id': customer_id})
        else:
            return jsonify({'success': False, 'error': 'Không thể thêm khách hàng'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
@login_required
def update_customer(customer_id):
    try:
        data = request.json
        customer_data = {
            'name': data['name'],
            'phone': data.get('phone', ''),
            'email': data.get('email', ''),
            'address': data.get('address', '')
        }
        success = db.update_customer(customer_id, customer_data)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
@login_required
def delete_customer(customer_id):
    success, error = db.delete_customer(customer_id)
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': error}), 400

@app.route('/api/customers/<int:customer_id>/history')
@login_required
def get_customer_history(customer_id):
    history = db.get_customer_history(customer_id)
    return jsonify(history)

# ==================== API ĐƠN HÀNG ====================
@app.route('/api/orders', methods=['GET'])
@login_required
def get_orders():
    orders = db.get_all_orders()
    return jsonify(orders)

@app.route('/api/orders', methods=['POST'])
@login_required
def create_order():
    try:
        data = request.json
        order_number = f"DH{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        order_data = {
            'order_number': order_number,
            'customer_id': data.get('customer_id'),
            'total_amount': data['total_amount'],
            'payment_method': data.get('payment_method', 'cash'),
            'status': 'completed',
            'created_by': 1
        }
        
        order_id, error = db.create_order(order_data, data['items'])
        
        if order_id:
            return jsonify({'success': True, 'order_id': order_id, 'order_number': order_number})
        else:
            return jsonify({'success': False, 'error': error}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== API HÓA ĐƠN ====================
@app.route('/api/invoices', methods=['GET'])
@login_required
def get_invoices():
    filter_type = request.args.get('filter', 'all')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    invoices = db.get_invoices(filter_type, start_date, end_date)
    return jsonify(invoices)

# ==================== API THỐNG KÊ ====================
@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    stats = db.get_stats()
    return jsonify(stats)

@app.route('/api/reports/detail', methods=['GET'])
@login_required
def report_detail():
    """Báo cáo chi tiết doanh thu theo ngày/tháng/năm"""
    try:
        report_type = request.args.get('type', 'day')
        date_param = request.args.get('date')
        
        if report_type == 'day':
            if date_param:
                target_date = date_param
            else:
                target_date = datetime.now().date().isoformat()
            
            # Lấy dữ liệu theo giờ
            result = db.client.table('orders')\
                .select('created_at, total_amount')\
                .eq('status', 'completed')\
                .gte('created_at', target_date)\
                .lt('created_at', f"{target_date}T23:59:59")\
                .execute()
            
            hours_data = {}
            for order in result.data:
                hour = int(order['created_at'][11:13])
                hours_data[hour] = hours_data.get(hour, 0) + order['total_amount']
            
            reports = []
            for h in range(24):
                reports.append({
                    'hour': f"{h:02d}",
                    'order_count': 1 if h in hours_data else 0,
                    'revenue': hours_data.get(h, 0)
                })
            
            return jsonify(reports)
        
        elif report_type == 'month':
            if date_param:
                target_date = date_param
            else:
                target_date = datetime.now().strftime('%Y-%m')
            
            result = db.client.table('orders')\
                .select('created_at, total_amount')\
                .eq('status', 'completed')\
                .gte('created_at', f"{target_date}-01")\
                .lt('created_at', f"{target_date}-32")\
                .execute()
            
            days_data = {}
            for order in result.data:
                day = int(order['created_at'][8:10])
                days_data[day] = days_data.get(day, 0) + order['total_amount']
            
            year = int(target_date[:4])
            month = int(target_date[5:7])
            from calendar import monthrange
            days_in_month = monthrange(year, month)[1]
            
            reports = []
            for d in range(1, days_in_month + 1):
                reports.append({
                    'day': f"{year}-{month:02d}-{d:02d}",
                    'order_count': 1 if d in days_data else 0,
                    'revenue': days_data.get(d, 0)
                })
            
            return jsonify(reports)
        
        elif report_type == 'year':
            if date_param:
                year = int(date_param.split('-')[0])
            else:
                year = datetime.now().year
            
            result = db.client.table('orders')\
                .select('created_at, total_amount')\
                .eq('status', 'completed')\
                .gte('created_at', f"{year}-01-01")\
                .lt('created_at', f"{year + 1}-01-01")\
                .execute()
            
            months_data = {}
            for order in result.data:
                month = int(order['created_at'][5:7])
                months_data[month] = months_data.get(month, 0) + order['total_amount']
            
            reports = []
            for m in range(1, 13):
                reports.append({
                    'month': f"{year}-{m:02d}",
                    'order_count': 1 if m in months_data else 0,
                    'revenue': months_data.get(m, 0)
                })
            
            return jsonify(reports)
        
        return jsonify([])
    except Exception as e:
        print(f"Lỗi report_detail: {e}")
        return jsonify([])

# ==================== CHẠY APP ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

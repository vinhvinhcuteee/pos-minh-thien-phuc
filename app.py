from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
from database import Database
from datetime import datetime, timedelta
from auth import login_required, check_login

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
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

# ==================== QUẢN LÝ SẢN PHẨM ====================
@app.route('/products')
@login_required
def products_page():
    return render_template('products.html')

@app.route('/api/products', methods=['GET'])
@login_required
def get_products():
    products = db.fetch_all("SELECT * FROM products ORDER BY id DESC")
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
@login_required
def add_product():
    data = request.json
    query = """
        INSERT INTO products (name, price, stock, cost_price, category)
        VALUES (%s, %s, %s, %s, %s)
    """
    product_id = db.execute_query(query, (
        data['name'],
        data['price'],
        data['stock'],
        data.get('cost_price', 0),
        data.get('category', '')
    ))
    return jsonify({'success': True, 'id': product_id})

@app.route('/api/products/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    data = request.json
    query = """
        UPDATE products 
        SET name=%s, price=%s, stock=%s, cost_price=%s, category=%s
        WHERE id=%s
    """
    db.execute_query(query, (
        data['name'],
        data['price'],
        data['stock'],
        data.get('cost_price', 0),
        data.get('category', ''),
        product_id
    ))
    return jsonify({'success': True})

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    db.execute_query("DELETE FROM products WHERE id=%s", (product_id,))
    return jsonify({'success': True})

# ==================== QUẢN LÝ KHÁCH HÀNG ====================
@app.route('/customers')
@login_required
def customers_page():
    return render_template('customers.html')

@app.route('/api/customers', methods=['GET'])
@login_required
def get_customers():
    customers = db.fetch_all("SELECT * FROM customers ORDER BY total_spent DESC")
    return jsonify(customers)

@app.route('/api/customers', methods=['POST'])
@login_required
def add_customer():
    data = request.json
    query = """
        INSERT INTO customers (name, phone, email, address, total_spent)
        VALUES (%s, %s, %s, %s, %s)
    """
    customer_id = db.execute_query(query, (
        data['name'],
        data.get('phone', ''),
        data.get('email', ''),
        data.get('address', ''),
        0
    ))
    return jsonify({'success': True, 'id': customer_id})

@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
@login_required
def update_customer(customer_id):
    data = request.json
    db.execute_query("""
        UPDATE customers 
        SET name=%s, phone=%s, email=%s, address=%s
        WHERE id=%s
    """, (data['name'], data.get('phone', ''), data.get('email', ''), 
          data.get('address', ''), customer_id))
    return jsonify({'success': True})

@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
@login_required
def delete_customer(customer_id):
    orders = db.fetch_one("SELECT COUNT(*) as count FROM orders WHERE customer_id = %s", (customer_id,))
    if orders and orders['count'] > 0:
        return jsonify({'success': False, 'error': 'Khách hàng có đơn hàng, không thể xóa'}), 400
    
    db.execute_query("DELETE FROM customers WHERE id=%s", (customer_id,))
    return jsonify({'success': True})

@app.route('/api/customers/<int:customer_id>/history')
@login_required
def get_customer_history(customer_id):
    orders = db.fetch_all("""
        SELECT o.*, oi.product_id, oi.quantity, oi.price, p.name as product_name
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        WHERE o.customer_id = %s
        ORDER BY o.created_at DESC
    """, (customer_id,))
    return jsonify(orders)

# ==================== QUẢN LÝ ĐƠN HÀNG ====================
@app.route('/api/orders', methods=['GET'])
@login_required
def get_orders():
    orders = db.fetch_all("""
        SELECT o.*, c.name as customer_name 
        FROM orders o
        LEFT JOIN customers c ON o.customer_id = c.id
        ORDER BY o.created_at DESC 
        LIMIT 50
    """)
    return jsonify(orders)

@app.route('/api/orders', methods=['POST'])
@login_required
def create_order():
    data = request.json
    order_number = f"DH{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    query = """
        INSERT INTO orders (order_number, customer_id, total_amount, payment_method, status, created_by)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    order_id = db.execute_query(query, (
        order_number,
        data.get('customer_id'),
        data['total_amount'],
        data.get('payment_method', 'cash'),
        'completed',
        data.get('created_by', 1)
    ))
    
    for item in data['items']:
        db.execute_query("""
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (%s, %s, %s, %s)
        """, (order_id, item['id'], item['quantity'], item['price']))
        
        db.execute_query("""
            UPDATE products SET stock = stock - %s WHERE id = %s
        """, (item['quantity'], item['id']))
    
    if data.get('customer_id'):
        db.execute_query("""
            UPDATE customers 
            SET total_spent = total_spent + %s,
                last_purchase = NOW()
            WHERE id = %s
        """, (data['total_amount'], data['customer_id']))
    
    return jsonify({'success': True, 'order_id': order_id, 'order_number': order_number})

# ==================== HÓA ĐƠN ====================
@app.route('/invoices')
@login_required
def invoices_page():
    return render_template('invoices.html')

@app.route('/api/invoices', methods=['GET'])
@login_required
def get_invoices():
    filter_type = request.args.get('filter', 'all')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = """
        SELECT 
            o.order_number,
            o.created_at,
            p.name as product_name,
            oi.quantity,
            oi.price,
            (oi.quantity * oi.price) as subtotal,
            o.total_amount
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        WHERE o.status = 'completed'
    """
    params = []
    
    if filter_type == 'today':
        query += " AND DATE(o.created_at) = CURRENT_DATE"
    elif filter_type == 'week':
        query += " AND o.created_at >= DATE_TRUNC('week', CURRENT_DATE)"
    elif filter_type == 'month':
        query += " AND o.created_at >= DATE_TRUNC('month', CURRENT_DATE)"
    
    if start_date:
        query += " AND DATE(o.created_at) >= %s"
        params.append(start_date)
    
    if end_date:
        query += " AND DATE(o.created_at) <= %s"
        params.append(end_date)
    
    query += " ORDER BY o.created_at DESC"
    
    invoices = db.fetch_all(query, tuple(params) if params else None)
    return jsonify(invoices)

# ==================== BÁO CÁO THỐNG KÊ ====================
@app.route('/reports')
@login_required
def reports_page():
    return render_template('reports.html')

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    total_products = db.fetch_one("SELECT COUNT(*) as count FROM products")
    total_customers = db.fetch_one("SELECT COUNT(*) as count FROM customers")
    total_orders = db.fetch_one("SELECT COUNT(*) as count FROM orders WHERE status = 'completed'")
    
    today = datetime.now().date()
    today_revenue = db.fetch_one("""
        SELECT COALESCE(SUM(total_amount), 0) as revenue 
        FROM orders 
        WHERE DATE(created_at) = %s AND status = 'completed'
    """, (today,))
    
    this_month = datetime.now().replace(day=1).date()
    month_revenue = db.fetch_one("""
        SELECT COALESCE(SUM(total_amount), 0) as revenue 
        FROM orders 
        WHERE DATE(created_at) >= %s AND status = 'completed'
    """, (this_month,))
    
    profit_data = db.fetch_one("""
        SELECT 
            COALESCE(SUM(oi.quantity * oi.price), 0) as revenue,
            COALESCE(SUM(oi.quantity * p.cost_price), 0) as cost
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.id
        JOIN products p ON oi.product_id = p.id
        WHERE DATE(o.created_at) >= %s AND o.status = 'completed'
    """, (this_month,))
    
    revenue = profit_data['revenue'] if profit_data else 0
    cost = profit_data['cost'] if profit_data else 0
    profit = revenue - cost
    
    top_products = db.fetch_all("""
        SELECT p.name, SUM(oi.quantity) as total_sold
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        JOIN orders o ON oi.order_id = o.id
        WHERE o.status = 'completed'
        GROUP BY p.id, p.name
        ORDER BY total_sold DESC
        LIMIT 5
    """)
    
    return jsonify({
        'total_products': total_products['count'] if total_products else 0,
        'total_customers': total_customers['count'] if total_customers else 0,
        'total_orders': total_orders['count'] if total_orders else 0,
        'today_revenue': today_revenue['revenue'] if today_revenue else 0,
        'month_revenue': month_revenue['revenue'] if month_revenue else 0,
        'profit': profit,
        'profit_margin': (profit / revenue * 100) if revenue > 0 else 0,
        'top_products': top_products
    })

@app.route('/api/reports/detail', methods=['GET'])
@login_required
def report_detail():
    report_type = request.args.get('type', 'day')
    date_param = request.args.get('date')
    
    if report_type == 'day':
        if date_param:
            target_date = date_param
        else:
            target_date = datetime.now().strftime('%Y-%m-%d')
        
        query = """
            SELECT 
                EXTRACT(HOUR FROM created_at) as hour,
                COUNT(*) as order_count,
                COALESCE(SUM(total_amount), 0) as revenue
            FROM orders
            WHERE DATE(created_at) = %s AND status = 'completed'
            GROUP BY hour
            ORDER BY hour
        """
        reports = db.fetch_all(query, (target_date,))
        
        hours_data = {int(h['hour']): h for h in reports}
        result = []
        for h in range(24):
            if h in hours_data:
                result.append({
                    'hour': f"{h:02d}",
                    'order_count': hours_data[h]['order_count'],
                    'revenue': hours_data[h]['revenue']
                })
            else:
                result.append({
                    'hour': f"{h:02d}",
                    'order_count': 0,
                    'revenue': 0
                })
        return jsonify(result)
    
    elif report_type == 'month':
        if date_param:
            target_date = datetime.strptime(date_param, '%Y-%m-%d')
        else:
            target_date = datetime.now()
        
        year = target_date.year
        month = target_date.month
        
        query = """
            SELECT 
                EXTRACT(DAY FROM created_at) as day,
                COUNT(*) as order_count,
                COALESCE(SUM(total_amount), 0) as revenue
            FROM orders
            WHERE EXTRACT(YEAR FROM created_at) = %s 
                AND EXTRACT(MONTH FROM created_at) = %s
                AND status = 'completed'
            GROUP BY day
            ORDER BY day
        """
        reports = db.fetch_all(query, (year, month))
        
        from calendar import monthrange
        days_in_month = monthrange(year, month)[1]
        days_data = {int(d['day']): d for d in reports}
        result = []
        for d in range(1, days_in_month + 1):
            if d in days_data:
                result.append({
                    'day': f"{year}-{month:02d}-{d:02d}",
                    'order_count': days_data[d]['order_count'],
                    'revenue': days_data[d]['revenue']
                })
            else:
                result.append({
                    'day': f"{year}-{month:02d}-{d:02d}",
                    'order_count': 0,
                    'revenue': 0
                })
        return jsonify(result)
    
    elif report_type == 'year':
        if date_param:
            year = int(date_param.split('-')[0])
        else:
            year = datetime.now().year
        
        query = """
            SELECT 
                EXTRACT(MONTH FROM created_at) as month,
                COUNT(*) as order_count,
                COALESCE(SUM(total_amount), 0) as revenue
            FROM orders
            WHERE EXTRACT(YEAR FROM created_at) = %s AND status = 'completed'
            GROUP BY month
            ORDER BY month
        """
        reports = db.fetch_all(query, (year,))
        
        months_data = {int(m['month']): m for m in reports}
        result = []
        for m in range(1, 13):
            if m in months_data:
                result.append({
                    'month': f"{year}-{m:02d}",
                    'order_count': months_data[m]['order_count'],
                    'revenue': months_data[m]['revenue']
                })
            else:
                result.append({
                    'month': f"{year}-{m:02d}",
                    'order_count': 0,
                    'revenue': 0
                })
        return jsonify(result)
    
    return jsonify([])

# ==================== CHẠY APP ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
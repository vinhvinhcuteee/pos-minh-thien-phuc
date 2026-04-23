from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
from database import Database
from datetime import datetime, timedelta
from auth import login_required, check_login
import sqlite3  # Thêm dòng này nếu chưa có
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

# Thêm vào sau API invoices (khoảng dòng 220):

@app.route('/api/invoices/<order_number>', methods=['DELETE'])
@login_required
def delete_invoice(order_number):
    """Xóa hóa đơn theo mã đơn hàng"""
    try:
        success, message = db.delete_invoice(order_number)
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
                target_date = datetime.now().strftime('%Y-%m-%d')
            
            reports = []
            for h in range(24):
                reports.append({
                    'hour': f"{h:02d}",
                    'order_count': 0,
                    'revenue': 0,
                    'total_quantity': 0
                })
            
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT 
                    strftime('%H', o.created_at) as hour,
                    COUNT(DISTINCT o.id) as order_count,
                    SUM(o.total_amount) as revenue,
                    SUM(oi.quantity) as total_quantity
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                WHERE o.status = 'completed' AND DATE(o.created_at) = ?
                GROUP BY strftime('%H', o.created_at)
            """, (target_date,))
            
            rows = cursor.fetchall()
            for row in rows:
                hour_int = int(row['hour'])
                reports[hour_int]['order_count'] = row['order_count']
                reports[hour_int]['revenue'] = row['revenue'] or 0
                reports[hour_int]['total_quantity'] = row['total_quantity'] or 0
            
            return jsonify(reports)
        
        elif report_type == 'month':
            if date_param:
                target_date = date_param
            else:
                target_date = datetime.now().strftime('%Y-%m')
            
            year = int(target_date[:4])
            month = int(target_date[5:7])
            from calendar import monthrange
            days_in_month = monthrange(year, month)[1]
            
            reports = []
            for d in range(1, days_in_month + 1):
                reports.append({
                    'day': f"{year}-{month:02d}-{d:02d}",
                    'order_count': 0,
                    'revenue': 0,
                    'total_quantity': 0
                })
            
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT 
                    strftime('%d', o.created_at) as day,
                    COUNT(DISTINCT o.id) as order_count,
                    SUM(o.total_amount) as revenue,
                    SUM(oi.quantity) as total_quantity
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                WHERE o.status = 'completed' AND strftime('%Y-%m', o.created_at) = ?
                GROUP BY strftime('%d', o.created_at)
            """, (target_date,))
            
            rows = cursor.fetchall()
            for row in rows:
                day_int = int(row['day'])
                reports[day_int - 1]['order_count'] = row['order_count']
                reports[day_int - 1]['revenue'] = row['revenue'] or 0
                reports[day_int - 1]['total_quantity'] = row['total_quantity'] or 0
            
            return jsonify(reports)
        
        elif report_type == 'year':
            if date_param:
                year = int(date_param.split('-')[0])
            else:
                year = datetime.now().year
            
            reports = []
            for m in range(1, 13):
                reports.append({
                    'month': f"{year}-{m:02d}",
                    'order_count': 0,
                    'revenue': 0,
                    'total_quantity': 0
                })
            
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT 
                    strftime('%m', o.created_at) as month,
                    COUNT(DISTINCT o.id) as order_count,
                    SUM(o.total_amount) as revenue,
                    SUM(oi.quantity) as total_quantity
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                WHERE o.status = 'completed' AND strftime('%Y', o.created_at) = ?
                GROUP BY strftime('%m', o.created_at)
            """, (str(year),))
            
            rows = cursor.fetchall()
            for row in rows:
                month_int = int(row['month'])
                reports[month_int - 1]['order_count'] = row['order_count']
                reports[month_int - 1]['revenue'] = row['revenue'] or 0
                reports[month_int - 1]['total_quantity'] = row['total_quantity'] or 0
            
            return jsonify(reports)
        
        return jsonify([])
        
    except Exception as e:
        print(f"ERROR: {e}")
        return jsonify({'error': str(e)}), 500
        
@app.route('/backup/full')
@login_required
def backup_full():
    """Backup đầy đủ: sản phẩm, khách hàng, đơn hàng, chi tiết đơn hàng"""
    import sqlite3
    from datetime import datetime
    
    conn = sqlite3.connect('data/pos.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Nội dung backup
    content = f"""-- ============================================
-- BACKUP CỬA HÀNG MINH THIÊN PHÚC
-- Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- ============================================

PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;

"""
    
    # 1. Bảng sản phẩm
    content += "-- ============================================\n"
    content += "-- 1. DANH SÁCH SẢN PHẨM\n"
    content += "-- ============================================\n\n"
    
    cursor.execute("SELECT * FROM products ORDER BY id")
    products = cursor.fetchall()
    
    content += "DROP TABLE IF EXISTS products;\n"
    content += """CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price INTEGER NOT NULL,
    cost_price INTEGER DEFAULT 0,
    stock INTEGER DEFAULT 0,
    category TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);\n\n"""
    
    for p in products:
        content += f"INSERT INTO products VALUES ({p['id']}, '{p['name'].replace("'", "''")}', {p['price']}, {p['cost_price']}, {p['stock']}, '{p['category'] or ''}', '{p['created_at']}');\n"
    
    # 2. Bảng khách hàng
    content += f"\n\n-- ============================================\n"
    content += f"-- 2. DANH SÁCH KHÁCH HÀNG ({cursor.execute('SELECT COUNT(*) FROM customers').fetchone()[0]} khách hàng)\n"
    content += f"-- ============================================\n\n"
    
    cursor.execute("SELECT * FROM customers ORDER BY id")
    customers = cursor.fetchall()
    
    content += "DROP TABLE IF EXISTS customers;\n"
    content += """CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    address TEXT,
    total_spent INTEGER DEFAULT 0,
    last_purchase TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);\n\n"""
    
    for c in customers:
        content += f"INSERT INTO customers VALUES ({c['id']}, '{c['name'].replace("'", "''")}', '{c['phone'] or ''}', '{c['email'] or ''}', '{c['address'] or ''}', {c['total_spent']}, '{c['last_purchase'] or ''}', '{c['created_at']}');\n"
    
    # 3. Bảng đơn hàng
    content += f"\n\n-- ============================================\n"
    content += f"-- 3. DANH SÁCH ĐƠN HÀNG ({cursor.execute('SELECT COUNT(*) FROM orders').fetchone()[0]} đơn hàng)\n"
    content += f"-- ============================================\n\n"
    
    cursor.execute("SELECT * FROM orders ORDER BY id")
    orders = cursor.fetchall()
    
    content += "DROP TABLE IF EXISTS orders;\n"
    content += """CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT UNIQUE NOT NULL,
    customer_id INTEGER,
    total_amount INTEGER NOT NULL,
    payment_method TEXT DEFAULT 'cash',
    status TEXT DEFAULT 'completed',
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);\n\n"""
    
    for o in orders:
        customer_id = o['customer_id'] if o['customer_id'] else 'NULL'
        content += f"INSERT INTO orders VALUES ({o['id']}, '{o['order_number']}', {customer_id}, {o['total_amount']}, '{o['payment_method']}', '{o['status']}', {o['created_by'] or 1}, '{o['created_at']}');\n"
    
    # 4. Bảng chi tiết đơn hàng
    content += f"\n\n-- ============================================\n"
    content += f"-- 4. CHI TIẾT ĐƠN HÀNG ({cursor.execute('SELECT COUNT(*) FROM order_items').fetchone()[0]} dòng)\n"
    content += f"-- ============================================\n\n"
    
    cursor.execute("SELECT * FROM order_items ORDER BY id")
    items = cursor.fetchall()
    
    content += "DROP TABLE IF EXISTS order_items;\n"
    content += """CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price INTEGER NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);\n\n"""
    
    for item in items:
        content += f"INSERT INTO order_items VALUES ({item['id']}, {item['order_id']}, {item['product_id']}, {item['quantity']}, {item['price']});\n"
    
    # 5. Thống kê tổng hợp
    content += f"\n\n-- ============================================\n"
    content += f"-- 5. THỐNG KÊ TỔNG HỢP\n"
    content += f"-- ============================================\n\n"
    
    # Thống kê doanh thu
    cursor.execute("SELECT SUM(total_amount) as total FROM orders WHERE status='completed'")
    total_revenue = cursor.fetchone()['total'] or 0
    
    cursor.execute("SELECT COUNT(*) as count FROM customers")
    total_customers = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM products")
    total_products = cursor.fetchone()['count']
    
    content += f"""
-- 📊 THỐNG KÊ:
-- Tổng sản phẩm: {total_products}
-- Tổng khách hàng: {total_customers}
-- Tổng doanh thu: {total_revenue:,.0f} VNĐ
-- Tổng đơn hàng: {len(orders)}
"""
    
    # Thống kê theo tháng
    content += f"\n-- 📅 DOANH THU THEO THÁNG:\n"
    cursor.execute("""
        SELECT strftime('%Y-%m', created_at) as month, 
               COUNT(*) as orders, 
               SUM(total_amount) as revenue
        FROM orders 
        WHERE status='completed'
        GROUP BY month
        ORDER BY month DESC
    """)
    monthly = cursor.fetchall()
    for m in monthly:
        content += f"-- {m['month']}: {m['orders']} đơn - {m['revenue']:,.0f} VNĐ\n"
    
    # Top sản phẩm bán chạy
    content += f"\n-- 🏆 TOP SẢN PHẨM BÁN CHẠY:\n"
    cursor.execute("""
        SELECT p.name, SUM(oi.quantity) as sold
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        GROUP BY p.id
        ORDER BY sold DESC
        LIMIT 5
    """)
    top_products = cursor.fetchall()
    for tp in top_products:
        content += f"-- {tp['name']}: {tp['sold']} sản phẩm\n"
    
    content += "\nCOMMIT;\n"
    
    conn.close()
    
    # Tạo file backup
    filename = f"backup_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    
    return content, 200, {
        'Content-Type': 'text/plain',
        'Content-Disposition': f'attachment; filename={filename}'
    }

# ==================== CHẠY APP ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

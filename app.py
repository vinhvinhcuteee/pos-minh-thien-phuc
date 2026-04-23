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
    try:
        result = db.client.table('products').select('*').order('id', desc=True).execute()
        return jsonify(result.data)
    except Exception as e:
        print(f"Lỗi: {e}")
        return jsonify([])

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
        result = db.client.table('products').insert(product_data).execute()
        return jsonify({'success': True, 'id': result.data[0]['id'] if result.data else None})
    except Exception as e:
        print(f"Lỗi: {e}")
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
        db.client.table('products').update(product_data).eq('id', product_id).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    try:
        db.client.table('products').delete().eq('id', product_id).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== API KHÁCH HÀNG ====================
@app.route('/api/customers', methods=['GET'])
@login_required
def get_customers():
    try:
        result = db.client.table('customers').select('*').order('total_spent', desc=True).execute()
        return jsonify(result.data)
    except Exception as e:
        return jsonify([])

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
        result = db.client.table('customers').insert(customer_data).execute()
        return jsonify({'success': True, 'id': result.data[0]['id'] if result.data else None})
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
        db.client.table('customers').update(customer_data).eq('id', customer_id).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
@login_required
def delete_customer(customer_id):
    try:
        # Kiểm tra xem khách hàng có đơn hàng không
        orders = db.client.table('orders').select('id', count='exact').eq('customer_id', customer_id).execute()
        if orders.count and orders.count > 0:
            return jsonify({'success': False, 'error': 'Khách hàng có đơn hàng, không thể xóa'}), 400
        db.client.table('customers').delete().eq('id', customer_id).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/customers/<int:customer_id>/history')
@login_required
def get_customer_history(customer_id):
    try:
        result = db.client.table('orders')\
            .select('*, order_items(*, products(name))')\
            .eq('customer_id', customer_id)\
            .order('created_at', desc=True)\
            .execute()
        
        history = []
        for order in result.data:
            for item in order.get('order_items', []):
                history.append({
                    'order_id': order['id'],
                    'order_number': order['order_number'],
                    'total_amount': order['total_amount'],
                    'created_at': order['created_at'],
                    'payment_method': order['payment_method'],
                    'product_name': item.get('products', {}).get('name', ''),
                    'quantity': item['quantity'],
                    'price': item['price']
                })
        return jsonify(history)
    except Exception as e:
        return jsonify([])

# ==================== API ĐƠN HÀNG ====================
@app.route('/api/orders', methods=['GET'])
@login_required
def get_orders():
    try:
        result = db.client.table('orders')\
            .select('*, customers(name)')\
            .order('created_at', desc=True)\
            .limit(50)\
            .execute()
        
        orders = []
        for order in result.data:
            orders.append({
                'id': order['id'],
                'order_number': order['order_number'],
                'customer_name': order.get('customers', {}).get('name', 'Khách lẻ'),
                'total_amount': order['total_amount'],
                'payment_method': order['payment_method'],
                'status': order['status'],
                'created_at': order['created_at']
            })
        return jsonify(orders)
    except Exception as e:
        return jsonify([])

@app.route('/api/orders', methods=['POST'])
@login_required
def create_order():
    try:
        data = request.json
        order_number = f"DH{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Tạo đơn hàng
        order_data = {
            'order_number': order_number,
            'customer_id': data.get('customer_id'),
            'total_amount': data['total_amount'],
            'payment_method': data.get('payment_method', 'cash'),
            'status': 'completed',
            'created_by': 1
        }
        result = db.client.table('orders').insert(order_data).execute()
        
        if not result.data:
            return jsonify({'success': False, 'error': 'Không thể tạo đơn hàng'}), 500
        
        order_id = result.data[0]['id']
        
        # Thêm chi tiết đơn hàng và cập nhật tồn kho
        for item in data['items']:
            # Thêm order item
            db.client.table('order_items').insert({
                'order_id': order_id,
                'product_id': item['id'],
                'quantity': item['quantity'],
                'price': item['price']
            }).execute()
            
            # Giảm tồn kho
            product = db.client.table('products').select('stock').eq('id', item['id']).execute()
            if product.data:
                new_stock = product.data[0]['stock'] - item['quantity']
                db.client.table('products').update({'stock': new_stock}).eq('id', item['id']).execute()
        
        # Cập nhật tổng chi tiêu khách hàng
        if data.get('customer_id'):
            customer = db.client.table('customers').select('total_spent').eq('id', data['customer_id']).execute()
            if customer.data:
                new_total = customer.data[0]['total_spent'] + data['total_amount']
                db.client.table('customers').update({
                    'total_spent': new_total,
                    'last_purchase': datetime.now().isoformat()
                }).eq('id', data['customer_id']).execute()
        
        return jsonify({'success': True, 'order_id': order_id, 'order_number': order_number})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== API HÓA ĐƠN ====================
@app.route('/api/invoices', methods=['GET'])
@login_required
def get_invoices():
    try:
        filter_type = request.args.get('filter', 'all')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = db.client.table('orders')\
            .select('*, order_items(*, products(name))')\
            .eq('status', 'completed')\
            .order('created_at', desc=True)
        
        if filter_type == 'today':
            today = datetime.now().date().isoformat()
            query = query.gte('created_at', today)
        elif filter_type == 'week':
            week_ago = (datetime.now() - timedelta(days=7)).date().isoformat()
            query = query.gte('created_at', week_ago)
        elif filter_type == 'month':
            month_ago = (datetime.now() - timedelta(days=30)).date().isoformat()
            query = query.gte('created_at', month_ago)
        
        if start_date:
            query = query.gte('created_at', start_date)
        if end_date:
            query = query.lte('created_at', end_date)
        
        result = query.execute()
        
        invoices = []
        for order in result.data:
            for item in order.get('order_items', []):
                invoices.append({
                    'order_number': order['order_number'],
                    'created_at': order['created_at'],
                    'product_name': item.get('products', {}).get('name', ''),
                    'quantity': item['quantity'],
                    'price': item['price'],
                    'subtotal': item['quantity'] * item['price'],
                    'total_amount': order['total_amount']
                })
        return jsonify(invoices)
    except Exception as e:
        return jsonify([])

# ==================== API THỐNG KÊ ====================
@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    try:
        # Tổng số
        products_count = db.client.table('products').select('id', count='exact').execute().count or 0
        customers_count = db.client.table('customers').select('id', count='exact').execute().count or 0
        orders_count = db.client.table('orders').select('id', count='exact').eq('status', 'completed').execute().count or 0
        
        # Doanh thu hôm nay
        today = datetime.now().date().isoformat()
        today_orders = db.client.table('orders').select('total_amount').eq('status', 'completed').gte('created_at', today).execute()
        today_revenue = sum(o['total_amount'] for o in today_orders.data)
        
        # Doanh thu tháng này
        first_day = datetime.now().replace(day=1).date().isoformat()
        month_orders = db.client.table('orders').select('total_amount').eq('status', 'completed').gte('created_at', first_day).execute()
        month_revenue = sum(o['total_amount'] for o in month_orders.data)
        
        return jsonify({
            'total_products': products_count,
            'total_customers': customers_count,
            'total_orders': orders_count,
            'today_revenue': today_revenue,
            'month_revenue': month_revenue,
            'profit': month_revenue * 0.3,
            'profit_margin': 30,
            'top_products': []
        })
    except Exception as e:
        return jsonify({
            'total_products': 0, 'total_customers': 0, 'total_orders': 0,
            'today_revenue': 0, 'month_revenue': 0, 'profit': 0, 'profit_margin': 0, 'top_products': []
        })

# ==================== CHẠY APP ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

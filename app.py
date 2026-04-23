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

# ==================== QUẢN LÝ SẢN PHẨM ====================
@app.route('/products')
@login_required
def products_page():
    return render_template('products.html')

@app.route('/api/products', methods=['GET'])
@login_required
def get_products():
    """Lấy danh sách sản phẩm"""
    try:
        result = db.client.table('products').select('*').order('id', desc=True).execute()
        return jsonify(result.data)
    except Exception as e:
        print(f"❌ Lỗi get_products: {e}")
        return jsonify([])

@app.route('/api/products', methods=['POST'])
@login_required
def add_product():
    """Thêm sản phẩm mới"""
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
        if result.data:
            return jsonify({'success': True, 'id': result.data[0]['id']})
        else:
            return jsonify({'success': False, 'error': 'Không thể thêm sản phẩm'}), 500
    except Exception as e:
        print(f"❌ Lỗi add_product: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    """Cập nhật sản phẩm"""
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
        print(f"❌ Lỗi update_product: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    """Xóa sản phẩm"""
    try:
        db.client.table('products').delete().eq('id', product_id).execute()
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Lỗi delete_product: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== QUẢN LÝ KHÁCH HÀNG ====================
@app.route('/customers')
@login_required
def customers_page():
    return render_template('customers.html')

@app.route('/api/customers', methods=['GET'])
@login_required
def get_customers():
    """Lấy danh sách khách hàng"""
    try:
        result = db.client.table('customers').select('*').order('total_spent', desc=True).execute()
        return jsonify(result.data)
    except Exception as e:
        print(f"❌ Lỗi get_customers: {e}")
        return jsonify([])

@app.route('/api/customers', methods=['POST'])
@login_required
def add_customer():
    """Thêm khách hàng mới"""
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
        if result.data:
            return jsonify({'success': True, 'id': result.data[0]['id']})
        else:
            return jsonify({'success': False, 'error': 'Không thể thêm khách hàng'}), 500
    except Exception as e:
        print(f"❌ Lỗi add_customer: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
@login_required
def update_customer(customer_id):
    """Cập nhật khách hàng"""
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
        print(f"❌ Lỗi update_customer: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
@login_required
def delete_customer(customer_id):
    """Xóa khách hàng"""
    try:
        # Kiểm tra xem khách hàng có đơn hàng không
        orders = db.client.table('orders').select('id', count='exact').eq('customer_id', customer_id).execute()
        if orders.count and orders.count > 0:
            return jsonify({'success': False, 'error': 'Khách hàng có đơn hàng, không thể xóa'}), 400
        
        db.client.table('customers').delete().eq('id', customer_id).execute()
        return jsonify({'success': True})
    except Exception as e:
        print(f"❌ Lỗi delete_customer: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/customers/<int:customer_id>/history')
@login_required
def get_customer_history(customer_id):
    """Lấy lịch sử mua hàng của khách hàng"""
    try:
        # Lấy tất cả đơn hàng của khách hàng kèm chi tiết sản phẩm
        result = db.client.table('orders')\
            .select('*, order_items(*, products(name))')\
            .eq('customer_id', customer_id)\
            .order('created_at', desc=True)\
            .execute()
        
        # Format lại dữ liệu để dễ xử lý trên frontend
        history = []
        for order in result.data:
            for item in order.get('order_items', []):
                history.append({
                    'order_id': order['id'],
                    'order_number': order['order_number'],
                    'total_amount': order['total_amount'],
                    'created_at': order['created_at'],
                    'payment_method': order['payment_method'],
                    'product_id': item['product_id'],
                    'product_name': item['products']['name'] if item.get('products') else '',
                    'quantity': item['quantity'],
                    'price': item['price']
                })
        
        return jsonify(history)
    except Exception as e:
        print(f"❌ Lỗi get_customer_history: {e}")
        return jsonify([])

# ==================== QUẢN LÝ ĐƠN HÀNG ====================
@app.route('/api/orders', methods=['GET'])
@login_required
def get_orders():
    """Lấy danh sách đơn hàng"""
    try:
        result = db.client.table('orders')\
            .select('*, customers(name)')\
            .order('created_at', desc=True)\
            .limit(50)\
            .execute()
        
        # Format lại dữ liệu
        orders = []
        for order in result.data:
            orders.append({
                'id': order['id'],
                'order_number': order['order_number'],
                'customer_id': order.get('customer_id'),
                'customer_name': order['customers']['name'] if order.get('customers') else 'Khách lẻ',
                'total_amount': order['total_amount'],
                'payment_method': order['payment_method'],
                'status': order['status'],
                'created_at': order['created_at']
            })
        
        return jsonify(orders)
    except Exception as e:
        print(f"❌ Lỗi get_orders: {e}")
        return jsonify([])

@app.route('/api/orders', methods=['POST'])
@login_required
def create_order():
    """Tạo đơn hàng mới"""
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
            order_item = {
                'order_id': order_id,
                'product_id': item['id'],
                'quantity': item['quantity'],
                'price': item['price']
            }
            db.client.table('order_items').insert(order_item).execute()
            
            # Giảm tồn kho
            product = db.client.table('products').select('stock').eq('id', item['id']).execute()
            if product.data:
                new_stock = product.data[0]['stock'] - item['quantity']
                db.client.table('products').update({'stock': new_stock}).eq('id', item['id']).execute()
        
        # Cập nhật tổng chi tiêu của khách hàng
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
        print(f"❌ Lỗi create_order: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== HÓA ĐƠN ====================
@app.route('/invoices')
@login_required
def invoices_page():
    return render_template('invoices.html')

@app.route('/api/invoices', methods=['GET'])
@login_required
def get_invoices():
    """Lấy danh sách hóa đơn"""
    try:
        filter_type = request.args.get('filter', 'all')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Xây dựng query
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
        
        # Format lại dữ liệu
        invoices = []
        for order in result.data:
            for item in order.get('order_items', []):
                invoices.append({
                    'order_number': order['order_number'],
                    'created_at': order['created_at'],
                    'product_name': item['products']['name'] if item.get('products') else '',
                    'quantity': item['quantity'],
                    'price': item['price'],
                    'subtotal': item['quantity'] * item['price'],
                    'total_amount': order['total_amount']
                })
        
        return jsonify(invoices)
    except Exception as e:
        print(f"❌ Lỗi get_invoices: {e}")
        return jsonify([])

# ==================== BÁO CÁO THỐNG KÊ ====================
@app.route('/reports')
@login_required
def reports_page():
    return render_template('reports.html')

@app.route('/api/stats', methods=['GET'])
@login_required
def get_stats():
    """Lấy thống kê tổng quan"""
    try:
        # Tổng số sản phẩm
        products_result = db.client.table('products').select('id', count='exact').execute()
        total_products = products_result.count or 0
        
        # Tổng số khách hàng
        customers_result = db.client.table('customers').select('id', count='exact').execute()
        total_customers = customers_result.count or 0
        
        # Tổng số đơn hàng hoàn thành
        orders_result = db.client.table('orders').select('id', count='exact').eq('status', 'completed').execute()
        total_orders = orders_result.count or 0
        
        # Doanh thu hôm nay
        today = datetime.now().date().isoformat()
        today_result = db.client.table('orders')\
            .select('total_amount')\
            .eq('status', 'completed')\
            .gte('created_at', today)\
            .execute()
        today_revenue = sum(order['total_amount'] for order in today_result.data)
        
        # Doanh thu tháng này
        first_day_of_month = datetime.now().replace(day=1).date().isoformat()
        month_result = db.client.table('orders')\
            .select('total_amount')\
            .eq('status', 'completed')\
            .gte('created_at', first_day_of_month)\
            .execute()
        month_revenue = sum(order['total_amount'] for order in month_result.data)
        
        # Lợi nhuận tháng này
        profit_result = db.client.table('order_items')\
            .select('quantity, price, products(cost_price)')\
            .execute()
        
        revenue = 0
        cost = 0
        for item in profit_result.data:
            revenue += item['quantity'] * item['price']
            if item.get('products'):
                cost += item['quantity'] * item['products']['cost_price']
        
        profit = revenue - cost
        profit_margin = (profit / revenue * 100) if revenue > 0 else 0
        
        # Top sản phẩm bán chạy
        top_products_result = db.client.table('order_items')\
            .select('products(name), quantity')\
            .execute()
        
        product_sales = {}
        for item in top_products_result.data:
            name = item['products']['name'] if item.get('products') else 'Unknown'
            product_sales[name] = product_sales.get(name, 0) + item['quantity']
        
        top_products = [{'name': k, 'total_sold': v} for k, v in sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]]
        
        return jsonify({
            'total_products': total_products,
            'total_customers': total_customers,
            'total_orders': total_orders,
            'today_revenue': today_revenue,
            'month_revenue': month_revenue,
            'profit': profit,
            'profit_margin': profit_margin,
            'top_products': top_products
        })
    except Exception as e:
        print(f"❌ Lỗi get_stats: {e}")
        return jsonify({
            'total_products': 0,
            'total_customers': 0,
            'total_orders': 0,
            'today_revenue': 0,
            'month_revenue': 0,
            'profit': 0,
            'profit_margin': 0,
            'top_products': []
        })

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
            
            # Lấy dữ liệu theo ngày trong tháng
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
            
            # Lấy số ngày trong tháng
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
            
            # Lấy dữ liệu theo tháng trong năm
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
        print(f"❌ Lỗi report_detail: {e}")
        return jsonify([])

# ==================== CHẠY APP ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

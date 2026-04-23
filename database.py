import os
from supabase import create_client, Client

class Database:
    def __init__(self):
        self.client: Client = None
        self.connect()

    def connect(self):
        try:
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            print("=" * 50)
            print("ĐANG KẾT NỐI SUPABASE...")
            print("=" * 50)
            
            if not supabase_url or not supabase_key:
                print("❌ LỖI: Thiếu SUPABASE_URL hoặc SUPABASE_KEY!")
                return
            
            print(f"📡 URL: {supabase_url}")
            self.client = create_client(supabase_url, supabase_key)
            print("✅ KẾT NỐI THÀNH CÔNG!")
            
            # Kiểm tra quyền truy cập
            result = self.client.table('products').select('*', count='exact').limit(1).execute()
            print(f"✅ Có thể đọc bảng products! ({result.count} sản phẩm)")
            
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ LỖI KẾT NỐI: {e}")

    # ==================== SẢN PHẨM ====================
    def get_all_products(self):
        try:
            result = self.client.table('products').select('*').order('id', desc=True).execute()
            return result.data
        except Exception as e:
            print(f"Lỗi get_all_products: {e}")
            return []

    def add_product(self, data):
        try:
            result = self.client.table('products').insert(data).execute()
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            print(f"Lỗi add_product: {e}")
            return None

    def update_product(self, product_id, data):
        try:
            self.client.table('products').update(data).eq('id', product_id).execute()
            return True
        except Exception as e:
            print(f"Lỗi update_product: {e}")
            return False

    def delete_product(self, product_id):
        try:
            self.client.table('products').delete().eq('id', product_id).execute()
            return True
        except Exception as e:
            print(f"Lỗi delete_product: {e}")
            return False

    # ==================== KHÁCH HÀNG ====================
    def get_all_customers(self):
        try:
            result = self.client.table('customers').select('*').order('total_spent', desc=True).execute()
            return result.data
        except Exception as e:
            print(f"Lỗi get_all_customers: {e}")
            return []

    def add_customer(self, data):
        try:
            result = self.client.table('customers').insert(data).execute()
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            print(f"Lỗi add_customer: {e}")
            return None

    def update_customer(self, customer_id, data):
        try:
            self.client.table('customers').update(data).eq('id', customer_id).execute()
            return True
        except Exception as e:
            print(f"Lỗi update_customer: {e}")
            return False

    def delete_customer(self, customer_id):
        try:
            self.client.table('customers').delete().eq('id', customer_id).execute()
            return True, ""
        except Exception as e:
            print(f"Lỗi delete_customer: {e}")
            return False, str(e)

    def get_customer_history(self, customer_id):
        try:
            result = self.client.table('orders')\
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
            return history
        except Exception as e:
            print(f"Lỗi get_customer_history: {e}")
            return []

    # ==================== ĐƠN HÀNG ====================
    def get_all_orders(self):
        try:
            result = self.client.table('orders')\
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
            return orders
        except Exception as e:
            print(f"Lỗi get_all_orders: {e}")
            return []

    def create_order(self, order_data, items):
        try:
            # Tạo đơn hàng
            result = self.client.table('orders').insert(order_data).execute()
            if not result.data:
                return None, "Không thể tạo đơn hàng"
            
            order_id = result.data[0]['id']
            
            # Thêm chi tiết đơn hàng
            for item in items:
                self.client.table('order_items').insert({
                    'order_id': order_id,
                    'product_id': item['id'],
                    'quantity': item['quantity'],
                    'price': item['price']
                }).execute()
                
                # Cập nhật tồn kho
                product = self.client.table('products').select('stock').eq('id', item['id']).execute()
                if product.data:
                    new_stock = product.data[0]['stock'] - item['quantity']
                    self.client.table('products').update({'stock': new_stock}).eq('id', item['id']).execute()
            
            # Cập nhật tổng chi tiêu khách hàng
            if order_data.get('customer_id'):
                customer = self.client.table('customers').select('total_spent').eq('id', order_data['customer_id']).execute()
                if customer.data:
                    new_total = customer.data[0]['total_spent'] + order_data['total_amount']
                    self.client.table('customers').update({
                        'total_spent': new_total,
                        'last_purchase': datetime.now().isoformat()
                    }).eq('id', order_data['customer_id']).execute()
            
            return order_id, None
        except Exception as e:
            print(f"Lỗi create_order: {e}")
            return None, str(e)

    # ==================== HÓA ĐƠN ====================
    def get_invoices(self, filter_type='all', start_date=None, end_date=None):
        try:
            from datetime import datetime, timedelta
            
            query = self.client.table('orders')\
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
            return invoices
        except Exception as e:
            print(f"Lỗi get_invoices: {e}")
            return []

    # ==================== THỐNG KÊ ====================
    def get_stats(self):
        try:
            from datetime import datetime
            
            products_count = self.client.table('products').select('id', count='exact').execute().count or 0
            customers_count = self.client.table('customers').select('id', count='exact').execute().count or 0
            orders_count = self.client.table('orders').select('id', count='exact').eq('status', 'completed').execute().count or 0
            
            today = datetime.now().date().isoformat()
            today_orders = self.client.table('orders').select('total_amount').eq('status', 'completed').gte('created_at', today).execute()
            today_revenue = sum(o['total_amount'] for o in today_orders.data)
            
            first_day = datetime.now().replace(day=1).date().isoformat()
            month_orders = self.client.table('orders').select('total_amount').eq('status', 'completed').gte('created_at', first_day).execute()
            month_revenue = sum(o['total_amount'] for o in month_orders.data)
            
            return {
                'total_products': products_count,
                'total_customers': customers_count,
                'total_orders': orders_count,
                'today_revenue': today_revenue,
                'month_revenue': month_revenue,
                'profit': month_revenue * 0.3,
                'profit_margin': 30,
                'top_products': []
            }
        except Exception as e:
            print(f"Lỗi get_stats: {e}")
            return {
                'total_products': 0, 'total_customers': 0, 'total_orders': 0,
                'today_revenue': 0, 'month_revenue': 0, 'profit': 0, 'profit_margin': 0, 'top_products': []
            }

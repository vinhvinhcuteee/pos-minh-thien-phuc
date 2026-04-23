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
            
            print("==================================================")
            print("ĐANG KẾT NỐI SUPABASE VIA CLIENT...")
            print("==================================================")
            
            if not supabase_url or not supabase_key:
                print("❌ LỖI: Thiếu SUPABASE_URL hoặc SUPABASE_KEY trong biến môi trường!")
                return
            
            print(f"📡 SUPABASE_URL: {supabase_url}")
            self.client = create_client(supabase_url, supabase_key)
            print("✅ KẾT NỐI SUPABASE THÀNH CÔNG!")
            
            # Kiểm tra kết nối bằng cách đọc bảng products
            try:
                result = self.client.table('products').select('*', count='exact').limit(1).execute()
                print("✅ Kiểm tra kết nối thành công! (Đã tìm thấy bảng 'products')")
            except Exception as e:
                print(f"⚠️ Cảnh báo: Không thể truy cập bảng 'products' - {e}")
                print("   Hãy chắc chắn bạn đã tạo các bảng cần thiết trong Supabase.")
            
            print("==================================================")
            
        except Exception as e:
            print(f"❌ LỖI KẾT NỐI SUPABASE: {e}")

    # --- Các hàm mới, đúng chuẩn Supabase ---
    def get_all_products(self):
        """Lấy tất cả sản phẩm"""
        try:
            result = self.client.table('products').select('*').order('id', desc=True).execute()
            return result.data
        except Exception as e:
            print(f"❌ Lỗi lấy sản phẩm: {e}")
            return []

    def add_product(self, product_data):
        """Thêm sản phẩm mới"""
        try:
            result = self.client.table('products').insert(product_data).execute()
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            print(f"❌ Lỗi thêm sản phẩm: {e}")
            return None

    def update_product(self, product_id, product_data):
        """Cập nhật sản phẩm"""
        try:
            self.client.table('products').update(product_data).eq('id', product_id).execute()
            return True
        except Exception as e:
            print(f"❌ Lỗi cập nhật sản phẩm {product_id}: {e}")
            return False

    def delete_product(self, product_id):
        """Xóa sản phẩm"""
        try:
            self.client.table('products').delete().eq('id', product_id).execute()
            return True
        except Exception as e:
            print(f"❌ Lỗi xóa sản phẩm {product_id}: {e}")
            return False

    # --- Thêm các hàm tương tự cho Customers, Orders ---
    def get_all_customers(self):
        try:
            result = self.client.table('customers').select('*').order('total_spent', desc=True).execute()
            return result.data
        except Exception as e:
            print(f"❌ Lỗi lấy khách hàng: {e}")
            return []

    def add_customer(self, customer_data):
        try:
            result = self.client.table('customers').insert(customer_data).execute()
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            print(f"❌ Lỗi thêm khách hàng: {e}")
            return None
            
    # Bạn cần viết thêm các hàm cho orders, order_items dựa trên cấu trúc này.

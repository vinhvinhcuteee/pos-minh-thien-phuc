import os
from supabase import create_client, Client

class Database:
    def __init__(self):
        self.supabase = None
        self.connect()

    def connect(self):
        try:
            # Lấy thông tin từ biến môi trường
            supabase_url = os.environ.get('SUPABASE_URL')
            supabase_key = os.environ.get('SUPABASE_KEY')
            
            print("=" * 50)
            print("ĐANG KẾT NỐI SUPABASE...")
            print("=" * 50)
            
            if not supabase_url or not supabase_key:
                print("❌ LỖI: Thiếu SUPABASE_URL hoặc SUPABASE_KEY!")
                print("   Vui lòng thêm trên Render Dashboard:")
                print("   - SUPABASE_URL: https://nlwtdvrspsheasqmyyqny.supabase.co")
                print("   - SUPABASE_KEY: (anon public key từ Supabase)")
                return
            
            print(f"📡 SUPABASE_URL: {supabase_url}")
            self.supabase = create_client(supabase_url, supabase_key)
            print("✅ KẾT NỐI SUPABASE THÀNH CÔNG!")
            print("=" * 50)
            
            # Tạo bảng nếu chưa có (dùng SQL thuần)
            self.create_tables_if_not_exist()
            
        except Exception as e:
            print(f"❌ LỖI KẾT NỐI: {e}")

    def create_tables_if_not_exist(self):
        """Kiểm tra và tạo bảng nếu chưa có"""
        try:
            # Kiểm tra xem bảng products có tồn tại không
            result = self.supabase.table('products').select('*', count='exact').limit(1).execute()
            print("✅ Các bảng đã tồn tại!")
        except Exception as e:
            print("⚠️ Bảng chưa tồn tại, hãy tạo thủ công trên Supabase SQL Editor")
            print("   Vào Supabase → SQL Editor → Chạy lệnh tạo bảng")

    def execute_query(self, query, params=None):
        """Thực thi query (dùng cho INSERT, UPDATE, DELETE)"""
        # Phương pháp đơn giản: không dùng query raw, dùng supabase client
        print(f"⚠️ execute_query không được hỗ trợ trong client mode")
        return None

    def fetch_all(self, table_name, filters=None):
        """Lấy tất cả dữ liệu từ bảng"""
        try:
            query = self.supabase.table(table_name).select('*')
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            result = query.execute()
            return result.data
        except Exception as e:
            print(f"❌ Lỗi fetch_all từ {table_name}: {e}")
            return []

    def fetch_one(self, table_name, filters=None):
        """Lấy một dòng dữ liệu"""
        try:
            query = self.supabase.table(table_name).select('*').limit(1)
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            result = query.execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"❌ Lỗi fetch_one từ {table_name}: {e}")
            return None

    def insert(self, table_name, data):
        """Thêm dữ liệu vào bảng"""
        try:
            result = self.supabase.table(table_name).insert(data).execute()
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            print(f"❌ Lỗi insert vào {table_name}: {e}")
            return None

    def update(self, table_name, id, data):
        """Cập nhật dữ liệu"""
        try:
            result = self.supabase.table(table_name).update(data).eq('id', id).execute()
            return True
        except Exception as e:
            print(f"❌ Lỗi update {table_name}: {e}")
            return False

    def delete(self, table_name, id):
        """Xóa dữ liệu"""
        try:
            self.supabase.table(table_name).delete().eq('id', id).execute()
            return True
        except Exception as e:
            print(f"❌ Lỗi delete từ {table_name}: {e}")
            return False

    def close(self):
        pass

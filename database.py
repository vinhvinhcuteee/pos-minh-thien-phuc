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
            
            # Kiểm tra kết nối
            result = self.client.table('products').select('*', count='exact').limit(1).execute()
            print(f"✅ Kết nối hoạt động tốt! (Tìm thấy bảng 'products' với {result.count} sản phẩm)")
            
            print("==================================================")
            
        except Exception as e:
            print(f"❌ LỖI KẾT NỐI SUPABASE: {e}")

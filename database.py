import psycopg2
import psycopg2.extras
import os
from urllib.parse import urlparse

class Database:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        try:
            # Lấy DATABASE_URL từ biến môi trường
            database_url = os.environ.get('DATABASE_URL')
            
            print("=" * 50)
            print("ĐANG KẾT NỐI DATABASE...")
            print("=" * 50)
            
            if not database_url:
                print("❌ LỖI: Không tìm thấy biến môi trường DATABASE_URL!")
                print("   Vui lòng thêm DATABASE_URL trên Render Dashboard")
                self.connection = None
                return
            
            # In ra 50 ký tự đầu của URL để debug (che mật khẩu)
            masked_url = database_url[:50] + "..." if len(database_url) > 50 else database_url
            print(f"📡 DATABASE_URL (50 ký tự đầu): {masked_url}")
            
            # Xử lý URL cho Supabase
            if 'supabase' in database_url or 'pooler' in database_url:
                # Đảm bảo dùng Session Pooler (cổng 6543)
                if ':5432' in database_url:
                    database_url = database_url.replace(':5432', ':6543')
                    print("✅ Đã chuyển sang cổng Session Pooler (6543)")
                
                # Thêm sslmode=require nếu chưa có
                if 'sslmode' not in database_url:
                    if '?' in database_url:
                        database_url += '&sslmode=require'
                    else:
                        database_url += '?sslmode=require'
                    print("✅ Đã thêm sslmode=require")
                
                # Chuyển postgres:// thành postgresql:// nếu cần
                if database_url.startswith('postgres://'):
                    database_url = database_url.replace('postgres://', 'postgresql://', 1)
                    print("✅ Đã chuyển postgres:// -> postgresql://")
            
            # Thử kết nối
            print("🔄 Đang kết nối đến Supabase...")
            self.connection = psycopg2.connect(database_url)
            self.connection.autocommit = False
            
            print("✅ KẾT NỐI THÀNH CÔNG!")
            print("=" * 50)
            
            # Tạo bảng và dữ liệu mẫu
            self.create_tables()
            
        except psycopg2.OperationalError as e:
            print(f"❌ LỖI KẾT NỐI (OperationalError): {e}")
            print("\n🔧 KIỂM TRA LẠI:")
            print("   1. DATABASE_URL có đúng định dạng Session Pooler không?")
            print("   2. Cổng có phải 6543 không?")
            print("   3. Có ?sslmode=require ở cuối không?")
            print("   4. Mật khẩu có đúng không?")
            print("   5. Tên user có bao gồm project ID không? (postgres.xxxxx)")
            self.connection = None
        except psycopg2.Error as e:
            print(f"❌ LỖI PSYCOPG2: {e}")
            print(f"   Loại lỗi: {type(e).__name__}")
            self.connection = None
        except Exception as e:
            print(f"❌ LỖI KHÔNG XÁC ĐỊNH: {e}")
            print(f"   Loại lỗi: {type(e).__name__}")
            self.connection = None

    def create_tables(self):
        if not self.connection:
            print("❌ Không thể tạo bảng vì chưa kết nối database!")
            return
            
        cursor = self.connection.cursor()
        print("\n🏗️ ĐANG TẠO BẢNG...")
        
        try:
            # Bảng sản phẩm
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    price DECIMAL(15,0) NOT NULL,
                    cost_price DECIMAL(15,0) DEFAULT 0,
                    stock INTEGER DEFAULT 0,
                    category VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Bảng khách hàng
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    phone VARCHAR(20),
                    email VARCHAR(255),
                    address TEXT,
                    total_spent DECIMAL(15,0) DEFAULT 0,
                    last_purchase TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Bảng đơn hàng
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id SERIAL PRIMARY KEY,
                    order_number VARCHAR(50) UNIQUE NOT NULL,
                    customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
                    total_amount DECIMAL(15,0) NOT NULL,
                    payment_method VARCHAR(50) DEFAULT 'cash',
                    status VARCHAR(50) DEFAULT 'completed',
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Bảng chi tiết đơn hàng
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    id SERIAL PRIMARY KEY,
                    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
                    product_id INTEGER REFERENCES products(id),
                    quantity INTEGER NOT NULL,
                    price DECIMAL(15,0) NOT NULL
                )
            """)
            
            # Bảng theo dõi trạng thái đơn hàng
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_status_log (
                    id SERIAL PRIMARY KEY,
                    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
                    old_status VARCHAR(50),
                    new_status VARCHAR(50),
                    changed_by INTEGER,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT
                )
            """)
            
            # Bảng hoàn trả
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS refunds (
                    id SERIAL PRIMARY KEY,
                    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
                    amount DECIMAL(15,0) NOT NULL,
                    reason TEXT,
                    refunded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.connection.commit()
            print("✅ ĐÃ TẠO/CẬP NHẬT BẢNG THÀNH CÔNG!")
            
            # Thêm dữ liệu mẫu
            self.insert_sample_data()
            
        except Exception as e:
            print(f"❌ LỖI TẠO BẢNG: {e}")
            self.connection.rollback()
        finally:
            cursor.close()

    def insert_sample_data(self):
        if not self.connection:
            print("❌ Không thể thêm dữ liệu mẫu vì chưa kết nối database!")
            return
            
        cursor = self.connection.cursor()
        print("\n📦 ĐANG KIỂM TRA DỮ LIỆU MẪU...")
        
        try:
            # Thêm sản phẩm mẫu
            cursor.execute("SELECT COUNT(*) FROM products")
            count = cursor.fetchone()[0]
            
            if count == 0:
                print("   Thêm sản phẩm mẫu...")
                sample_products = [
                    ('Cà phê đen', 15000, 8000, 100, 'Đồ uống'),
                    ('Cà phê sữa', 20000, 10000, 100, 'Đồ uống'),
                    ('Bánh mì thịt', 25000, 15000, 50, 'Đồ ăn'),
                    ('Trà đào', 30000, 18000, 80, 'Đồ uống'),
                    ('Nước ép cam', 35000, 20000, 60, 'Đồ uống'),
                ]
                for p in sample_products:
                    cursor.execute("""
                        INSERT INTO products (name, price, cost_price, stock, category)
                        VALUES (%s, %s, %s, %s, %s)
                    """, p)
                print("   ✅ Đã thêm 5 sản phẩm mẫu")
            else:
                print(f"   ℹ️ Đã có {count} sản phẩm trong database")
            
            # Thêm khách hàng mẫu
            cursor.execute("SELECT COUNT(*) FROM customers")
            count = cursor.fetchone()[0]
            
            if count == 0:
                print("   Thêm khách hàng mẫu...")
                sample_customers = [
                    ('Nguyễn Văn A', '0987654321', 'a@gmail.com', 'Hà Nội'),
                    ('Trần Thị B', '0978123456', 'b@gmail.com', 'TP HCM'),
                    ('Lê Văn C', '0965111222', 'c@gmail.com', 'Đà Nẵng'),
                ]
                for c in sample_customers:
                    cursor.execute("""
                        INSERT INTO customers (name, phone, email, address)
                        VALUES (%s, %s, %s, %s)
                    """, c)
                print("   ✅ Đã thêm 3 khách hàng mẫu")
            else:
                print(f"   ℹ️ Đã có {count} khách hàng trong database")
            
            self.connection.commit()
            print("✅ DỮ LIỆU MẪU HOÀN TẤT!")
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ LỖI THÊM DỮ LIỆU MẪU: {e}")
            self.connection.rollback()
        finally:
            cursor.close()

    def execute_query(self, query, params=None):
        if not self.connection:
            print("❌ Lỗi: Chưa kết nối database!")
            return None
            
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params or ())
            self.connection.commit()
            # Lấy ID nếu là INSERT
            if query.strip().upper().startswith('INSERT'):
                cursor.execute("SELECT LASTVAL()")
                result = cursor.fetchone()
                return result[0] if result else None
            return None
        except Exception as e:
            print(f"❌ Lỗi query: {e}")
            print(f"   Query: {query[:200]}")
            self.connection.rollback()
            return None
        finally:
            cursor.close()

    def fetch_all(self, query, params=None):
        if not self.connection:
            print("❌ Lỗi: Chưa kết nối database!")
            return []
            
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Lỗi fetch_all: {e}")
            return []
        finally:
            cursor.close()

    def fetch_one(self, query, params=None):
        if not self.connection:
            print("❌ Lỗi: Chưa kết nối database!")
            return None
            
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchone()
        except Exception as e:
            print(f"❌ Lỗi fetch_one: {e}")
            return None
        finally:
            cursor.close()

    def close(self):
        if self.connection:
            self.connection.close()
            print("🔌 Đã đóng kết nối database")

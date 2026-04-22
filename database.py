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
            
            if database_url:
                # Xử lý URL cho Supabase
                if 'supabase' in database_url:
                    # Supabase cần ?sslmode=require ở cuối
                    if 'sslmode' not in database_url:
                        if '?' in database_url:
                            database_url += '&sslmode=require'
                        else:
                            database_url += '?sslmode=require'
                    
                    # Chuyển postgres:// thành postgresql:// nếu cần
                    if database_url.startswith('postgres://'):
                        database_url = database_url.replace('postgres://', 'postgresql://', 1)
                
                self.connection = psycopg2.connect(database_url)
                print("✅ Kết nối Supabase thành công!")
            else:
                # Local development - dùng localhost
                self.connection = psycopg2.connect(
                    host='localhost',
                    database='pos_db',
                    user='postgres',
                    password='your_password'
                )
                print("✅ Kết nối database local thành công!")
            
            # Kiểm tra kết nối
            self.connection.autocommit = False
            self.create_tables()
            
        except Exception as e:
            print(f"❌ Lỗi kết nối database: {e}")
            print("\n🔧 Kiểm tra lại:")
            print("1. DATABASE_URL đã được set trên Render chưa?")
            print("2. Mật khẩu Supabase có đúng không?")
            print("3. URL có bắt đầu bằng postgresql:// không?")

    def create_tables(self):
        cursor = self.connection.cursor()
        
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
        
        # Thêm dữ liệu mẫu nếu chưa có
        self.insert_sample_data()
        cursor.close()

    def insert_sample_data(self):
        cursor = self.connection.cursor()
        
        try:
            # Thêm sản phẩm mẫu
            cursor.execute("SELECT COUNT(*) FROM products")
            if cursor.fetchone()[0] == 0:
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
                print("✅ Đã thêm sản phẩm mẫu")
            
            # Thêm khách hàng mẫu
            cursor.execute("SELECT COUNT(*) FROM customers")
            if cursor.fetchone()[0] == 0:
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
                print("✅ Đã thêm khách hàng mẫu")
            
            self.connection.commit()
        except Exception as e:
            print(f"Lỗi khi thêm dữ liệu mẫu: {e}")
            self.connection.rollback()
        finally:
            cursor.close()

    def execute_query(self, query, params=None):
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
            print(f"Lỗi query: {e}")
            self.connection.rollback()
            return None
        finally:
            cursor.close()

    def fetch_all(self, query, params=None):
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Exception as e:
            print(f"Lỗi fetch: {e}")
            return []
        finally:
            cursor.close()

    def fetch_one(self, query, params=None):
        cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            cursor.execute(query, params or ())
            return cursor.fetchone()
        except Exception as e:
            print(f"Lỗi fetch: {e}")
            return None
        finally:
            cursor.close()

    def close(self):
        if self.connection:
            self.connection.close()

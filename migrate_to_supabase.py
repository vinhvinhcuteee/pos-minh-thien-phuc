#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script migrate dữ liệu từ Render PostgreSQL sang Supabase
Cách dùng:
1. Export dữ liệu từ Render: pg_dump "RENDER_URL" -Fc -f render_backup.dump
2. Chạy script này: python migrate_to_supabase.py
"""

import psycopg2
import psycopg2.extras
import os
import sys

# ==================== CẤU HÌNH ====================
# THAY ĐỔI CÁC GIÁ TRỊ NÀY TRƯỚC KHI CHẠY!

# Kết nối cũ (Render) - nếu bạn có backup file thì không cần
RENDER_HOST = "your-render-host"
RENDER_DATABASE = "your-database-name"
RENDER_USER = "your-username"
RENDER_PASSWORD = "your-password"
RENDER_PORT = "5432"

# Kết nối mới (Supabase) - lấy từ Supabase Dashboard
SUPABASE_HOST = "db.xxxxx.supabase.co"  # Thay bằng host của bạn
SUPABASE_DATABASE = "postgres"
SUPABASE_USER = "postgres"
SUPABASE_PASSWORD = "your-supabase-password"  # Mật khẩu bạn đã tạo
SUPABASE_PORT = "5432"

# ==================== HÀM KẾT NỐI ====================

def connect_render():
    """Kết nối đến database Render cũ"""
    try:
        conn = psycopg2.connect(
            host=RENDER_HOST,
            database=RENDER_DATABASE,
            user=RENDER_USER,
            password=RENDER_PASSWORD,
            port=RENDER_PORT
        )
        print("✅ Kết nối Render thành công!")
        return conn
    except Exception as e:
        print(f"❌ Lỗi kết nối Render: {e}")
        return None

def connect_supabase():
    """Kết nối đến Supabase"""
    try:
        conn = psycopg2.connect(
            host=SUPABASE_HOST,
            database=SUPABASE_DATABASE,
            user=SUPABASE_USER,
            password=SUPABASE_PASSWORD,
            port=SUPABASE_PORT,
            sslmode='require'
        )
        print("✅ Kết nối Supabase thành công!")
        return conn
    except Exception as e:
        print(f"❌ Lỗi kết nối Supabase: {e}")
        print("\n🔧 Kiểm tra lại:")
        print("1. Host có đúng không? (db.xxxxx.supabase.co)")
        print("2. Mật khẩu có đúng không?")
        return None

# ==================== HÀM MIGRATE ====================

def migrate_products(old_conn, new_conn):
    """Migrate bảng products"""
    print("\n📦 Đang migrate bảng products...")
    cur_old = old_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur_new = new_conn.cursor()
    
    try:
        cur_old.execute("SELECT * FROM products ORDER BY id")
        products = cur_old.fetchall()
        
        for p in products:
            cur_new.execute("""
                INSERT INTO products (id, name, price, cost_price, stock, category, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (p['id'], p['name'], p['price'], p['cost_price'], 
                  p['stock'], p.get('category'), p['created_at']))
        
        new_conn.commit()
        print(f"   ✅ Đã migrate {len(products)} sản phẩm")
    except Exception as e:
        print(f"   ❌ Lỗi: {e}")
        new_conn.rollback()
    finally:
        cur_old.close()
        cur_new.close()

def migrate_customers(old_conn, new_conn):
    """Migrate bảng customers"""
    print("\n👥 Đang migrate bảng khách hàng...")
    cur_old = old_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur_new = new_conn.cursor()
    
    try:
        cur_old.execute("SELECT * FROM customers ORDER BY id")
        customers = cur_old.fetchall()
        
        for c in customers:
            cur_new.execute("""
                INSERT INTO customers (id, name, phone, email, address, total_spent, last_purchase, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (c['id'], c['name'], c.get('phone'), c.get('email'),
                  c.get('address'), c.get('total_spent', 0), 
                  c.get('last_purchase'), c['created_at']))
        
        new_conn.commit()
        print(f"   ✅ Đã migrate {len(customers)} khách hàng")
    except Exception as e:
        print(f"   ❌ Lỗi: {e}")
        new_conn.rollback()
    finally:
        cur_old.close()
        cur_new.close()

def migrate_orders(old_conn, new_conn):
    """Migrate bảng orders và order_items"""
    print("\n📄 Đang migrate đơn hàng...")
    cur_old = old_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur_new = new_conn.cursor()
    
    try:
        # Migrate orders
        cur_old.execute("SELECT * FROM orders ORDER BY id")
        orders = cur_old.fetchall()
        
        for o in orders:
            cur_new.execute("""
                INSERT INTO orders (id, order_number, customer_id, total_amount, 
                                   payment_method, status, created_by, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (o['id'], o['order_number'], o.get('customer_id'), o['total_amount'],
                  o.get('payment_method', 'cash'), o.get('status', 'completed'),
                  o.get('created_by'), o['created_at']))
        
        # Migrate order_items
        cur_old.execute("SELECT * FROM order_items ORDER BY id")
        items = cur_old.fetchall()
        
        for item in items:
            cur_new.execute("""
                INSERT INTO order_items (id, order_id, product_id, quantity, price)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (item['id'], item['order_id'], item['product_id'], 
                  item['quantity'], item['price']))
        
        new_conn.commit()
        print(f"   ✅ Đã migrate {len(orders)} đơn hàng và {len(items)} chi tiết")
    except Exception as e:
        print(f"   ❌ Lỗi: {e}")
        new_conn.rollback()
    finally:
        cur_old.close()
        cur_new.close()

def update_sequences(new_conn):
    """Cập nhật sequence ID cho các bảng"""
    print("\n🔄 Đang cập nhật sequences...")
    cur = new_conn.cursor()
    
    tables = ['products', 'customers', 'orders', 'order_items']
    
    for table in tables:
        try:
            cur.execute(f"""
                SELECT setval('{table}_id_seq', COALESCE((SELECT MAX(id) FROM {table}), 1))
            """)
            print(f"   ✅ Đã cập nhật sequence cho bảng {table}")
        except Exception as e:
            print(f"   ⚠️ Lỗi cập nhật {table}: {e}")
    
    new_conn.commit()
    cur.close()

# ==================== HÀM CHÍNH ====================

def main():
    print("=" * 50)
    print("   MIGRATE DỮ LIỆU SANG SUPABASE")
    print("=" * 50)
    
    # Kiểm tra cấu hình
    if SUPABASE_HOST == "db.xxxxx.supabase.co":
        print("\n❌ BẠN CẦN SỬA CẤU HÌNH TRƯỚC KHI CHẠY!")
        print("\nVui lòng thay đổi các giá trị ở đầu file:")
        print("  - SUPABASE_HOST (lấy từ Supabase Dashboard)")
        print("  - SUPABASE_PASSWORD (mật khẩu bạn đã tạo)")
        print("  - RENDER_HOST, RENDER_USER, RENDER_PASSWORD (nếu có)")
        return
    
    # Kết nối database
    print("\n📡 Đang kết nối database...")
    
    # Kết nối Supabase trước để tạo bảng
    supabase_conn = connect_supabase()
    if not supabase_conn:
        return
    
    # Tạo bảng trên Supabase nếu chưa có
    print("\n🏗️ Đang tạo cấu trúc bảng trên Supabase...")
    from database import Database
    db = Database()  # This will create tables
    db.connection = supabase_conn
    db.create_tables()
    
    # Kết nối Render (nếu có)
    render_conn = connect_render()
    if not render_conn:
        print("\n⚠️ Không kết nối được Render. Chỉ tạo bảng mới, không migrate dữ liệu.")
        supabase_conn.close()
        return
    
    # Migrate dữ liệu
    print("\n🚀 BẮT ĐẦU MIGRATE DỮ LIỆU...")
    
    migrate_products(render_conn, supabase_conn)
    migrate_customers(render_conn, supabase_conn)
    migrate_orders(render_conn, supabase_conn)
    update_sequences(supabase_conn)
    
    # Đóng kết nối
    render_conn.close()
    supabase_conn.close()
    
    print("\n" + "=" * 50)
    print("   ✅ MIGRATE HOÀN TẤT!")
    print("=" * 50)
    print("\n📝 Các bước tiếp theo:")
    print("1. Lấy connection string từ Supabase Dashboard")
    print("2. Cập nhật DATABASE_URL trên Render")
    print("3. Deploy lại ứng dụng trên Render")
    print("4. Kiểm tra ứng dụng hoạt động bình thường")

if __name__ == "__main__":
    main()
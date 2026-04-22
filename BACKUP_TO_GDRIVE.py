import os
import subprocess
from datetime import datetime

# Cấu hình database
DB_NAME = "pos_db"
DB_USER = "postgres"
DB_PASSWORD = "your_password"
DB_HOST = "localhost"
DB_PORT = "5432"

# Thư mục backup
BACKUP_DIR = "backups"
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

def backup_database():
    """Backup database ra file SQL"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"backup_{DB_NAME}_{timestamp}.sql")
    
    # Tạo backup
    cmd = f"PGPASSWORD={DB_PASSWORD} pg_dump -h {DB_HOST} -p {DB_PORT} -U {DB_USER} -d {DB_NAME} -F c -f {backup_file}"
    
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"✅ Backup thành công: {backup_file}")
        
        # Tạo file backup dạng readable
        readable_file = os.path.join(BACKUP_DIR, f"backup_{DB_NAME}_{timestamp}_readable.sql")
        cmd_readable = f"PGPASSWORD={DB_PASSWORD} pg_dump -h {DB_HOST} -p {DB_PORT} -U {DB_USER} -d {DB_NAME} > {readable_file}"
        subprocess.run(cmd_readable, shell=True, check=True)
        print(f"✅ Backup readable: {readable_file}")
        
        return backup_file
    except Exception as e:
        print(f"❌ Lỗi backup: {e}")
        return None

def list_backups():
    """Liệt kê các file backup"""
    backups = []
    for f in os.listdir(BACKUP_DIR):
        if f.endswith('.sql'):
            file_path = os.path.join(BACKUP_DIR, f)
            size = os.path.getsize(file_path)
            modified = datetime.fromtimestamp(os.path.getmtime(file_path))
            backups.append({
                'name': f,
                'size': size,
                'date': modified
            })
    return sorted(backups, key=lambda x: x['date'], reverse=True)

def restore_database(backup_file):
    """Khôi phục database từ file backup"""
    cmd = f"PGPASSWORD={DB_PASSWORD} pg_restore -h {DB_HOST} -p {DB_PORT} -U {DB_USER} -d {DB_NAME} -c {backup_file}"
    
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"✅ Khôi phục thành công từ: {backup_file}")
        return True
    except Exception as e:
        print(f"❌ Lỗi khôi phục: {e}")
        return False

def cleanup_old_backups(days=30):
    """Xóa các backup cũ hơn số ngày quy định"""
    cutoff = datetime.now().timestamp() - (days * 86400)
    
    for f in os.listdir(BACKUP_DIR):
        if f.endswith('.sql'):
            file_path = os.path.join(BACKUP_DIR, f)
            if os.path.getmtime(file_path) < cutoff:
                os.remove(file_path)
                print(f"🗑️ Đã xóa backup cũ: {f}")

if __name__ == "__main__":
    print("=== TOOL BACKUP DATABASE ===")
    print("1. Backup database")
    print("2. Xem danh sách backup")
    print("3. Cleanup backup cũ")
    
    choice = input("Chọn chức năng (1/2/3): ")
    
    if choice == '1':
        backup_database()
    elif choice == '2':
        backups = list_backups()
        print("\nDanh sách backup:")
        for b in backups:
            size_mb = b['size'] / (1024 * 1024)
            print(f"  {b['name']} - {size_mb:.2f} MB - {b['date']}")
    elif choice == '3':
        days = int(input("Xóa backup cũ hơn bao nhiêu ngày? (mặc định 30): ") or 30)
        cleanup_old_backups(days)
        print("Đã xóa backup cũ!")
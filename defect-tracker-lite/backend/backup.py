import os, shutil, datetime
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, 'app.db')
BACKUPS = os.path.join(BASE_DIR, 'backups')
os.makedirs(BACKUPS, exist_ok=True)

ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
dst = os.path.join(BACKUPS, f'app-{ts}.db')
shutil.copy2(DB, dst)
print(f'Backup created: {dst}')

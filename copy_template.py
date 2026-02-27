import shutil
import os

src = r"d:\Projects\Safina bot\expense-tracker-pro\СМЕТА ШАБЛОН.docx"
dst = r"d:\Projects\Safina bot\expense-tracker-pro\backend\app\services\docx\template.docx"

if os.path.exists(src):
    shutil.copy2(src, dst)
    print(f"Successfully copied {src} to {dst}")
    print(f"New size: {os.path.getsize(dst)}")
else:
    print(f"Source file not found: {src}")

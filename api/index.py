import os
import sys

# Thêm thư mục gốc dự án vào sys.path để Python nhận diện backend, module, graph trên Vercel
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.main import app

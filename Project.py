from flask import Flask, request, render_template_string
import os
import time

app = Flask(_name_)
DATA_FOLDER = "data"
RECORD_SIZE = 60
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)


class BTreeNode:
    def _init_(self, t, leaf=True):
        self.t = t
        self.leaf = leaf
        self.keys = []
        self.values = []
        self.children = []

class BTree:
    def _init_(self, t=3):
        self.root = BTreeNode(t, True)
        self.t = t

    def search(self, k, node=None):
        node = node or self.root
        i = 0
        while i < len(node.keys) and k > node.keys[i]:
            i += 1
        if i < len(node.keys) and k == node.keys[i]:
            return node.values[i]
        if node.leaf:
            return None
        return self.search(k, node.children[i])

    def split_child(self, parent, i):
        t = self.t
        full_child = parent.children[i]
        new_child = BTreeNode(t, full_child.leaf)

        mid_key = full_child.keys[t-1]
        mid_val = full_child.values[t-1]

        parent.keys.insert(i, mid_key)
        parent.values.insert(i, mid_val)
        parent.children.insert(i+1, new_child)

        new_child.keys = full_child.keys[t:]
        new_child.values = full_child.values[t:]
        if not full_child.leaf:
            new_child.children = full_child.children[t:]

        full_child.keys = full_child.keys[:t-1]
        full_child.values = full_child.values[:t-1]
        if not full_child.leaf:
            full_child.children = full_child.children[:t]

    def insert(self, k, v):
        root = self.root
        if len(root.keys) == (2 * self.t) - 1:
            new_root = BTreeNode(self.t, False)
            new_root.children.append(root)
            self.split_child(new_root, 0)
            self.root = new_root
            self._insert_non_full(new_root, k, v)
        else:
            self._insert_non_full(root, k, v)

    def _insert_non_full(self, node, k, v):
        i = len(node.keys) - 1
        if node.leaf:
            node.keys.append(None)
            node.values.append(None)
            while i >= 0 and k < node.keys[i]:
                node.keys[i+1] = node.keys[i]
                node.values[i+1] = node.values[i]
                i -= 1
            node.keys[i+1] = k
            node.values[i+1] = v
        else:
            while i >= 0 and k < node.keys[i]:
                i -= 1
            i += 1
            if len(node.children[i].keys) == (2 * self.t) - 1:
                self.split_child(node, i)
                if k > node.keys[i]:
                    i += 1
            self._insert_non_full(node.children[i], k, v)

btree = BTree(t=3)

students = []

def generate_id():
    return f"2024{len(students)+1:05d}"

def load_default():
    global students
    students = [
        "202400001|محمد أحمد|95", "202400002|فاطمة علي|88", "202400003|أحمد حسن|72",
        "202400004|نور محمد|91", "202400005|يوسف خالد|65", "202400006|زينب إبراهيم|89",
        "202400007|عمر صلاح|93", "202400008|لين محمد|87", "202400009|خالد عبدالله|78",
        "202400010|سارة محمود|94"
    ]

def rebuild_all():
    global btree
    btree = BTree(t=3)

    # Sequential
    with open(f"{DATA_FOLDER}/sequential.txt", "w", encoding="utf-8") as f:
        for s in students: f.write(s + "\n")

    # Indexed
    with open(f"{DATA_FOLDER}/indexed.dat", "wb") as f:
        for s in students: f.write(s.ljust(RECORD_SIZE, " ").encode()[:RECORD_SIZE])
    with open(f"{DATA_FOLDER}/index.txt", "w", encoding="utf-8") as f:
        for i, s in enumerate(students):
            f.write(f"{s.split('|')[0]}|{i*RECORD_SIZE}\n")

    # Direct Access
    with open(f"{DATA_FOLDER}/direct.dat", "wb") as f:
        f.write(b"\x00" * RECORD_SIZE * 100000)
    with open(f"{DATA_FOLDER}/direct.dat", "r+b") as f:
        for s in students:
            sid = int(s.split("|")[0])
            f.seek((sid % 100000) * RECORD_SIZE)
            f.write(s.ljust(RECORD_SIZE, " ").encode()[:RECORD_SIZE])

    # B-Tree
    for s in students:
        sid = s.split("|")[0]
        btree.insert(sid, s)

# دوال البحث
def search_sequential(target):
    start = time.time()
    with open(f"{DATA_FOLDER}/sequential.txt", "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if line.startswith(target + "|"):
                return time.time() - start, i+1, line.strip()
    return time.time() - start, -1, None

def search_indexed(target):
    start = time.time()
    pos = -1
    with open(f"{DATA_FOLDER}/index.txt", "r", encoding="utf-8") as f:
        for line in f:
            sid, p = line.strip().split("|")
            if sid == target:
                pos = int(p)
                break
    if pos == -1: return time.time() - start, -1, None
    with open(f"{DATA_FOLDER}/indexed.dat", "rb") as f:
        f.seek(pos)
        data = f.read(RECORD_SIZE).decode('utf-8', errors='ignore').strip()
    return time.time() - start, pos // RECORD_SIZE + 1, data

def search_direct(target):
    start = time.time()
    try:
        sid = int(target)
        slot = (sid % 100000) * RECORD_SIZE
        with open(f"{DATA_FOLDER}/direct.dat", "rb") as f:
            f.seek(slot)
            data = f.read(RECORD_SIZE).decode('utf-8', errors='ignore').strip()
            if data.startswith(target + "|"):
                return time.time() - start, slot // RECORD_SIZE + 1, data
    except: pass
    return time.time() - start, -1, None

def search_btree(target):
    start = time.time()
    result = btree.search(target)
    return time.time() - start, "O(log n)", result

# أول تشغيل
if not students:
    load_default()
    rebuild_all()

HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>محاكاة طرق تنظيم الملفات</title>
    <style>
        body {font-family: Tahoma, Arial; background: linear-gradient(135deg, #1e3c72, #2a5298); color:white; margin:0; padding:20px;}
        .container {max-width: 1100px; margin:auto; background:rgba(0,0,0,0.5); padding:40px; border-radius:20px; box-shadow:0 0 30px rgba(0,0,0,0.6);}
        h1 {text-align:center; color:#fff; font-size:32px; margin-bottom:30px; text-shadow:0 0 10px rgba(255,255,255,0.5);}
        .controls {text-align:center; margin:40px 0;}
        input, select, button {padding:14px 20px; margin:8px; font-size:18px; border-radius:10px; border:none;}
        button {background:#3498db; color:white; cursor:pointer; transition:0.3s; font-weight:bold;}
        button:hover {background:#2980b9; transform:scale(1.05);}
        .add {background:#27ae60;}
        .del {background:#e74c3c;}
        .result {background:rgba(255,255,255,0.15); padding:25px; border-radius:15px; margin:30px 0; border:2px solid #3498db;}
        table {width:100%; background:white; color:black; border-radius:15px; overflow:hidden; margin:40px 0; box-shadow:0 10px 25px rgba(0,0,0,0.4);}
        th {background:#2c3e50; color:white; padding:18px; font-size:20px;}
        td {padding:15px; text-align:center; font-size:16px;}
        .clickable:hover {background:#f8f9fa; cursor:pointer;}
        .found {color:#27ae60; font-weight:bold;}
        .notfound {color:#e74c3c; font-weight:bold;}
    </style>
</head>
<body>
<div class="container">
    <h1>محاكاة طرق تنظيم الملفات</h1>

    <div class="controls">
        <form method="POST">
            <input type="text" name="search_id" placeholder="رقم الطالب (مثل 202400001)" required>
            <select name="method">
                <option value="sequential">تسلسلي (Sequential)</option>
                <option value="indexed">مؤشر (Indexed)</option>
                <option value="direct">مباشر (Direct Access)</option>
                <option value="btree">B-Tree</option>
            </select>
            <button type="submit" name="action" value="search">بحث</button>
        </form>

        <form method="POST">
            <input type="text" name="new_name" placeholder="اسم الطالب الجديد" required>
            <input type="number" name="new_grade" placeholder="الدرجة" min="0" max="100" required>
            <button class="add" name="action" value="add">إضافة طالب</button>
        </form>

        <form method="POST">
            <input type="text" name="delete_id" placeholder="رقم الطالب لحذفه">
            <button class="del" name="action" value="delete">حذف طالب</button>
        </form>
    </div>

    {% if result %}
    <div class="result">
        <h2 style="color:#3498db;">نتيجة البحث بطريقة: {{ method_name }}</h2>
        {% if student_data %}
        <p><strong>بيانات الطالب:</strong> {{ student_data }}</p>
        <p><strong>الوقت:</strong> {{ "%.8f" % time_taken }} ثانية</p>
        <p><strong>عدد القراءات / التعقيد:</strong> <span class="found">{{ accesses }}</span></p>
        {% else %}
        <p class="notfound">الطالب غير موجود</p>
        {% endif %}
    </div>
    {% endif %}

    {% if message %}
    <h3 style="text-align:center; background:#27ae60; padding:15px; border-radius:12px; color:white; font-weight:bold;">{{ message }}</h3>
    {% endif %}

    <h2 style="text-align:center; margin-top:50px; color:#ecf0f1;">قائمة الطلاب الحاليين</h2>
    <table>
        <tr><th>رقم الطالب</th><th>الاسم</th><th>الدرجة</th></tr>
        {% for s in students %}
        <tr class="clickable" onclick="document.querySelector('[name=search_id]').value='{{ s.split('|')[0] }}'">
            <td><strong>{{ s.split('|')[0] }}</strong></td>
            <td>{{ s.split('|')[1] }}</td>
            <td>{{ s.split('|')[2] }}</td>
        </tr>
        {% endfor %}
    </table>
</div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    global students
    message = None
    result = None
    method_name = student_data = ""
    time_taken = accesses = 0

    if request.method == "POST":
        action = request.form.get("action")

        if action == "add":
            name = request.form["new_name"].strip()
            grade = request.form["new_grade"]
            new_id = generate_id()
            students.append(f"{new_id}|{name}|{grade}")
            rebuild_all()
            message = f"تم إضافة الطالب {new_id} - {name} بنجاح!"

        elif action == "delete":
            del_id = request.form["delete_id"].strip()
            old_len = len(students)
            students = [s for s in students if not s.startswith(del_id + "|")]
            if len(students) < old_len:
                rebuild_all()
                message = f"تم حذف الطالب {del_id} بنجاح!"
            else:
                message = "الطالب غير موجود!"

        elif action == "search":
            target = request.form["search_id"].strip()
            method = request.form["method"]

            if method == "sequential":
                method_name = "تسلسلي (Sequential)"
                time_taken, accesses, student_data = search_sequential(target)
            elif method == "indexed":
                method_name = "مؤشر (Indexed)"
                time_taken, accesses, student_data = search_indexed(target)
            elif method == "direct":
                method_name = "مباشر (Direct Access)"
                time_taken, accesses, student_data = search_direct(target)
            elif method == "btree":
                method_name = "B-Tree"
                time_taken, accesses, student_data = search_btree(target)

            result = True

    return render_template_string(HTML,
        students=students, message=message, result=result,
        method_name=method_name, student_data=student_data,
        time_taken=time_taken, accesses=accesses if accesses != -1 else "غير موجود"
    )

if _name_ == "_main_":
    print("محاكاة طرق تنظيم الملفات - جاهز للتشغيل")
    print("افتح المتصفح على: http://127.0.0.1:5000")
    app.run(debug=True)
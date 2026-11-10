import csv
from datetime import datetime
import io
import json
import os
from flask import (
    Flask,
    Response,
    flash,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)
import sqlite3
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "mohamed_it_financial_secret_key_v6"

# إعداد مجلد تخزين الصور الشخصية
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
  os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
  return (
      "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
  )


# إعداد قاعدة البيانات المحلية SQLite
def init_db():
  conn = sqlite3.connect("finance.db")
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            budget REAL DEFAULT 50000.0,
            created_at TEXT,
            avatar TEXT DEFAULT ''
        )
    """)
  for col, definition in [
      ("budget", "REAL DEFAULT 50000.0"),
      ("created_at", "TEXT"),
      ("avatar", "TEXT DEFAULT ''"),
  ]:
    try:
      cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
    except:
      pass

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL, -- 'expense' أو 'income'
            category TEXT,
            date TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
  conn.commit()
  conn.close()


init_db()

# قالب لوحة التحكم الرئيسية
TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>نظام تقليل الهدر المالي - الإصدار المتقدم 6.0</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap');
        body { font-family: 'Cairo', sans-serif; }
    </style>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen flex flex-col justify-between">
    {% if not session.get('user_id') %}
    <!-- صفحة تسجيل الدخول -->
    <div class="flex items-center justify-center min-h-screen px-4">
        <div class="bg-slate-800 border border-slate-700 p-8 rounded-2xl shadow-2xl w-full max-w-md">
            <div class="text-center mb-8">
                <div class="bg-cyan-500/10 text-cyan-400 w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 text-2xl font-bold border border-cyan-500/20">
                    <i class="fa-solid fa-wallet"></i>
                </div>
                <h1 class="text-2xl font-bold text-white">نظام تقليل الهدر المالي</h1>
                <p class="text-slate-400 text-sm mt-1">النسخة الاحترافية - تصميم: محمد الطيب</p>
            </div>

            {% with messages = get_flashed_messages() %}
              {% if messages %}
                <div class="bg-rose-500/10 border border-rose-500/30 text-rose-400 p-3 rounded-xl mb-4 text-sm text-center">
                  {{ messages[0] }}
                </div>
              {% endif %}
            {% endwith %}

            <form method="POST" action="/login" class="space-y-4">
                <div>
                    <label class="block text-sm text-slate-300 mb-1">اسم المستخدم</label>
                    <input type="text" name="username" required class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-cyan-500">
                </div>
                <div>
                    <label class="block text-sm text-slate-300 mb-1">كلمة المرور</label>
                    <input type="password" name="password" required class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-cyan-500">
                </div>
                <div class="flex gap-3 pt-2">
                    <button type="submit" class="flex-1 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold py-3 rounded-xl transition shadow-lg shadow-cyan-600/20">تسجيل الدخول</button>
                    <button type="submit" formaction="/register" class="flex-1 bg-slate-700 hover:bg-slate-600 text-white font-semibold py-3 rounded-xl transition">حساب جديد</button>
                </div>
            </form>
        </div>
    </div>
    {% else %}
    <!-- لوحة التحكم الرئيسية -->
    <div class="flex flex-1">
        <aside class="w-64 bg-slate-800 border-l border-slate-700 min-h-screen p-6 hidden md:block">
            <div class="flex items-center gap-3 mb-8">
                <div class="bg-cyan-500 text-slate-900 p-2.5 rounded-xl font-bold">
                    <i class="fa-solid fa-chart-line"></i>
                </div>
                <div>
                    <h2 class="font-bold text-white">الهدر المالي</h2>
                    <p class="text-xs text-cyan-400">الإصدار 6.0 PRO</p>
                </div>
            </div>
            <nav class="space-y-2">
                <a href="/" class="flex items-center gap-3 bg-cyan-500/10 text-cyan-400 px-4 py-3 rounded-xl font-medium border border-cyan-500/20">
                    <i class="fa-solid fa-house"></i> الرئيسية
                </a>
                <a href="/profile" class="flex items-center gap-3 text-slate-400 hover:text-cyan-400 hover:bg-slate-700/50 px-4 py-3 rounded-xl transition">
                    <i class="fa-solid fa-user-circle"></i> الملف الشخصي
                </a>
                <a href="/about" class="flex items-center gap-3 text-slate-400 hover:text-cyan-400 hover:bg-slate-700/50 px-4 py-3 rounded-xl transition">
                    <i class="fa-solid fa-id-card"></i> نبذة عن المصمم
                </a>
                <a href="/print_report" target="_blank" class="flex items-center gap-3 text-slate-400 hover:text-cyan-400 hover:bg-slate-700/50 px-4 py-3 rounded-xl transition">
                    <i class="fa-solid fa-print"></i> تقرير الطباعة / PDF
                </a>
                <a href="/export" class="flex items-center gap-3 text-slate-400 hover:text-cyan-400 hover:bg-slate-700/50 px-4 py-3 rounded-xl transition">
                    <i class="fa-solid fa-file-excel"></i> تصدير (CSV)
                </a>
                <a href="/logout" class="flex items-center gap-3 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 px-4 py-3 rounded-xl transition">
                    <i class="fa-solid fa-right-from-bracket"></i> تسجيل الخروج
                </a>
            </nav>
        </aside>

        <main class="flex-1 p-6 md:p-10">
            <header class="flex justify-between items-center mb-8 bg-slate-800/50 border border-slate-700/60 p-4 rounded-2xl backdrop-blur">
                <div class="flex items-center gap-3">
                    <a href="/profile" class="w-11 h-11 rounded-full overflow-hidden border-2 border-cyan-500/40 bg-slate-900 flex items-center justify-center font-bold text-lg hover:border-cyan-500 transition shadow">
                        {% if user_avatar %}
                            <img src="{{ url_for('static', filename='uploads/' + user_avatar) }}" alt="صورة البروفايل" class="w-full h-full object-cover">
                        {% else %}
                            <span class="text-cyan-400">{{ session.username[0].upper() }}</span>
                        {% endif %}
                    </a>
                    <div>
                        <h1 class="text-xl font-bold text-white">أهلاً بك، <span class="text-cyan-400">{{ session.username }}</span></h1>
                        <p class="text-xs text-slate-400">لوحة التحكم المتقدمة - تتبع الهدر وإدارة الميزانية</p>
                    </div>
                </div>
                <div class="flex gap-2">
                    <a href="/about" class="bg-slate-700 hover:bg-slate-600 text-white px-3 py-2 rounded-xl text-sm font-medium transition flex items-center gap-2">
                        <i class="fa-solid fa-id-card"></i> نبذة عني
                    </a>
                    <a href="/print_report" target="_blank" class="bg-cyan-600 hover:bg-cyan-500 text-white px-3 py-2 rounded-xl text-sm font-medium transition flex items-center gap-2">
                        <i class="fa-solid fa-print"></i> PDF
                    </a>
                    <a href="/logout" class="md:hidden bg-rose-500/10 text-rose-400 px-3 py-1.5 rounded-lg text-sm border border-rose-500/20">خروج</a>
                </div>
            </header>

            <!-- ملخص الإحصائيات -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div class="bg-slate-800 border border-slate-700 p-6 rounded-2xl shadow-lg">
                    <p class="text-slate-400 text-sm mb-1">إجمالي الإيرادات</p>
                    <h3 class="text-2xl font-bold text-emerald-400">{{ total_income }} ج.س</h3>
                </div>
                <div class="bg-slate-800 border border-slate-700 p-6 rounded-2xl shadow-lg">
                    <p class="text-slate-400 text-sm mb-1">إجمالي المصروفات (الهدر)</p>
                    <h3 class="text-2xl font-bold text-rose-400">{{ total_expense }} ج.س</h3>
                </div>
                <div class="bg-slate-800 border border-slate-700 p-6 rounded-2xl shadow-lg">
                    <p class="text-slate-400 text-sm mb-1">صافي الرصيد / المتبقي</p>
                    <h3 class="text-2xl font-bold text-cyan-400">{{ total_income - total_expense }} ج.س</h3>
                </div>
            </div>

            <!-- إعداد الميزانية الشهرية وشريط التقدم -->
            <div class="bg-slate-800 border border-slate-700 p-6 rounded-2xl shadow-lg mb-8">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-lg font-bold text-white flex items-center gap-2">
                        <i class="fa-solid fa-bullseye text-cyan-400"></i> إدارة الميزانية الشهرية المستهدفة
                    </h2>
                    <form method="POST" action="/update_budget" class="flex gap-2">
                        <input type="number" name="budget" value="{{ user_budget }}" required class="bg-slate-900 border border-slate-700 rounded-xl px-3 py-1 text-sm text-white w-32 focus:outline-none focus:border-cyan-500">
                        <button type="submit" class="bg-cyan-600 hover:bg-cyan-500 text-white px-3 py-1 rounded-xl text-xs font-semibold transition">تحديث</button>
                    </form>
                </div>
                {% set b_progress = (total_expense / user_budget * 100) if user_budget > 0 else 0 %}
                <div class="space-y-2">
                    <div class="flex justify-between text-xs text-slate-300">
                        <span>المصروفات الحالية: {{ total_expense }} ج.س</span>
                        <span>الحد الأقصى: {{ user_budget }} ج.س ({{ "%.1f"|format(b_progress) }}%)</span>
                    </div>
                    <div class="w-full bg-slate-900 rounded-full h-3 border border-slate-700 overflow-hidden">
                        <div class="h-full {% if b_progress > 90 %}bg-rose-500{% elif b_progress > 60 %}bg-amber-500{% else %}bg-emerald-500{% endif %} transition-all duration-500" style="width: {{ b_progress if b_progress <= 100 else 100 }}%;"></div>
                    </div>
                </div>
            </div>

            <!-- قسم النموذج والرسوم البيانية -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
                <div class="bg-slate-800 border border-slate-700 p-6 rounded-2xl shadow-lg lg:col-span-1">
                    <h2 class="text-lg font-bold text-white mb-4"><i class="fa-solid fa-plus-circle text-cyan-400 ml-2"></i>إضافة معاملة مالية</h2>
                    <form method="POST" action="/add" class="space-y-4">
                        <div>
                            <label class="block text-xs text-slate-400 mb-1">الوصف أو العنوان</label>
                            <input type="text" name="title" required placeholder="مثال: فاتورة كهرباء..." class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500">
                        </div>
                        <div>
                            <label class="block text-xs text-slate-400 mb-1">المبلغ (ج.س)</label>
                            <input type="number" step="0.01" name="amount" required placeholder="0.00" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500">
                        </div>
                        <div>
                            <label class="block text-xs text-slate-400 mb-1">نوع المعاملة</label>
                            <select name="type" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500">
                                <option value="expense">مصروف (هدر محتمل)</option>
                                <option value="income">إيراد / دخل</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-xs text-slate-400 mb-1">التصنيف</label>
                            <select name="category" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500">
                                <option value="فواتير والتزامات">فواتير والتزامات</option>
                                <option value="طعام ومؤونة">طعام ومؤونة</option>
                                <option value="ترفيه وكماليات">ترفيه وكماليات</option>
                                <option value="مواصلات ونقل">مواصلات ونقل</option>
                                <option value="أخرى">أخرى</option>
                            </select>
                        </div>
                        <button type="submit" class="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-semibold py-2.5 rounded-xl transition text-sm">حفظ المعاملة</button>
                    </form>
                </div>

                <div class="bg-slate-800 border border-slate-700 p-6 rounded-2xl shadow-lg lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <h3 class="text-sm font-bold text-white mb-2 text-center"><i class="fa-solid fa-chart-pie text-cyan-400 ml-1"></i>التحليل المالي العام</h3>
                        <div class="w-full h-56 flex items-center justify-center">
                            <canvas id="financeChart"></canvas>
                        </div>
                    </div>
                    <div>
                        <h3 class="text-sm font-bold text-white mb-2 text-center"><i class="fa-solid fa-chart-bar text-cyan-400 ml-1"></i>المصروفات حسب الفئات</h3>
                        <div class="w-full h-56 flex items-center justify-center">
                            <canvas id="categoryChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <!-- سجل المعاملات -->
            <div class="bg-slate-800 border border-slate-700 rounded-2xl shadow-lg overflow-hidden">
                <div class="p-6 border-b border-slate-700 flex flex-col md:flex-row justify-between items-center gap-4">
                    <h2 class="text-lg font-bold text-white">سجل المعاملات المالية</h2>
                    <form method="GET" action="/" class="flex flex-wrap gap-2 w-full md:w-auto">
                        <input type="text" name="search" value="{{ search_query }}" placeholder="بحث بالوصف..." class="bg-slate-900 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500">
                        <select name="filter_cat" class="bg-slate-900 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500">
                            <option value="">كل التصنيفات</option>
                            <option value="فواتير والتزامات" {% if filter_cat == 'فواتير والتزامات' %}selected{% endif %}>فواتير والتزامات</option>
                            <option value="طعام ومؤونة" {% if filter_cat == 'طعام ومؤونة' %}selected{% endif %}>طعام ومؤونة</option>
                            <option value="ترفيه وكماليات" {% if filter_cat == 'ترفيه وكماليات' %}selected{% endif %}>ترفيه وكماليات</option>
                            <option value="مواصلات ونقل" {% if filter_cat == 'مواصلات ونقل' %}selected{% endif %}>مواصلات ونقل</option>
                            <option value="أخرى" {% if filter_cat == 'أخرى' %}selected{% endif %}>أخرى</option>
                        </select>
                        <button type="submit" class="bg-cyan-600 hover:bg-cyan-500 text-white px-3 py-1.5 rounded-xl text-xs transition">بحث وتصفية</button>
                        {% if search_query or filter_cat %}
                        <a href="/" class="bg-slate-700 hover:bg-slate-600 text-white px-3 py-1.5 rounded-xl text-xs transition flex items-center">إلغاء</a>
                        {% endif %}
                    </form>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-right text-sm">
                        <thead class="bg-slate-900/50 text-slate-400 border-b border-slate-700">
                            <tr>
                                <th class="p-4">الوصف</th>
                                <th class="p-4">المبلغ</th>
                                <th class="p-4">النوع</th>
                                <th class="p-4">التصنيف</th>
                                <th class="p-4">التاريخ</th>
                                <th class="p-4 text-center">إجراءات</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-700/50">
                            {% for t in transactions %}
                            <tr class="hover:bg-slate-700/20 transition">
                                <td class="p-4 font-medium text-white">{{ t[2] }}</td>
                                <td class="p-4 font-bold {% if t[4] == 'income' %}text-emerald-400{% else %}text-rose-400{% endif %}">
                                    {% if t[4] == 'income' %}+{% else %}-{% endif %}{{ t[3] }} ج.س
                                </td>
                                <td class="p-4">
                                    <span class="px-2.5 py-1 rounded-full text-xs {% if t[4] == 'income' %}bg-emerald-500/10 text-emerald-400 border border-emerald-500/20{% else %}bg-rose-500/10 text-rose-400 border border-rose-500/20{% endif %}">
                                        {% if t[4] == 'income' %}إيراد{% else %}مصروف{% endif %}
                                    </span>
                                </td>
                                <td class="p-4 text-slate-300">{{ t[5] or 'عام' }}</td>
                                <td class="p-4 text-slate-400 text-xs">{{ t[6] }}</td>
                                <td class="p-4 text-center">
                                    <a href="/delete/{{ t[0] }}" class="text-rose-400 hover:text-rose-300 bg-rose-500/10 border border-rose-500/20 px-3 py-1 rounded-lg text-xs transition">حذف</a>
                                </td>
                            </tr>
                            {% else %}
                            <tr>
                                <td colspan="6" class="p-8 text-center text-slate-500">لا توجد معاملات مطابقة للبحث أو مسجلة حتى الآن.</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </main>
    </div>

    <!-- تذييل بصمة المصمم الثابت -->
    <footer class="bg-slate-950 border-t border-slate-800 py-6 text-center text-slate-400 text-xs">
        <div class="max-w-4xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-4">
            <div class="flex items-center gap-3">
                <img src="{{ url_for('static', filename='my_photo.jpg') }}" alt="محمد الطيب" class="w-10 h-10 rounded-full object-cover border border-cyan-500/40">
                <div class="text-right">
                    <p class="text-white font-bold">تصميم وتطوير: محمد الطيب حمد محمد علي</p>
                    <p class="text-[11px] text-cyan-400">طالب تقانة المعلومات (الدفعة الخامسة - كلية الفجر)</p>
                </div>
            </div>
            <div>
                <p>&copy; 2026 نظام تقليل الهدر المالي (v6.0 PRO) - جميع الحقوق محفوظة.</p>
            </div>
        </div>
    </footer>

    <script>
        const ctx1 = document.getElementById('financeChart').getContext('2d');
        new Chart(ctx1, {
            type: 'doughnut',
            data: {
                labels: ['الإيرادات', 'المصروفات'],
                datasets: [{
                    data: [{{ total_income }}, {{ total_expense }}],
                    backgroundColor: ['#10b981', '#f43f5e'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom', labels: { color: '#cbd5e1', font: { family: 'Cairo' } } } }
            }
        });

        const ctx2 = document.getElementById('categoryChart').getContext('2d');
        new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: {{ cat_labels | safe }},
                datasets: [{
                    label: 'المصروفات حسب الفئة',
                    data: {{ cat_totals | safe }},
                    backgroundColor: ['#38bdf8', '#818cf8', '#c084fc', '#f472b6', '#fb7185'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: '#cbd5e1', font: { family: 'Cairo', size: 10 } }, grid: { display: false } },
                    y: { ticks: { color: '#cbd5e1', font: { family: 'Cairo' } }, grid: { color: '#334155' } }
                }
            }
        });
    </script>
    {% endif %}
</body>
</html>
"""

# قالب صفحة الملف الشخصي
PROFILE_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>الملف الشخصي الاحترافي - النظام المالي</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap');
        body { font-family: 'Cairo', sans-serif; }
    </style>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen flex items-center justify-center px-4 py-12">
    <div class="bg-slate-800 border border-slate-700 p-8 rounded-2xl shadow-2xl w-full max-w-lg">
        <div class="text-center pb-6 border-b border-slate-700 mb-6">
            <div class="relative w-28 h-28 mx-auto mb-4">
                <div class="w-full h-full rounded-full overflow-hidden border-4 border-slate-900 bg-slate-900 shadow-xl flex items-center justify-center">
                    {% if user_data[5] %}
                        <img src="{{ url_for('static', filename='uploads/' + user_data[5]) }}" alt="صورة المستخدم" class="w-full h-full object-cover">
                    {% else %}
                        <div class="w-full h-full bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-white text-3xl font-bold">
                            {{ user_data[1][0].upper() }}
                        </div>
                    {% endif %}
                </div>
            </div>
            <h1 class="text-2xl font-bold text-white">{{ user_data[1] }}</h1>
            <p class="text-xs text-cyan-400 mt-1"><i class="fa-solid fa-shield-halved ml-1"></i> حساب مستخدم موثق</p>
        </div>
        <form method="POST" action="/profile" enctype="multipart/form-data" class="space-y-4">
            <div>
                <label class="block text-sm text-slate-300 mb-1">اسم المستخدم</label>
                <input type="text" name="username" value="{{ user_data[1] }}" required class="w-full bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-cyan-500 text-sm">
            </div>
            <div>
                <label class="block text-sm text-slate-300 mb-1">تغيير الصورة الشخصية (PNG, JPG)</label>
                <input type="file" name="avatar" accept=".png, .jpg, .jpeg" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-400">
            </div>
            <div class="flex gap-3 pt-2">
                <button type="submit" class="flex-1 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold py-3 rounded-xl transition text-sm">حفظ التعديلات</button>
                <a href="/" class="flex-1 bg-slate-700 hover:bg-slate-600 text-white font-semibold py-3 rounded-xl transition text-center text-sm flex items-center justify-center">العودة للرئيسية</a>
            </div>
        </form>
    </div>
</body>
</html>
"""

# قالب صفحة "نبذة عني" (About Me) الجديدة كلياً
ABOUT_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>نبذة عن المصمم والمطور - محمد الطيب</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap');
        body { font-family: 'Cairo', sans-serif; }
    </style>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen flex flex-col justify-between">
    <div class="max-w-4xl mx-auto px-4 py-12 flex-1 w-full">
        <div class="flex justify-between items-center mb-8">
            <a href="/" class="bg-slate-800 border border-slate-700 hover:bg-slate-700 text-cyan-400 px-4 py-2 rounded-xl text-sm transition flex items-center gap-2">
                <i class="fa-solid fa-arrow-right"></i> العودة للوحة التحكم
            </a>
            <h1 class="text-xl font-bold text-white">الملف التعريفي للمطور</h1>
        </div>

        <div class="bg-slate-800 border border-slate-700 rounded-3xl p-8 md:p-12 shadow-2xl relative overflow-hidden">
            <div class="absolute -top-24 -left-24 w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"></div>
            
            <div class="flex flex-col md:flex-row items-center gap-8 text-center md:text-right">
                <!-- صورتك الشخصية -->
                <div class="relative">
                    <div class="w-40 h-40 rounded-2xl overflow-hidden border-4 border-cyan-500/40 shadow-2xl bg-slate-900">
                        <img src="{{ url_for('static', filename='my_photo.jpg') }}" alt="محمد الطيب حمد" class="w-full h-full object-cover">
                    </div>
                    <div class="absolute -bottom-2 -right-2 bg-cyan-600 text-white p-2 rounded-xl shadow-lg border border-slate-800" title="مطور برمجيات">
                        <i class="fa-solid fa-code text-sm"></i>
                    </div>
                </div>

                <!-- تفاصيلك والنبذة -->
                <div class="flex-1 space-y-3">
                    <span class="bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs px-3 py-1 rounded-full font-semibold inline-block">مطور وباسكت كامل (Full-Stack Developer)</span>
                    <h2 class="text-3xl font-bold text-white">محمد الطيب حمد محمد علي</h2>
                    <p class="text-cyan-400 font-medium text-sm">طالب تقانة المعلومات (الدفعة الخامسة) - كلية الفجر</p>
                    <p class="text-slate-300 text-sm leading-relaxed pt-2">
                        مطور برمجيات شغوف بتطوير وتصميم الأنظمة الويب المتقدمة والتطبيقات الذكية. قمت بتصميم وهندسة هذا النظام المتكامل (<span class="text-cyan-400 font-semibold">نظام تقليل الهدر المالي v6.0 PRO</span>) باستخدام أحدث التقنيات البرمجية لتقديم تجربة مستخدم سلسة، آمنة، وعالية الأداء في إدارة الميزانيات وتتبع النفقات بدقة ذكية.
                    </p>
                </div>
            </div>

            <!-- المهارات والتقنيات -->
            <div class="mt-10 pt-8 border-t border-slate-700/60 grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="bg-slate-900/60 border border-slate-700/60 p-5 rounded-2xl">
                    <div class="text-cyan-400 text-xl mb-2"><i class="fa-solid fa-laptop-code"></i></div>
                    <h3 class="font-bold text-white mb-1">تطوير الويب</h3>
                    <p class="text-xs text-slate-400">بناء وتطوير تطبيقات الويب المتكاملة باستخدام Flask, Python, HTML, Tailwind CSS.</p>
                </div>
                <div class="bg-slate-900/60 border border-slate-700/60 p-5 rounded-2xl">
                    <div class="text-cyan-400 text-xl mb-2"><i class="fa-solid fa-database"></i></div>
                    <h3 class="font-bold text-white mb-1">قواعد البيانات</h3>
                    <p class="text-xs text-slate-400">إدارة وتصميم هياكل قواعد البيانات بـ SQLite وإنشاء الاستعلامات المتقدمة.</p>
                </div>
                <div class="bg-slate-900/60 border border-slate-700/60 p-5 rounded-2xl">
                    <div class="text-cyan-400 text-xl mb-2"><i class="fa-solid fa-cloud-arrow-up"></i></div>
                    <h3 class="font-bold text-white mb-1">الاستضافة والنشر</h3>
                    <p class="text-xs text-slate-400">إدارة مستودعات GitHub ونشر المشاريع سحابياً على منصات مثل Render بجدارة.</p>
                </div>
            </div>
        </div>
    </div>

    <!-- تذييل الصفحة -->
    <footer class="bg-slate-950 border-t border-slate-800 py-6 text-center text-slate-400 text-xs">
        <p>&copy; 2026 نظام تقليل الهدر المالي (v6.0 PRO) - تم التطوير بكل فخر بواسطة محمد الطيب.</p>
    </footer>
</body>
</html>
"""

# قالب تقرير الطباعة الرسمي
PRINT_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>التقرير المالي الرسمي - {{ username }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap');
        body { font-family: 'Cairo', sans-serif; background: #fff; color: #000; }
        @media print { .no-print { display: none; } }
    </style>
</head>
<body class="p-8 max-w-4xl mx-auto">
    <div class="flex justify-between items-center border-b pb-4 mb-6">
        <div>
            <h1 class="text-2xl font-bold">تقرير التدفق المالي وتقليل الهدر</h1>
            <p class="text-sm text-gray-600">المستخدم: {{ username }} | تصميم: محمد الطيب | التاريخ: {{ now }}</p>
        </div>
        <button onclick="window.print()" class="no-print bg-blue-600 text-white px-4 py-2 rounded-xl text-sm font-bold shadow">طباعة التقرير / حفظ PDF</button>
    </div>

    <div class="grid grid-cols-3 gap-4 mb-6 text-center">
        <div class="border p-4 rounded-xl bg-gray-50">
            <p class="text-sm text-gray-500">إجمالي الإيرادات</p>
            <h3 class="text-xl font-bold text-emerald-600">{{ total_income }} ج.س</h3>
        </div>
        <div class="border p-4 rounded-xl bg-gray-50">
            <p class="text-sm text-gray-500">إجمالي المصروفات (الهدر)</p>
            <h3 class="text-xl font-bold text-rose-600">{{ total_expense }} ج.س</h3>
        </div>
        <div class="border p-4 rounded-xl bg-gray-50">
            <p class="text-sm text-gray-500">صافي المتبقي</p>
            <h3 class="text-xl font-bold text-blue-600">{{ total_income - total_expense }} ج.س</h3>
        </div>
    </div>

    <h2 class="text-lg font-bold mb-3">سجل المعاملات التفصيلي</h2>
    <table class="w-full text-right border-collapse border border-gray-300 text-sm">
        <thead>
            <tr class="bg-gray-100 border-b">
                <th class="p-2 border">الوصف</th>
                <th class="p-2 border">المبلغ</th>
                <th class="p-2 border">النوع</th>
                <th class="p-2 border">التصنيف</th>
                <th class="p-2 border">التاريخ</th>
            </tr>
        </thead>
        <tbody>
            {% for t in transactions %}
            <tr class="border-b">
                <td class="p-2 border">{{ t[2] }}</td>
                <td class="p-2 border font-bold">{{ t[3] }} ج.س</td>
                <td class="p-2 border">{% if t[4] == 'income' %}إيراد{% else %}مصروف{% endif %}</td>
                <td class="p-2 border">{{ t[5] or 'عام' }}</td>
                <td class="p-2 border text-xs">{{ t[6] }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""


@app.route("/")
def index():
  if "user_id" not in session:
    return render_template_string(TEMPLATE)

  search_query = request.args.get("search", "")
  filter_cat = request.args.get("filter_cat", "")

  conn = sqlite3.connect("finance.db")
  cursor = conn.cursor()

  query = "SELECT * FROM transactions WHERE user_id = ?"
  params = [session["user_id"]]

  if search_query:
    query += " AND title LIKE ?"
    params.append(f"%{search_query}%")
  if filter_cat:
    query += " AND category = ?"
    params.append(filter_cat)

  query += " ORDER BY id DESC"
  cursor.execute(query, params)
  transactions = cursor.fetchall()

  cursor.execute(
      "SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type ="
      ' "income"',
      (session["user_id"],),
  )
  total_income = cursor.fetchone()[0] or 0.0

  cursor.execute(
      "SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type ="
      ' "expense"',
      (session["user_id"],),
  )
  total_expense = cursor.fetchone()[0] or 0.0

  cursor.execute(
      "SELECT budget, avatar FROM users WHERE id = ?", (session["user_id"],)
  )
  user_res = cursor.fetchone()
  user_budget = (
      user_res[0] if user_res and user_res[0] is not None else 50000.0
  )
  user_avatar = user_res[1] if user_res else ""

  cursor.execute(
      "SELECT category, SUM(amount) FROM transactions WHERE user_id = ? AND type"
      ' = "expense" GROUP BY category',
      (session["user_id"],),
  )
  cat_results = cursor.fetchall()
  conn.close()

  cat_labels = [row[0] or "أخرى" for row in cat_results]
  cat_totals = [row[1] for row in cat_results]

  if not cat_labels:
    cat_labels = ["لا توجد مصاريف"]
    cat_totals = [0]

  return render_template_string(
      TEMPLATE,
      transactions=transactions,
      total_income=total_income,
      total_expense=total_expense,
      user_budget=user_budget,
      user_avatar=user_avatar,
      search_query=search_query,
      filter_cat=filter_cat,
      cat_labels=json.dumps(cat_labels, ensure_ascii=False),
      cat_totals=json.dumps(cat_totals),
  )


@app.route("/register", methods=["POST"])
def register():
  username = request.form["username"]
  password = request.form["password"]
  reg_date = datetime.now().strftime("%Y-%m-%d")
  try:
    conn = sqlite3.connect("finance.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, password, budget, created_at, avatar)"
        " VALUES (?, ?, ?, ?, ?)",
        (username, password, 50000.0, reg_date, ""),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))
  except:
    return "اسم المستخدم مستخدم مسبقاً. <a href='/'>الرجوع</a>"


@app.route("/login", methods=["POST"])
def login():
  username = request.form["username"]
  password = request.form["password"]
  conn = sqlite3.connect("finance.db")
  cursor = conn.cursor()
  cursor.execute(
      "SELECT id, username FROM users WHERE username = ? AND password = ?",
      (username, password),
  )
  user = cursor.fetchone()
  conn.close()
  if user:
    session["user_id"] = user[0]
    session["username"] = user[1]
    return redirect(url_for("index"))
  else:
    return "بيانات الدخول غير صحيحة. <a href='/'>الرجوع</a>"


@app.route("/logout")
def logout():
  session.clear()
  return redirect(url_for("index"))


@app.route("/profile", methods=["GET", "POST"])
def profile():
  if "user_id" not in session:
    return redirect(url_for("index"))

  conn = sqlite3.connect("finance.db")
  cursor = conn.cursor()

  if request.method == "POST":
    new_username = request.form["username"]
    new_pass = request.form["password"]

    file = request.files.get("avatar")
    if file and allowed_file(file.filename):
      filename = secure_filename(f"user_{session['user_id']}_{file.filename}")
      file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
      cursor.execute(
          "UPDATE users SET avatar = ? WHERE id = ?",
          (filename, session["user_id"]),
      )

    if new_pass:
      cursor.execute(
          "UPDATE users SET username = ?, password = ? WHERE id = ?",
          (new_username, new_pass, session["user_id"]),
      )
    else:
      cursor.execute(
          "UPDATE users SET username = ? WHERE id = ?",
          (new_username, session["user_id"]),
      )

    conn.commit()
    session["username"] = new_username

  cursor.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],))
  user_data = cursor.fetchone()

  cursor.execute(
      "SELECT COUNT(*) FROM transactions WHERE user_id = ?",
      (session["user_id"],),
  )
  tx_count = cursor.fetchone()[0] or 0
  conn.close()

  return render_template_string(
      PROFILE_TEMPLATE, user_data=user_data, tx_count=tx_count
  )


# مسار صفحة "نبذة عني" الجديدة
@app.route("/about")
def about():
  if "user_id" not in session:
    return redirect(url_for("index"))
  return render_template_string(ABOUT_TEMPLATE)


@app.route("/add", methods=["POST"])
def add():
  if "user_id" not in session:
    return redirect(url_for("index"))
  title = request.form["title"]
  amount = float(request.form["amount"])
  t_type = request.form["type"]
  category = request.form["category"]
  date = datetime.now().strftime("%Y-%m-%d %H:%M")

  conn = sqlite3.connect("finance.db")
  cursor = conn.cursor()
  cursor.execute(
      "INSERT INTO transactions (user_id, title, amount, type, category, date)"
      " VALUES (?, ?, ?, ?, ?, ?)",
      (session["user_id"], title, amount, t_type, category, date),
  )
  conn.commit()
  conn.close()
  return redirect(url_for("index"))


@app.route("/delete/<int:t_id>")
def delete_transaction(t_id):
  if "user_id" not in session:
    return redirect(url_for("index"))
  conn = sqlite3.connect("finance.db")
  cursor = conn.cursor()
  cursor.execute(
      "DELETE FROM transactions WHERE id = ? AND user_id = ?",
      (t_id, session["user_id"]),
  )
  conn.commit()
  conn.close()
  return redirect(url_for("index"))


@app.route("/update_budget", methods=["POST"])
def update_budget():
  if "user_id" not in session:
    return redirect(url_for("index"))
  new_budget = float(request.form["budget"])
  conn = sqlite3.connect("finance.db")
  cursor = conn.cursor()
  cursor.execute(
      "UPDATE users SET budget = ? WHERE id = ?",
      (new_budget, session["user_id"]),
  )
  conn.commit()
  conn.close()
  return redirect(url_for("index"))


@app.route("/print_report")
def print_report():
  if "user_id" not in session:
    return redirect(url_for("index"))
  conn = sqlite3.connect("finance.db")
  cursor = conn.cursor()
  cursor.execute(
      "SELECT * FROM transactions WHERE user_id = ? ORDER BY id DESC",
      (session["user_id"],),
  )
  transactions = cursor.fetchall()
  cursor.execute(
      "SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type ="
      ' "income"',
      (session["user_id"],),
  )
  total_income = cursor.fetchone()[0] or 0.0
  cursor.execute(
      "SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type ="
      ' "expense"',
      (session["user_id"],),
  )
  total_expense = cursor.fetchone()[0] or 0.0
  conn.close()
  now = datetime.now().strftime("%Y-%m-%d %H:%M")
  return render_template_string(
      PRINT_TEMPLATE,
      transactions=transactions,
      total_income=total_income,
      total_expense=total_expense,
      username=session["username"],
      now=now,
  )


@app.route("/export")
def export_report():
  if "user_id" not in session:
    return redirect(url_for("index"))
  conn = sqlite3.connect("finance.db")
  cursor = conn.cursor()
  cursor.execute(
      "SELECT title, amount, type, category, date FROM transactions WHERE"
      " user_id = ? ORDER BY id DESC",
      (session["user_id"],),
  )
  transactions = cursor.fetchall()
  conn.close()
  output = io.StringIO()
  writer = csv.writer(output)
  writer.writerow(["العنوان", "المبلغ", "النوع", "التصنيف", "التاريخ"])
  for t in transactions:
    writer.writerow(t)
  output.seek(0)
  return Response(
      "\ufeff" + output.getvalue(),
      mimetype="text/csv",
      headers={
          "Content-Disposition": (
              f"attachment;filename=financial_report_{session['username']}.csv"
          )
      },
  )


if __name__ == "__main__":
  app.run(debug=True, port=5000)

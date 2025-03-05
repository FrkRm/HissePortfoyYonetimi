import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import sqlite3
import yfinance as yf
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import datetime
import json

# Özel Dialog Sınıfları (Güncellenmiş)
class SellStockDialog(ctk.CTkToplevel):
    def __init__(self, parent, ticker):
        super().__init__(parent)
        self.title(f"{ticker} için Satış İşlemi")
        self.minsize(320, 250)  # Minimum boyut ayarlandı
        self.resizable(True, True)  # Kullanıcının pencereyi yeniden boyutlandırmasına izin veriyoruz
        self.result = None

        self.label_qty = ctk.CTkLabel(self, text="Satılacak Adet:")
        self.label_qty.pack(pady=(10, 0))
        self.entry_qty = ctk.CTkEntry(self, width=250)
        self.entry_qty.pack(pady=(0, 10))

        self.label_price = ctk.CTkLabel(self, text="Satış Fiyatı:")
        self.label_price.pack(pady=(10, 0))
        self.entry_price = ctk.CTkEntry(self, width=250)
        self.entry_price.pack(pady=(0, 10))

        self.label_date = ctk.CTkLabel(self, text="Satış Tarihi (YYYY-MM-DD):")
        self.label_date.pack(pady=(10, 0))
        self.entry_date = ctk.CTkEntry(self, width=250)
        self.entry_date.pack(pady=(0, 10))

        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(pady=10, fill=tk.X)
        self.ok_button = ctk.CTkButton(self.button_frame, text="Onayla", command=self.on_ok, width=100)
        self.ok_button.pack(side=tk.LEFT, padx=5)
        self.cancel_button = ctk.CTkButton(self.button_frame, text="İptal", command=self.destroy, width=100)
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        self.grab_set()
        self.wait_window(self)
    
    def on_ok(self):
        try:
            qty = int(self.entry_qty.get())
            price = float(self.entry_price.get())
            date_str = self.entry_date.get()
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            messagebox.showerror("Hata", "Lütfen tüm alanlara geçerli değerler girin.")
            return
        self.result = (qty, price, date_str)
        self.destroy()


class EditStockDialog(ctk.CTkToplevel):
    def __init__(self, parent, ticker):
        super().__init__(parent)
        self.title(f"{ticker} için Hisse Düzenle")
        self.minsize(320, 250)
        self.resizable(True, True)
        self.result = None

        self.label_qty = ctk.CTkLabel(self, text="Eklenecek Adet:")
        self.label_qty.pack(pady=(10, 0))
        self.entry_qty = ctk.CTkEntry(self, width=250)
        self.entry_qty.pack(pady=(0, 10))

        self.label_price = ctk.CTkLabel(self, text="Yeni Alış Fiyatı:")
        self.label_price.pack(pady=(10, 0))
        self.entry_price = ctk.CTkEntry(self, width=250)
        self.entry_price.pack(pady=(0, 10))

        self.label_date = ctk.CTkLabel(self, text="Yeni Alış Tarihi (YYYY-MM-DD):")
        self.label_date.pack(pady=(10, 0))
        self.entry_date = ctk.CTkEntry(self, width=250)
        self.entry_date.pack(pady=(0, 10))

        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(pady=10, fill=tk.X)
        self.ok_button = ctk.CTkButton(self.button_frame, text="Onayla", command=self.on_ok, width=100)
        self.ok_button.pack(side=tk.LEFT, padx=5)
        self.cancel_button = ctk.CTkButton(self.button_frame, text="İptal", command=self.destroy, width=100)
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        self.grab_set()
        self.wait_window(self)
    
    def on_ok(self):
        try:
            qty = int(self.entry_qty.get())
            price = float(self.entry_price.get())
            date_str = self.entry_date.get()
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            messagebox.showerror("Hata", "Lütfen tüm alanlara geçerli değerler girin.")
            return
        self.result = (qty, price, date_str)
        self.destroy()



# --- VERİTABANI YÖNETİMİ ---
class DatabaseManager:
    DB_NAME = "portfolio.db"
    
    @staticmethod
    def create_database():
        conn = sqlite3.connect(DatabaseManager.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                purchase_price REAL NOT NULL,
                purchase_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                sale_price REAL NOT NULL DEFAULT 0,
                sale_date TEXT NOT NULL DEFAULT ''
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
    
    @staticmethod
    def update_database_schema():
        conn = sqlite3.connect(DatabaseManager.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(portfolio)")
        columns = [info[1] for info in cursor.fetchall()]
        if "purchase_price" not in columns:
            cursor.execute("ALTER TABLE portfolio ADD COLUMN purchase_price REAL NOT NULL DEFAULT 0")
        if "purchase_date" not in columns:
            cursor.execute("ALTER TABLE portfolio ADD COLUMN purchase_date TEXT NOT NULL DEFAULT ''")
        if "status" not in columns:
            cursor.execute("ALTER TABLE portfolio ADD COLUMN status TEXT NOT NULL DEFAULT 'active'")
        if "sale_price" not in columns:
            cursor.execute("ALTER TABLE portfolio ADD COLUMN sale_price REAL NOT NULL DEFAULT 0")
        if "sale_date" not in columns:
            cursor.execute("ALTER TABLE portfolio ADD COLUMN sale_date TEXT NOT NULL DEFAULT ''")
        conn.commit()
        conn.close()
    
    @staticmethod
    def add_stock(ticker, quantity, purchase_price, purchase_date):
        conn = sqlite3.connect(DatabaseManager.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO portfolio (ticker, quantity, purchase_price, purchase_date, status, sale_price, sale_date)
            VALUES (?, ?, ?, ?, 'active', 0, '')
        """, (ticker, quantity, purchase_price, purchase_date))
        conn.commit()
        conn.close()
    
    @staticmethod
    def update_stock(ticker, quantity, purchase_price, purchase_date):
        conn = sqlite3.connect(DatabaseManager.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE portfolio 
            SET quantity = ?, purchase_price = ?, purchase_date = ?
            WHERE ticker = ? AND status = 'active'
        """, (quantity, purchase_price, purchase_date, ticker))
        conn.commit()
        conn.close()
    
    @staticmethod
    def sell_stock_in_db(ticker, sale_price, sale_date):
        conn = sqlite3.connect(DatabaseManager.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE portfolio 
            SET status = 'sold', sale_price = ?, sale_date = ?
            WHERE ticker = ? AND status = 'active'
        """, (sale_price, sale_date, ticker))
        conn.commit()
        conn.close()
    
    @staticmethod
    def remove_stock(ticker):
        conn = sqlite3.connect(DatabaseManager.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM portfolio WHERE ticker = ?", (ticker,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_portfolio():
        conn = sqlite3.connect(DatabaseManager.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ticker, quantity, purchase_price, purchase_date, status, sale_price, sale_date
            FROM portfolio
        """)
        portfolio = cursor.fetchall()
        conn.close()
        return portfolio
    
    @staticmethod
    def add_to_watchlist(ticker):
        conn = sqlite3.connect(DatabaseManager.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO watchlist (ticker) VALUES (?)", (ticker,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def remove_from_watchlist(ticker):
        conn = sqlite3.connect(DatabaseManager.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_watchlist():
        conn = sqlite3.connect(DatabaseManager.DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT ticker FROM watchlist")
        watchlist = cursor.fetchall()
        conn.close()
        return [item[0] for item in watchlist]

# --- YAHOO FINANCE İŞLEVLERİ ---
def get_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        if not data.empty:
            return data["Close"].iloc[-1]
        return None
    except Exception as e:
        print(f"Hata: {e}")
        return None

def get_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        return stock.info
    except Exception as e:
        print(f"Hata: {e}")
        return None

def plot_stock_performance(ticker, frame):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1mo")
        if data.empty:
            messagebox.showerror("Hata", "Grafik için yeterli veri bulunamadı.")
            return
        dates = data.index.strftime('%Y-%m-%d').tolist()
        prices = data["Close"].tolist()
        
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(dates, prices, label=f"{ticker} Fiyat")
        ax.set_xlabel("Tarih")
        ax.set_ylabel("Fiyat")
        ax.set_title(f"{ticker} Hisse Performansı")
        ax.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        for widget in frame.winfo_children():
            widget.destroy()
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(canvas, frame)
        toolbar.update()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    except Exception as e:
        messagebox.showerror("Hata", f"Grafik oluşturulamadı: {e}")

# --- PORTFÖY YÖNETİMİ ---
class Portfolio:
    def __init__(self):
        self.transactions = []  # Her işlem (aktif veya satılmış) burada saklanır.
        self.load_portfolio()
    
    def load_portfolio(self):
        self.transactions = []
        for row in DatabaseManager.get_portfolio():
            (ticker, quantity, purchase_price, purchase_date, status, sale_price, sale_date) = row
            self.transactions.append({
                "ticker": ticker,
                "quantity": quantity,
                "purchase_price": purchase_price,
                "purchase_date": purchase_date,
                "status": status,
                "sale_price": sale_price,
                "sale_date": sale_date
            })
    
    def get_active_holdings(self):
        active = {}
        for trans in self.transactions:
            if trans["status"] == "active":
                active[trans["ticker"]] = trans
        return active
    
    def get_sold_stocks(self):
        return [trans for trans in self.transactions if trans["status"] == "sold"]
    
    def add_stock(self, ticker, quantity, purchase_price, purchase_date):
        active = self.get_active_holdings()
        if ticker in active:
            current = active[ticker]
            new_qty = current["quantity"] + quantity
            new_avg = (current["quantity"] * current["purchase_price"] + quantity * purchase_price) / new_qty
            DatabaseManager.update_stock(ticker, new_qty, new_avg, purchase_date)
        else:
            DatabaseManager.add_stock(ticker, quantity, purchase_price, purchase_date)
        self.load_portfolio()
    
    def update_stock(self, ticker, quantity, purchase_price, purchase_date):
        active = self.get_active_holdings()
        if ticker in active:
            DatabaseManager.update_stock(ticker, quantity, purchase_price, purchase_date)
            self.load_portfolio()
    
    def sell_stock(self, ticker, sell_qty, sale_price, sale_date):
        active = self.get_active_holdings()
        if ticker not in active:
            messagebox.showwarning("Uyarı", "Bu hisse aktif değil veya bulunmuyor.")
            return
        current = active[ticker]
        current_qty = current["quantity"]
        if sell_qty > current_qty:
            messagebox.showerror("Hata", "Satmak istediğiniz miktar mevcut adetten fazla.")
            return
        if sell_qty == current_qty:
            DatabaseManager.sell_stock_in_db(ticker, sale_price, sale_date)
        else:
            new_qty = current_qty - sell_qty
            conn = sqlite3.connect(DatabaseManager.DB_NAME)
            cursor = conn.cursor()
            cursor.execute("UPDATE portfolio SET quantity = ? WHERE ticker = ? AND status = 'active'", (new_qty, ticker))
            conn.commit()
            conn.close()
            conn = sqlite3.connect(DatabaseManager.DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO portfolio (ticker, quantity, purchase_price, purchase_date, status, sale_price, sale_date)
                VALUES (?, ?, ?, ?, 'sold', ?, ?)
            """, (ticker, sell_qty, current["purchase_price"], current["purchase_date"], sale_price, sale_date))
            conn.commit()
            conn.close()
        self.load_portfolio()
    
    def get_portfolio_value(self):
        active = self.get_active_holdings()
        total_value = 0
        total_profit_loss = 0
        for ticker, data in active.items():
            price = get_stock_price(ticker)
            if price is not None:
                total_value += float(price) * data["quantity"]
                total_profit_loss += (float(price) - data["purchase_price"]) * data["quantity"]
        return total_value, total_profit_loss
    
    def get_sold_total_profit(self):
        sold = self.get_sold_stocks()
        total = 0
        for trans in sold:
            total += (trans["sale_price"] - trans["purchase_price"]) * trans["quantity"]
        return total

# --- MODERN ARAYÜZ (BAĞLAM MENÜSÜ EKLENMİŞ) ---
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Portföy Yönetimi")
        self.geometry("1200x800")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.portfolio = Portfolio()
        self.watchlist = DatabaseManager.get_watchlist()
        
        # Ana çerçeve
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.title_label = ctk.CTkLabel(self.main_frame, text="Portföy Yönetimi", font=("Arial", 28, "bold"))
        self.title_label.pack(pady=(10,20))
        
        self.input_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.input_frame.pack(fill=tk.X, padx=20, pady=(0,20))
        
        self.ticker_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Hisse Kodu (Ör: AAPL)", width=150)
        self.ticker_entry.grid(row=0, column=0, padx=8, pady=8)
        
        self.quantity_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Miktar", width=80)
        self.quantity_entry.grid(row=0, column=1, padx=8, pady=8)
        
        self.price_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Alış Fiyatı", width=80)
        self.price_entry.grid(row=0, column=2, padx=8, pady=8)
        
        self.date_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Alış Tarihi (YYYY-MM-DD)", width=150)
        self.date_entry.grid(row=0, column=3, padx=8, pady=8)
        
        self.button_frame = ctk.CTkFrame(self.input_frame, corner_radius=10)
        self.button_frame.grid(row=0, column=4, padx=8, pady=8)
        
        self.add_button = ctk.CTkButton(self.button_frame, text="Portföye Ekle", command=self.add_stock, width=90)
        self.add_button.grid(row=0, column=0, padx=4, pady=4)
        
        self.update_button = ctk.CTkButton(self.button_frame, text="Güncelle", command=self.update_stock, width=90)
        self.update_button.grid(row=0, column=1, padx=4, pady=4)
        
        self.search_button = ctk.CTkButton(self.button_frame, text="Ara", command=self.search_stock, width=90)
        self.search_button.grid(row=0, column=2, padx=4, pady=4)
        
        self.add_watchlist_button = ctk.CTkButton(self.button_frame, text="Takip Listesine Ekle", command=self.add_to_watchlist, width=110)
        self.add_watchlist_button.grid(row=0, column=3, padx=4, pady=4)
        
        self.detail_button = ctk.CTkButton(self.button_frame, text="Detaylı Bilgi", command=self.show_stock_details, width=90)
        self.detail_button.grid(row=0, column=4, padx=4, pady=4)
        
        # Sekmeler: Portföy, Takip Listesi, Grafik, Satılanlar
        self.tabview = ctk.CTkTabview(self.main_frame, width=1100, height=500)
        self.tabview.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        self.tabview.add("Portföy")
        self.tabview.add("Takip Listesi")
        self.tabview.add("Grafik")
        self.tabview.add("Satılanlar")
        
        # Portföy Tab
        self.portfolio_tab = self.tabview.tab("Portföy")
        self.portfolio_table_frame = ctk.CTkFrame(self.portfolio_tab, corner_radius=10)
        self.portfolio_table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.portfolio_columns = ("Hisse", "Miktar", "Alış Fiyatı", "Alış Tarihi", "Durum", "Fiyat", "Toplam Değer", "Kar/Zarar")
        self.portfolio_tree = ttk.Treeview(self.portfolio_table_frame, columns=self.portfolio_columns, show="headings", height=15)
        for col in self.portfolio_columns:
            self.portfolio_tree.heading(col, text=col)
            self.portfolio_tree.column(col, anchor=tk.CENTER, width=100)
        self.portfolio_tree.pack(fill=tk.BOTH, expand=True)
        self.portfolio_tree.tag_configure("sold", foreground="gray")
        self.portfolio_tree.bind("<<TreeviewSelect>>", self.on_portfolio_select)
        self.portfolio_tree.bind("<Button-3>", self.show_context_menu)
        
        self.value_label = ctk.CTkLabel(self.portfolio_tab, text="Portföy Değeri: 0 TL", font=("Arial", 18))
        self.value_label.pack(pady=5)
        self.profit_loss_label = ctk.CTkLabel(self.portfolio_tab, text="Net Kar/Zarar: 0 TL", font=("Arial", 18))
        self.profit_loss_label.pack(pady=(0,10))
        
        # Takip Listesi Tab
        self.watchlist_tab = self.tabview.tab("Takip Listesi")
        self.watchlist_table_frame = ctk.CTkFrame(self.watchlist_tab, corner_radius=10)
        self.watchlist_table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.watchlist_columns = ("Hisse", "Fiyat")
        self.watchlist_tree = ttk.Treeview(self.watchlist_table_frame, columns=self.watchlist_columns, show="headings", height=10)
        for col in self.watchlist_columns:
            self.watchlist_tree.heading(col, text=col)
            self.watchlist_tree.column(col, anchor=tk.CENTER, width=150)
        self.watchlist_tree.pack(fill=tk.BOTH, expand=True)
        self.watchlist_tree.bind("<<TreeviewSelect>>", self.on_watchlist_select)
        
        self.watchlist_info_label = ctk.CTkLabel(self.watchlist_tab, text="Hisse Bilgileri: ", font=("Arial", 16))
        self.watchlist_info_label.pack(pady=5)
        
        self.remove_watchlist_button = ctk.CTkButton(self.watchlist_tab, text="Takip Listesinden Çıkar", command=self.remove_from_watchlist, width=110)
        self.remove_watchlist_button.pack(pady=5)
        
        # Grafik Tab
        self.graph_tab = self.tabview.tab("Grafik")
        self.graph_control_frame = ctk.CTkFrame(self.graph_tab, corner_radius=10)
        self.graph_control_frame.pack(fill=tk.X, padx=10, pady=5)
        self.open_graph_button = ctk.CTkButton(self.graph_control_frame, text="Grafik Aç", command=self.open_graph, width=90)
        self.open_graph_button.pack(padx=10, pady=5)
        self.graph_frame = ctk.CTkFrame(self.graph_tab, corner_radius=10)
        self.graph_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Satılanlar Tab
        self.sold_tab = self.tabview.tab("Satılanlar")
        self.sold_table_frame = ctk.CTkFrame(self.sold_tab, corner_radius=10)
        self.sold_table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.sold_columns = ("Hisse", "Miktar", "Alış Fiyatı", "Alış Tarihi", "Satış Fiyatı", "Satış Tarihi", "Kar/Zarar")
        self.sold_tree = ttk.Treeview(self.sold_table_frame, columns=self.sold_columns, show="headings", height=10)
        for col in self.sold_columns:
            self.sold_tree.heading(col, text=col)
            self.sold_tree.column(col, anchor=tk.CENTER, width=120)
        self.sold_tree.pack(fill=tk.BOTH, expand=True)
        
        self.sold_profit_label = ctk.CTkLabel(self.sold_tab, text="Satışlardan Elde Edilen Toplam Kar/Zarar: 0 TL", font=("Arial", 18))
        self.sold_profit_label.pack(pady=5)
        
        # Bağlam Menüsü (Sağ tık)
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Hisseyi Sat", command=self.sell_stock_context)
        self.context_menu.add_command(label="Hisseyi Düzenle", command=self.edit_stock_context)
        self.context_menu.add_command(label="Hisseyi Sil", command=self.delete_stock_context)
        
        self.refresh_portfolio()
        self.refresh_watchlist()
        self.refresh_sold_stocks()
    
    def show_context_menu(self, event):
        row_id = self.portfolio_tree.identify_row(event.y)
        if row_id:
            self.portfolio_tree.selection_set(row_id)
            self.context_menu.post(event.x_root, event.y_root)
    
    def sell_stock_context(self):
        selected = self.portfolio_tree.selection()
        if selected:
            item = self.portfolio_tree.item(selected[0], "values")
            ticker = item[0]
            dialog = SellStockDialog(self, ticker)
            if dialog.result:
                sell_qty, sale_price, sale_date = dialog.result
                self.portfolio.sell_stock(ticker, sell_qty, sale_price, sale_date)
                profit = (sale_price - float(item[2])) * sell_qty
                messagebox.showinfo("Bilgi", f"{ticker} için satış tamamlandı. Kar/Zarar: {profit:.2f} TL")
                self.refresh_portfolio()
                self.refresh_sold_stocks()
    
    def edit_stock_context(self):
        selected = self.portfolio_tree.selection()
        if selected:
            item = self.portfolio_tree.item(selected[0], "values")
            ticker = item[0]
            active = self.portfolio.get_active_holdings()
            if ticker not in active:
                messagebox.showwarning("Uyarı", "Bu hisse aktif değil.")
                return
            dialog = EditStockDialog(self, ticker)
            if dialog.result:
                add_qty, new_price, new_date = dialog.result
                current = active[ticker]
                new_total_qty = current["quantity"] + add_qty
                new_avg = (current["quantity"] * current["purchase_price"] + add_qty * new_price) / new_total_qty
                DatabaseManager.update_stock(ticker, new_total_qty, new_avg, new_date)
                self.portfolio.load_portfolio()
                messagebox.showinfo("Bilgi", f"{ticker} için ekleme yapıldı.\nYeni Miktar: {new_total_qty}\nYeni Ortalama Fiyat: {new_avg:.2f}")
                self.refresh_portfolio()
    
    def delete_stock_context(self):
        selected = self.portfolio_tree.selection()
        if selected:
            item = self.portfolio_tree.item(selected[0], "values")
            ticker = item[0]
            confirm = messagebox.askyesno("Onay", f"{ticker} hissesini portföyden silmek istediğinize emin misiniz?")
            if confirm:
                DatabaseManager.remove_stock(ticker)
                self.portfolio.load_portfolio()
                self.refresh_portfolio()
                messagebox.showinfo("Bilgi", f"{ticker} portföyden silindi.")
    
    def on_portfolio_select(self, event):
        selected = self.portfolio_tree.selection()
        if selected:
            item = self.portfolio_tree.item(selected[0], "values")
            self.ticker_entry.delete(0, tk.END)
            self.ticker_entry.insert(0, item[0])
            self.quantity_entry.delete(0, tk.END)
            self.quantity_entry.insert(0, item[1])
            self.price_entry.delete(0, tk.END)
            self.price_entry.insert(0, item[2])
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, item[3])
    
    def on_watchlist_select(self, event):
        selected = self.watchlist_tree.selection()
        if selected:
            item = self.watchlist_tree.item(selected[0], "values")
            ticker = item[0]
            price = get_stock_price(ticker)
            if price is not None:
                self.watchlist_info_label.configure(text=f"Hisse Bilgileri: {ticker} - Fiyat: {price:.2f} TL")
            else:
                self.watchlist_info_label.configure(text=f"Hisse Bilgileri: {ticker} - Fiyat: N/A")
    
    def add_stock(self):
        try:
            ticker = self.ticker_entry.get().upper().strip()
            quantity = int(self.quantity_entry.get())
            purchase_price = float(self.price_entry.get())
            purchase_date = self.date_entry.get().strip()
            datetime.datetime.strptime(purchase_date, "%Y-%m-%d")
            self.portfolio.add_stock(ticker, quantity, purchase_price, purchase_date)
            messagebox.showinfo("Bilgi", f"{ticker} portföye eklendi.")
            self.refresh_portfolio()
        except Exception as e:
            messagebox.showerror("Hata", "Lütfen tüm alanlara geçerli değerler girin.")
    
    def update_stock(self):
        try:
            ticker = self.ticker_entry.get().upper().strip()
            quantity = int(self.quantity_entry.get())
            purchase_price = float(self.price_entry.get())
            purchase_date = self.date_entry.get().strip()
            datetime.datetime.strptime(purchase_date, "%Y-%m-%d")
            self.portfolio.update_stock(ticker, quantity, purchase_price, purchase_date)
            messagebox.showinfo("Bilgi", f"{ticker} portföyde güncellendi.")
            self.refresh_portfolio()
        except Exception as e:
            messagebox.showerror("Hata", "Lütfen tüm alanlara geçerli değerler girin.")
    
    def search_stock(self):
        ticker = self.ticker_entry.get().upper().strip()
        if ticker:
            info = get_stock_info(ticker)
            if info and "regularMarketPrice" in info:
                self.price_entry.delete(0, tk.END)
                self.price_entry.insert(0, f"{info['regularMarketPrice']:.2f}")
                messagebox.showinfo("Bilgi", f"{ticker} hissesi bulundu.")
            else:
                messagebox.showerror("Hata", "Hisse bilgisi bulunamadı.")
    
    def show_stock_details(self):
        ticker = self.ticker_entry.get().upper().strip()
        if ticker:
            info = get_stock_info(ticker)
            if info:
                detail_window = ctk.CTkToplevel(self)
                detail_window.title(f"{ticker} - Detaylı Bilgi")
                detail_window.geometry("600x400")
                text = tk.Text(detail_window, wrap="word")
                text.insert(tk.END, json.dumps(info, indent=4))
                text.config(state="disabled")
                text.pack(fill=tk.BOTH, expand=True)
            else:
                messagebox.showerror("Hata", "Hisse detayları alınamadı.")
        else:
            messagebox.showwarning("Uyarı", "Lütfen detaylarını görmek için bir hisse kodu girin.")
    
    def open_graph(self):
        ticker = self.ticker_entry.get().upper().strip()
        if ticker:
            for widget in self.graph_frame.winfo_children():
                widget.destroy()
            plot_stock_performance(ticker, self.graph_frame)
        else:
            messagebox.showwarning("Uyarı", "Lütfen grafik için bir hisse kodu seçin.")
    
    def refresh_portfolio(self):
        self.portfolio.load_portfolio()
        active = self.portfolio.get_active_holdings()
        for i in self.portfolio_tree.get_children():
            self.portfolio_tree.delete(i)
        for ticker, data in active.items():
            price = get_stock_price(ticker)
            if price is not None:
                current_price = float(price)
                total = current_price * data["quantity"]
                profit_loss = (current_price - data["purchase_price"]) * data["quantity"]
            else:
                current_price = 0
                total = 0
                profit_loss = 0
            self.portfolio_tree.insert("", "end", values=(
                ticker,
                data["quantity"],
                f"{data['purchase_price']:.2f}",
                data["purchase_date"],
                "Aktif",
                f"{current_price:.2f}" if current_price != 0 else "N/A",
                f"{total:.2f}" if total != 0 else "N/A",
                f"{profit_loss:.2f}" if profit_loss != 0 else "N/A"
            ))
        total_value, total_profit_loss = self.portfolio.get_portfolio_value()
        self.value_label.configure(text=f"Portföy Değeri: {total_value:.2f} TL")
        self.profit_loss_label.configure(text=f"Net Kar/Zarar: {total_profit_loss:.2f} TL")
    
    def refresh_watchlist(self):
        for i in self.watchlist_tree.get_children():
            self.watchlist_tree.delete(i)
        for ticker in self.watchlist:
            price = get_stock_price(ticker)
            price_text = f"{price:.2f} TL" if price is not None else "N/A"
            self.watchlist_tree.insert("", "end", values=(ticker, price_text))
    
    def refresh_sold_stocks(self):
        for i in self.sold_tree.get_children():
            self.sold_tree.delete(i)
        sold = self.portfolio.get_sold_stocks()
        sold_total_profit = 0
        for trans in sold:
            profit_loss = (trans["sale_price"] - trans["purchase_price"]) * trans["quantity"]
            sold_total_profit += profit_loss
            self.sold_tree.insert("", "end", values=(
                trans["ticker"],
                trans["quantity"],
                f"{trans['purchase_price']:.2f}",
                trans["purchase_date"],
                f"{trans['sale_price']:.2f}",
                trans["sale_date"],
                f"{profit_loss:.2f}"
            ))
        self.sold_profit_label.configure(text=f"Satışlardan Elde Edilen Toplam Kar/Zarar: {sold_total_profit:.2f} TL")
    
    def add_to_watchlist(self):
        ticker = self.ticker_entry.get().upper().strip()
        if ticker:
            if ticker not in self.watchlist:
                self.watchlist.append(ticker)
                DatabaseManager.add_to_watchlist(ticker)
                self.refresh_watchlist()
                messagebox.showinfo("Bilgi", f"{ticker} takip listesine eklendi.")
            else:
                messagebox.showwarning("Uyarı", f"{ticker} zaten takip listesinde.")
    
    def remove_from_watchlist(self):
        selected = self.watchlist_tree.selection()
        if selected:
            ticker = self.watchlist_tree.item(selected[0], "values")[0]
            if ticker in self.watchlist:
                self.watchlist.remove(ticker)
                DatabaseManager.remove_from_watchlist(ticker)
                self.refresh_watchlist()
                self.watchlist_info_label.configure(text="Hisse Bilgileri: ")
                messagebox.showinfo("Bilgi", f"{ticker} takip listesinden çıkarıldı.")
        else:
            messagebox.showwarning("Uyarı", "Lütfen listeden bir hisse seçin.")

if __name__ == "__main__":
    DatabaseManager.create_database()
    DatabaseManager.update_database_schema()
    app = App()
    app.mainloop()

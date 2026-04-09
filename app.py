import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import pandas as pd
from datetime import datetime
import cv2
from PIL import Image
import os

# =========================
# CONFIGURAÇÕES INICIAIS
# =========================
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

DB_NAME = "portaria_novacap.db"

# =========================
# BANCO DE DADOS
# =========================
def conectar():
    return sqlite3.connect(DB_NAME)

def criar_tabela():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS colaboradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricula TEXT UNIQUE,
            nome TEXT NOT NULL,
            setor TEXT,
            cargo TEXT,
            telefone TEXT,
            status TEXT DEFAULT 'ATIVO',
            data_cadastro TEXT
        )
    """)
    conn.commit()
    conn.close()

def inserir_colaborador(matricula, nome, setor, cargo, telefone):
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO colaboradores (matricula, nome, setor, cargo, telefone, status, data_cadastro)
            VALUES (?, ?, ?, ?, ?, 'ATIVO', ?)
        """, (
            matricula.strip(),
            nome.strip().upper(),
            setor.strip().upper(),
            cargo.strip().upper(),
            telefone.strip(),
            datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def listar_colaboradores():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, matricula, nome, setor, cargo, telefone, status, data_cadastro
        FROM colaboradores
        ORDER BY id DESC
    """)
    dados = cursor.fetchall()
    conn.close()
    return dados

def buscar_colaboradores(termo):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, matricula, nome, setor, cargo, telefone, status, data_cadastro
        FROM colaboradores
        WHERE matricula LIKE ? OR nome LIKE ?
        ORDER BY id DESC
    """, (f"%{termo}%", f"%{termo}%"))
    dados = cursor.fetchall()
    conn.close()
    return dados

def atualizar_status(id_colab, novo_status):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE colaboradores SET status = ? WHERE id = ?", (novo_status, id_colab))
    conn.commit()
    conn.close()

def contar_status():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM colaboradores")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM colaboradores WHERE status = 'ATIVO'")
    ativos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM colaboradores WHERE status = 'BLOQUEADO'")
    bloqueados = cursor.fetchone()[0]

    conn.close()
    return total, ativos, bloqueados

# =========================
# APLICAÇÃO PRINCIPAL
# =========================
class SistemaPortaria(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SISTEMA PORTARIA - NOVACAP 2026")
        self.geometry("1400x820")
        self.minsize(1200, 700)
        self.configure(fg_color="#0b4f93")

        criar_tabela()
        self.configurar_estilo_tabela()
        self.criar_layout()
        self.carregar_tabela()
        self.atualizar_dashboard()

    # =========================
    # ESTILO TABELA
    # =========================
    def configurar_estilo_tabela(self):
        style = ttk.Style()
        style.theme_use("default")

        style.configure(
            "Treeview",
            background="white",
            foreground="black",
            rowheight=28,
            fieldbackground="white",
            borderwidth=0,
            font=("Arial", 10)
        )

        style.configure(
            "Treeview.Heading",
            background="#d9e6f2",
            foreground="black",
            font=("Arial", 10, "bold"),
            relief="flat"
        )

        style.map(
            "Treeview",
            background=[("selected", "#cfe2f3")],
            foreground=[("selected", "black")]
        )

    # =========================
    # LAYOUT
    # =========================
    def criar_layout(self):
        # TOPO
        self.topo = ctk.CTkFrame(self, fg_color="#0b4f93", corner_radius=0, height=95)
        self.topo.pack(fill="x", side="top")
        self.topo.pack_propagate(False)

        try:
            img_n = ctk.CTkImage(light_image=Image.open("logo_novacap.png"), size=(170, 50))
            self.lbl_logo_n = ctk.CTkLabel(self.topo, image=img_n, text="")
            self.lbl_logo_n.pack(side="left", padx=20, pady=15)
        except:
            pass

        ctk.CTkLabel(
            self.topo,
            text="CONTROLE DE ACESSO INTEGRADO",
            font=("Arial", 30, "bold"),
            text_color="white"
        ).pack(side="left", expand=True)

        try:
            img_g = ctk.CTkImage(light_image=Image.open("logo_gdf.png"), size=(100, 50))
            self.lbl_logo_g = ctk.CTkLabel(self.topo, image=img_g, text="")
            self.lbl_logo_g.pack(side="right", padx=20, pady=15)
        except:
            pass

        # PAINEL PRINCIPAL
        self.painel = ctk.CTkFrame(self, fg_color="#f2f2f2", corner_radius=18)
        self.painel.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # BOTÕES SUPERIORES
        btn_frame = ctk.CTkFrame(self.painel, fg_color="transparent")
        btn_frame.pack(pady=(12, 8))

        ctk.CTkButton(
            btn_frame, text="+ NOVO CADASTRO", fg_color="#0c8a43",
            hover_color="#086c34", command=self.abrir_janela_cadastro, width=165, height=34
        ).grid(row=0, column=0, padx=6)

        ctk.CTkButton(
            btn_frame, text="🔒 ALTERAR STATUS", fg_color="#1f5fa8",
            hover_color="#184d87", command=self.alternar_status, width=165, height=34
        ).grid(row=0, column=1, padx=6)

        ctk.CTkButton(
            btn_frame, text="📊 EXPORTAR EXCEL", fg_color="#2f8f2f",
            hover_color="#246f24", command=self.gerar_excel, width=165, height=34
        ).grid(row=0, column=2, padx=6)

        ctk.CTkButton(
            btn_frame, text="🎥 CÂMERA", fg_color="#8b2fb2",
            hover_color="#6e258d", command=self.abrir_camera, width=165, height=34
        ).grid(row=0, column=3, padx=6)

        # DASHBOARD
        dash_frame = ctk.CTkFrame(self.painel, fg_color="transparent")
        dash_frame.pack(pady=(6, 8))

        self.card_total = self.criar_card(dash_frame, "TOTAL", "0", "#1f5fa8", 0)
        self.card_ativos = self.criar_card(dash_frame, "ATIVOS", "0", "#0c8a43", 1)
        self.card_bloqueados = self.criar_card(dash_frame, "BLOQUEADOS", "0", "#b52d2d", 2)

        # BUSCA
        busca_f = ctk.CTkFrame(self.painel, fg_color="transparent")
        busca_f.pack(pady=(5, 8))

        self.entry_busca = ctk.CTkEntry(
            busca_f, width=360, height=34,
            placeholder_text="Buscar por nome ou matrícula..."
        )
        self.entry_busca.grid(row=0, column=0, padx=6)

        ctk.CTkButton(
            busca_f, text="BUSCAR", command=self.buscar,
            width=100, height=34, fg_color="#2d8ae0", hover_color="#1f6fb8"
        ).grid(row=0, column=1, padx=5)

        ctk.CTkButton(
            busca_f, text="LIMPAR", fg_color="#6c757d", hover_color="#5a6268",
            command=self.limpar_busca, width=90, height=34
        ).grid(row=0, column=2, padx=5)

        # TABELA
        tabela_container = ctk.CTkFrame(self.painel, fg_color="white", corner_radius=10)
        tabela_container.pack(fill="both", expand=True, padx=18, pady=(5, 12))

        tab_f = ctk.CTkFrame(tabela_container, fg_color="white")
        tab_f.pack(fill="both", expand=True, padx=8, pady=8)

        self.tree = ttk.Treeview(
            tab_f,
            columns=("ID", "MAT", "NOME", "SETOR", "CARGO", "TEL", "STATUS", "DATA"),
            show="headings"
        )

        colunas = [
            ("ID", 50, "center"),
            ("MAT", 100, "center"),
            ("NOME", 260, "w"),
            ("SETOR", 170, "w"),
            ("CARGO", 170, "w"),
            ("TEL", 130, "center"),
            ("STATUS", 110, "center"),
            ("DATA", 160, "center")
        ]

        for col, largura, anchor in colunas:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=largura, anchor=anchor)

        scrollbar = ttk.Scrollbar(tab_f, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # TAGS
        self.tree.tag_configure("BLOQUEADO", foreground="red")
        self.tree.tag_configure("PAR", background="#f8f9fa")
        self.tree.tag_configure("IMPAR", background="white")

    def criar_card(self, master, tit, val, cor, col):
        f = ctk.CTkFrame(master, fg_color=cor, width=180, height=78, corner_radius=8)
        f.grid(row=0, column=col, padx=10)
        f.pack_propagate(False)

        ctk.CTkLabel(
            f, text=tit, font=("Arial", 11, "bold"), text_color="white"
        ).pack(pady=(7, 0))

        lbl = ctk.CTkLabel(
            f, text=val, font=("Arial", 28, "bold"), text_color="white"
        )
        lbl.pack()

        f.lbl_valor = lbl
        return f

    # =========================
    # CADASTRO
    # =========================
    def abrir_janela_cadastro(self):
        self.jan_cad = ctk.CTkToplevel(self)
        self.jan_cad.title("Novo Cadastro")
        self.jan_cad.geometry("460x520")
        self.jan_cad.resizable(False, False)
        self.jan_cad.grab_set()

        ctk.CTkLabel(
            self.jan_cad,
            text="CADASTRO DE COLABORADOR",
            font=("Arial", 18, "bold")
        ).pack(pady=(20, 15))

        self.e_mat = self.add_entry("Matrícula")
        self.e_nom = self.add_entry("Nome Completo")
        self.e_set = self.add_entry("Setor")
        self.e_car = self.add_entry("Cargo")
        self.e_tel = self.add_entry("Telefone")

        b_f = ctk.CTkFrame(self.jan_cad, fg_color="transparent")
        b_f.pack(pady=25)

        ctk.CTkButton(
            b_f, text="SALVAR", fg_color="#0c8a43", hover_color="#086c34",
            command=self.salvar, width=120
        ).grid(row=0, column=0, padx=10)

        ctk.CTkButton(
            b_f, text="CANCELAR", fg_color="#b52d2d", hover_color="#922525",
            command=self.jan_cad.destroy, width=120
        ).grid(row=0, column=1, padx=10)

    def add_entry(self, txt):
        ctk.CTkLabel(self.jan_cad, text=txt, font=("Arial", 12)).pack(padx=45, anchor="w")
        e = ctk.CTkEntry(self.jan_cad, width=360, height=34)
        e.pack(pady=(3, 10))
        return e

    def salvar(self):
        matricula = self.e_mat.get().strip()
        nome = self.e_nom.get().strip()
        setor = self.e_set.get().strip()
        cargo = self.e_car.get().strip()
        telefone = self.e_tel.get().strip()

        if not matricula or not nome:
            messagebox.showwarning("Atenção", "Preencha pelo menos Matrícula e Nome.")
            return

        if inserir_colaborador(matricula, nome, setor, cargo, telefone):
            messagebox.showinfo("Sucesso", "Colaborador cadastrado com sucesso!")
            self.jan_cad.destroy()
            self.carregar_tabela()
            self.atualizar_dashboard()
        else:
            messagebox.showerror("Erro", "Matrícula já existe no sistema!")

    # =========================
    # TABELA / BUSCA
    # =========================
    def carregar_tabela(self, termo=None):
        for item in self.tree.get_children():
            self.tree.delete(item)

        dados = buscar_colaboradores(termo) if termo else listar_colaboradores()

        for i, d in enumerate(dados):
            tags = []

            # Zebra
            tags.append("PAR" if i % 2 == 0 else "IMPAR")

            # Status
            if d[6] == "BLOQUEADO":
                tags.append("BLOQUEADO")

            self.tree.insert("", "end", values=d, tags=tuple(tags))

    def atualizar_dashboard(self):
        t, a, b = contar_status()
        self.card_total.lbl_valor.configure(text=str(t))
        self.card_ativos.lbl_valor.configure(text=str(a))
        self.card_bloqueados.lbl_valor.configure(text=str(b))

    def buscar(self):
        termo = self.entry_busca.get().strip()
        self.carregar_tabela(termo if termo else None)

    def limpar_busca(self):
        self.entry_busca.delete(0, "end")
        self.carregar_tabela()

    # =========================
    # STATUS
    # =========================
    def alternar_status(self):
        sel = self.tree.selection()

        if not sel:
            messagebox.showwarning("Atenção", "Selecione um colaborador na tabela.")
            return

        item = self.tree.item(sel[0])["values"]
        status_atual = item[6]
        novo = "BLOQUEADO" if status_atual == "ATIVO" else "ATIVO"

        atualizar_status(item[0], novo)
        self.carregar_tabela()
        self.atualizar_dashboard()

        messagebox.showinfo("Status Alterado", f"Status alterado para: {novo}")

    # =========================
    # EXPORTAR EXCEL
    # =========================
    def gerar_excel(self):
        dados = listar_colaboradores()

        if not dados:
            messagebox.showwarning("Atenção", "Não há dados para exportar.")
            return

        df = pd.DataFrame(
            dados,
            columns=["ID", "MAT", "NOME", "SETOR", "CARGO", "TEL", "STATUS", "DATA"]
        )

        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Arquivo Excel", "*.xlsx")],
            initialfile=f"relatorio_portaria_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

        if path:
            df.to_excel(path, index=False)
            messagebox.showinfo("Sucesso", "Arquivo Excel exportado com sucesso!")

    # =========================
    # CÂMERA
    # =========================
    def abrir_camera(self):
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            messagebox.showerror("Erro", "Não foi possível acessar a câmera.")
            return

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            cv2.imshow("Monitoramento - Pressione Q para sair", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()

# =========================
# EXECUÇÃO
# =========================
if __name__ == "__main__":
    app = SistemaPortaria()
    app.mainloop()
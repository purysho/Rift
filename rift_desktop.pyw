from __future__ import annotations

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from rift_core import scan_tree, compare_trees, summarize, export_json, export_csv

BG = '#0b0f14'; PANEL = '#111821'; TEXT = '#eaf1f7'; MUTED = '#8ea0ae'; ACCENT = '#5ec8ff'; GOLD = '#e4b457'

class RiftApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Rift — Folder & Build Comparison')
        self.geometry('1180x760'); self.minsize(900, 600); self.configure(bg=BG)
        self.entries = []
        self._style(); self._build()

    def _style(self):
        s = ttk.Style(self); s.theme_use('clam')
        s.configure('.', background=BG, foreground=TEXT, fieldbackground=PANEL, bordercolor='#24303d')
        s.configure('TButton', background='#18222d', foreground=TEXT, padding=8)
        s.map('TButton', background=[('active', '#21303d')])
        s.configure('Treeview', background=PANEL, fieldbackground=PANEL, foreground=TEXT, rowheight=28)
        s.configure('Treeview.Heading', background='#16212b', foreground=TEXT)
        s.configure('TCheckbutton', background=BG, foreground=TEXT)

    def _build(self):
        header = tk.Frame(self, bg=BG); header.pack(fill='x', padx=24, pady=(20, 10))
        tk.Label(header, text='RIFT', bg=BG, fg=TEXT, font=('Segoe UI Semibold', 28)).pack(side='left')
        tk.Label(header, text='  compare two folders without touching either one', bg=BG, fg=MUTED, font=('Segoe UI', 11)).pack(side='left', pady=(12,0))

        chooser = tk.Frame(self, bg=BG); chooser.pack(fill='x', padx=24, pady=8)
        self.left_var = tk.StringVar(); self.right_var = tk.StringVar(); self.hash_var = tk.BooleanVar(value=True)
        for col, label, var in [(0,'LEFT / BASELINE',self.left_var),(1,'RIGHT / TARGET',self.right_var)]:
            box = tk.Frame(chooser, bg=PANEL, highlightbackground='#23313f', highlightthickness=1)
            box.grid(row=0,column=col,sticky='ew',padx=(0,8) if col==0 else (8,0))
            tk.Label(box,text=label,bg=PANEL,fg=ACCENT,font=('Segoe UI Semibold',9)).pack(anchor='w',padx=12,pady=(10,2))
            row=tk.Frame(box,bg=PANEL); row.pack(fill='x',padx=10,pady=(0,10))
            ttk.Entry(row,textvariable=var).pack(side='left',fill='x',expand=True)
            ttk.Button(row,text='Browse',command=lambda v=var:self._browse(v)).pack(side='left',padx=(8,0))
        chooser.grid_columnconfigure(0,weight=1); chooser.grid_columnconfigure(1,weight=1)

        bar = tk.Frame(self,bg=BG); bar.pack(fill='x',padx=24,pady=8)
        ttk.Checkbutton(bar,text='Hash files (slower, enables rename detection)',variable=self.hash_var).pack(side='left')
        ttk.Button(bar,text='Compare',command=self.compare).pack(side='left',padx=12)
        ttk.Button(bar,text='Export JSON',command=lambda:self.export('json')).pack(side='right')
        ttk.Button(bar,text='Export CSV',command=lambda:self.export('csv')).pack(side='right',padx=8)
        self.status = tk.Label(bar,text='Ready',bg=BG,fg=MUTED); self.status.pack(side='left',padx=14)

        self.summary = tk.Label(self,bg=BG,fg=GOLD,font=('Consolas',11),anchor='w'); self.summary.pack(fill='x',padx=24,pady=(4,8))
        cols=('status','path','from','left','right')
        self.tree=ttk.Treeview(self,columns=cols,show='headings')
        for c,t,w in [('status','STATUS',100),('path','PATH',480),('from','RENAMED FROM',300),('left','LEFT SIZE',100),('right','RIGHT SIZE',100)]:
            self.tree.heading(c,text=t); self.tree.column(c,width=w,anchor='w')
        self.tree.pack(fill='both',expand=True,padx=24,pady=(0,24))
        for tag,color in [('added','#8edb9b'),('removed','#ff7f7f'),('modified','#ffd166'),('renamed','#77c9ff'),('unchanged','#65727e')]: self.tree.tag_configure(tag,foreground=color)

    def _browse(self,var):
        p=filedialog.askdirectory()
        if p: var.set(p)

    def compare(self):
        l,r=self.left_var.get(),self.right_var.get()
        if not (Path(l).is_dir() and Path(r).is_dir()):
            messagebox.showerror('Rift','Choose two valid folders.'); return
        self.status.config(text='Scanning…');
        threading.Thread(target=self._do_compare,args=(l,r,self.hash_var.get()),daemon=True).start()

    def _do_compare(self,l,r,hash_files):
        try:
            left=scan_tree(l,hash_files=hash_files); right=scan_tree(r,hash_files=hash_files)
            entries=compare_trees(left,right,detect_renames=hash_files)
            self.after(0,lambda:self._show(entries))
        except Exception as e:
            self.after(0,lambda:messagebox.showerror('Rift',str(e)))

    def _show(self,entries):
        self.entries=entries; self.tree.delete(*self.tree.get_children())
        for e in entries:
            self.tree.insert('', 'end', values=(e.status.upper(),e.relpath,e.renamed_from or '',e.left.size if e.left else '',e.right.size if e.right else ''), tags=(e.status,))
        s=summarize(entries)
        self.summary.config(text='  ·  '.join(f'{k.upper()} {v}' for k,v in s.items()))
        self.status.config(text=f'{len(entries)} paths compared')

    def export(self,kind):
        if not self.entries: messagebox.showinfo('Rift','Run a comparison first.'); return
        ext='.json' if kind=='json' else '.csv'; p=filedialog.asksaveasfilename(defaultextension=ext,filetypes=[(kind.upper(),f'*{ext}')])
        if not p:return
        (export_json if kind=='json' else export_csv)(self.entries,p)
        self.status.config(text=f'Exported {Path(p).name}')

if __name__=='__main__': RiftApp().mainloop()
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from evaluate import compute_metrics, llm_judge, LLM_MODEL



class ASRBenchmarkGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ASR metrikas")
        self.root.resizable(False, False)

        self.manual_transcript_path = None
        self.auto_transcript_paths = []

        self._build_ui()

    # Grafiskā interfeisa izveidošana 
    def _build_ui(self):
        padding = {"padx": 12, "pady": 6}

        
        manual_frame = ttk.LabelFrame(self.root, text="Manuālā transkripcija")
        manual_frame.pack(fill="x", padx=16, pady=(16, 8))

        self.manual_label = ttk.Label(manual_frame, text="Fails nav izvēlēts", foreground="gray")
        self.manual_label.pack(side="left", expand=True, fill="x", **padding)

        ttk.Button(manual_frame, text="Pārlūkot", command=self._select_manual).pack(
            side="right", **padding
        )

        auto_frame = ttk.LabelFrame(self.root, text="Automātiskās transkripcijas (1–10)")
        auto_frame.pack(fill="both", expand=True, padx=16, pady=8)

        btn_row = ttk.Frame(auto_frame)
        btn_row.pack(fill="x", padx=8, pady=(6, 2))

        ttk.Button(btn_row, text="Pievienot failu", command=self._add_auto).pack(side="left", padx=(0, 6))
        ttk.Button(btn_row, text="Dzēst failu", command=self._remove_selected).pack(side="left")

        self.auto_listbox = tk.Listbox(auto_frame, height=10, selectmode=tk.MULTIPLE)
        self.auto_listbox.pack(fill="both", expand=True, padx=8, pady=(2, 8))

        scrollbar = ttk.Scrollbar(self.auto_listbox, orient="vertical", command=self.auto_listbox.yview)
        self.auto_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.auto_count_label = ttk.Label(auto_frame, text="0 / 10 files added", foreground="gray")
        self.auto_count_label.pack(anchor="e", padx=8, pady=(0, 4))


        self.evaluate_btn = ttk.Button(self.root, text="Novērtēt", command=self._evaluate)
        self.evaluate_btn.pack(pady=(4, 8))

      
        results_frame = ttk.LabelFrame(self.root, text="Rezultāti")
        results_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        columns = ("transcript", "wer", "cer", "llm")
        self.results_tree = ttk.Treeview(
            results_frame, columns=columns, show="headings", height=10
        )
        self.results_tree.heading("transcript", text="Transkripcija")
        self.results_tree.heading("wer", text="WER")
        self.results_tree.heading("cer", text="CER")
        self.results_tree.heading("llm", text=f"LLM ({LLM_MODEL})")
        self.results_tree.column("transcript", width=240, stretch=True)
        self.results_tree.column("wer", width=80, anchor="center")
        self.results_tree.column("cer", width=80, anchor="center")
        self.results_tree.column("llm", width=220, anchor="center")
        self.results_tree.pack(fill="both", expand=True, padx=8, pady=8)






    # Failu apstrādes funkcijas
    
    def _select_manual(self):
        path = filedialog.askopenfilename(
            title="Izvēlēties manuālo transkripciju",
            filetypes=[("Text files", "*.txt")],
        )
        if path:
            self.manual_transcript_path = path
            self.manual_label.config(text=path, foreground="black")

    def _add_auto(self):
        remaining = 10 - len(self.auto_transcript_paths)
        if remaining <= 0:
            messagebox.showwarning("Failu skaita ierobežojums ir pārsniegts", "Var pievienot ne vairāk kā 10 failus")
            return

        paths = filedialog.askopenfilenames(
            title="Select Automatic Transcript(s)",
            filetypes=[("Text files", "*.txt")],
        )
        if not paths:
            return

        added = 0
        for path in paths:
            if len(self.auto_transcript_paths) >= 10:
                messagebox.showwarning(
                    "Failu skaita ierobežojums ir pārsniegts",
                    f"Tikai  {added} faili ir pievienoti",
                )
                break
            if path not in self.auto_transcript_paths:
                self.auto_transcript_paths.append(path)
                self.auto_listbox.insert(tk.END, path)
                added += 1

        self._update_count_label()

    def _remove_selected(self):
        selected_indices = list(self.auto_listbox.curselection())
        for index in reversed(selected_indices):
            self.auto_listbox.delete(index)
            del self.auto_transcript_paths[index]
        self._update_count_label()

    def _update_count_label(self):
        count = len(self.auto_transcript_paths)
        color = "red" if count > 10 else ("black" if count > 0 else "gray")
        self.auto_count_label.config(text=f"{count} / 10 faili pievienoti", foreground=color)





    # Transkripciju novērtēšana 
    def _evaluate(self):
        if not self.manual_transcript_path:
            messagebox.showwarning("Missing Input", "Izvēlieties manuālo transkripciju")
            return
        if not self.auto_transcript_paths:
            messagebox.showwarning("Missing Input", "Pievienojiet vismaz vienu automātisku transkripciju")
            return

        try:
            reference = open(self.manual_transcript_path).read()
        except OSError as e:
            messagebox.showerror("File Error", f"Nepareizs faila formāts:\n{e}")
            return

        self.results_tree.delete(*self.results_tree.get_children())
        self.evaluate_btn.config(state="disabled")

        row_ids = []
        hypotheses = []

        for path in self.auto_transcript_paths:
            try:
                hypothesis = open(path).read()
            except OSError as e:
                messagebox.showerror("File Error", f"Nepareizs faila formāts:\n{path}\n{e}")
                self.evaluate_btn.config(state="normal")
                return

            wer, cer = compute_metrics(reference, hypothesis)

            row_id = self.results_tree.insert(
                "", tk.END,
                values=(path, f"{wer:.2%}", f"{cer:.2%}", "..."),
            )
            row_ids.append(row_id)
            hypotheses.append(hypothesis)

        threading.Thread(
            target=self._run_llm_scoring,
            args=(reference, hypotheses, row_ids),
            daemon=True,
        ).start()

    def _run_llm_scoring(self, reference, hypotheses, row_ids):
        for row_id, hypothesis in zip(row_ids, hypotheses):
            try:
                score = llm_judge(reference, hypothesis)
                llm_text = f"{(1 - score):.2%}"
            except Exception as e:
                import traceback, sys
                traceback.print_exc(file=sys.stderr)
                llm_text = f"Error: {e}"
            self.root.after(0, self._update_llm_cell, row_id, llm_text)
        self.root.after(0, lambda: self.evaluate_btn.config(state="normal"))

    def _update_llm_cell(self, row_id, llm_text):
        current = self.results_tree.item(row_id, "values")
        self.results_tree.item(row_id, values=(current[0], current[1], current[2], llm_text))


def main():
    root = tk.Tk()
    ASRBenchmarkGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

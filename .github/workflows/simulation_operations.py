import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ui_setup import setup_ui, clear_graph
import math

class CNCApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulazione CNC")
        self.left_frame = ttk.Frame(root)
        self.left_frame.pack(side="left", fill="y")
        self.right_frame = ttk.Frame(root)
        self.right_frame.pack(side="right", fill="both", expand=True)

        self.program_listbox = tk.Listbox(self.left_frame)
        self.program_listbox.pack(padx=10, pady=10, fill="both", expand=True)

        self.show_graph()

        self.g00_count = 0  # Inizializza il contatore G00

    def show_graph(self):
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.right_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas.draw()

    def clear_left_frame(self):
        for widget in self.left_frame.winfo_children():
            widget.destroy()

    def cancel_new_program(self):
        reset_simulation(self)  # Aggiungi il reset della simulazione
        clear_graph(self)  # Cancella il grafico e lo rende bianco
        self.clear_left_frame()
        self.program_listbox.pack(padx=10, pady=10, fill="both", expand=True)
        setup_ui(self)  # Reimposta l'interfaccia utente

    def show_message(self, message, type="info"):
        if type == "error":
            tk.messagebox.showerror("Errore", message)
        else:
            tk.messagebox.showinfo("Informazione", message)

def prepare_simulation(app):
    """Prepara la simulazione delle istruzioni G-code."""
    selected_program_index = app.program_listbox.curselection()
    if not selected_program_index:
        app.show_message("Errore: Nessun programma selezionato", "error")
        return

    program_path = app.program_listbox.get(selected_program_index)
    if not program_path.endswith('.gcode'):
        app.show_message("Errore: Seleziona un file G-code", "error")
        return

    app.clear_left_frame()

    # Mostra le istruzioni G-code
    with open(program_path, 'r') as file:
        gcode_instructions = file.readlines()

    app.gcode_listbox = tk.Listbox(app.left_frame)
    app.gcode_listbox.pack(padx=10, pady=10, fill="both", expand=True)
    for instruction in gcode_instructions:
        app.gcode_listbox.insert(tk.END, instruction.strip())

    app.start_simulation_button = ttk.Button(app.left_frame, text="Avvia Simulazione", command=lambda: simulate_program(app, gcode_instructions))
    app.start_simulation_button.pack(pady=10)

    app.step_simulation_button = ttk.Button(app.left_frame, text="Esegui Istruzione", command=lambda: step_simulation(app))
    app.step_simulation_button.pack(pady=10)

    app.pause_simulation_button = ttk.Button(app.left_frame, text="Pausa", command=lambda: pause_simulation(app))
    app.pause_simulation_button.pack(pady=10)

    app.resume_simulation_button = ttk.Button(app.left_frame, text="Riprendi", command=lambda: resume_simulation(app))
    app.resume_simulation_button.pack(pady=10)

    app.flip_simulation_button = ttk.Button(app.left_frame, text="Ribalta Disegno", command=lambda: flip_and_simulate(app))
    app.flip_simulation_button.pack(pady=10)

    app.back_button = ttk.Button(app.left_frame, text="Indietro", command=app.cancel_new_program)
    app.back_button.pack(pady=10)

    app.show_message("Premi 'Avvia Simulazione' per iniziare o 'Esegui Istruzione' per eseguire un'istruzione alla volta.")

    # Inizializza l'indice dell'istruzione corrente e la posizione
    reset_simulation(app)

    # Inizializza gcode_instructions nell'app
    app.gcode_instructions = gcode_instructions

    # Mostra immediatamente il triangolino alla posizione iniziale
    app.show_graph()
    initialize_graph(app)

def reset_simulation(app, reset_graph=True):
    """Resetta la simulazione alle impostazioni iniziali."""
    app.current_instruction_index = 0
    app.current_position = [30, -10]  # Posizione iniziale
    app.simulation_paused = False
    app.g00_count = 0  # Reset del contatore dei comandi G00
    if reset_graph:
        initialize_graph(app)
    deselect_all_instructions(app)

def initialize_graph(app):
    """Inizializza il grafico."""
    app.ax.clear()
    app.ax.set_xlabel("X (mm)")
    app.ax.set_ylabel("Y (mm)")
    app.ax.set_xlim([0, 35])
    app.ax.set_ylim([-10, 10])
    app.canvas.draw()

def deselect_all_instructions(app):
    """Deseleziona tutte le istruzioni nella listbox."""
    for i in range(app.gcode_listbox.size()):
        app.gcode_listbox.itemconfig(i, {'bg':'white'})

def simulate_program(app, gcode_instructions):
    """Simula tutte le istruzioni G-code sul grafico."""
    reset_simulation(app)
    app.gcode_instructions = gcode_instructions
    execute_next_instruction(app)

def flip_and_simulate(app):
    """Ribalta le istruzioni G-code eseguite fino a questo momento e simula il programma sul grafico."""
    executed_instructions = app.gcode_instructions[:app.current_instruction_index]
    flipped_instructions = flip_y_instructions(executed_instructions)
    current_position_backup = app.current_position.copy()  # Backup della posizione corrente
    app.current_instruction_index_backup = app.current_instruction_index  # Backup dell'indice corrente
    g00_count_backup = app.g00_count  # Backup del contatore G00
    reset_simulation(app, reset_graph=False)  # Reset della simulazione senza cancellare il grafico
    app.current_position = current_position_backup  # Ripristina la posizione corrente
    app.current_instruction_index = app.current_instruction_index_backup  # Ripristina l'indice corrente
    app.g00_count = g00_count_backup  # Ripristina il contatore G00
    simulate_flipped_program(app, flipped_instructions)
    app.current_position = current_position_backup  # Riporta la posizione alla posizione di backup

def flip_y_instructions(gcode_instructions):
    """Ribalta il segno della coordinata Y nelle istruzioni G-code."""
    flipped_instructions = []
    for instruction in gcode_instructions:
        parts = instruction.split()
        flipped_parts = []
        for part in parts:
            if part.startswith('Y'):
                y_value = float(part[1:])
                flipped_parts.append(f'Y{-y_value}')
            else:
                flipped_parts.append(part)
        flipped_instructions.append(' '.join(flipped_parts))
    return flipped_instructions

def simulate_flipped_program(app, gcode_instructions):
    """Simula le istruzioni G-code ribaltate senza cancellare il grafico precedente."""
    app.gcode_instructions = gcode_instructions
    app.current_instruction_index = 0
    execute_next_instruction(app)

def execute_next_instruction(app):
    """Esegue la prossima istruzione G-code."""
    if app.simulation_paused:
        return

    if app.current_instruction_index >= len(app.gcode_instructions):
        app.show_message("Simulazione completata")
        return

    # Deseleziona l'istruzione precedente
    if app.current_instruction_index > 0:
        app.gcode_listbox.itemconfig(app.current_instruction_index - 1, {'bg':'white'})

    instruction = app.gcode_instructions[app.current_instruction_index].strip()
    app.gcode_listbox.itemconfig(app.current_instruction_index, {'bg':'yellow'})  # Evidenzia l'istruzione corrente
    app.canvas.draw()
    app.root.update()

    x, y = app.current_position
    x, y, feed_rate = execute_gcode_instruction(app, instruction, x, y)

    if instruction.startswith('G00') or instruction.startswith('G01'):
        if instruction.startswith('G00'):
            app.g00_count += 1
            if app.g00_count == 1:
                draw_line(app, app.current_position, [x, y], 'ro-')  # Primo G00
            else:
                app.current_position = [x, y]  # Aggiorna solo la posizione senza disegnare la linea
                app.show_message(f"Eseguendo: {instruction}")
                app.current_instruction_index += 1
                if app.current_instruction_index < len(app.gcode_instructions):
                    execute_next_instruction(app)
                return
        else:
            draw_line(app, app.current_position, [x, y], 'bo-')
        app.current_position = [x, y]
        app.canvas.draw()
        app.show_message(f"Eseguendo: {instruction}")

    app.current_instruction_index += 1

    if instruction.startswith('M30'):
        app.show_message("Simulazione completata")
        return

    # Esegui la prossima istruzione immediatamente
    execute_next_instruction(app)

def step_simulation(app):
    """Esegue un'istruzione G-code alla volta sul grafico."""
    if app.current_instruction_index >= app.gcode_listbox.size():
        app.show_message("Tutte le istruzioni sono state eseguite")
        reset_simulation(app)
        return

    # Deseleziona l'istruzione precedente
    if app.current_instruction_index > 0:
        app.gcode_listbox.itemconfig(app.current_instruction_index - 1, {'bg':'white'})

    instruction = app.gcode_listbox.get(app.current_instruction_index).strip()
    app.gcode_listbox.itemconfig(app.current_instruction_index, {'bg':'yellow'})  # Evidenzia l'istruzione corrente
    app.canvas.draw()
    app.root.update()

    x, y = app.current_position
    x, y, feed_rate = execute_gcode_instruction(app, instruction, x, y)

    if instruction.startswith('G00') or instruction.startswith('G01'):
        if instruction.startswith('G00'):
            app.g00_count += 1
            if app.g00_count == 1:
                draw_line(app, app.current_position, [x, y], 'ro-')  # Primo G00
            else:
                app.current_position = [x, y]  # Aggiorna solo la posizione senza disegnare la linea
                app.show_message(f"Eseguendo: {instruction}")
                app.current_instruction_index += 1
                return
        else:
            draw_line(app, app.current_position, [x, y], 'bo-')
        app.current_position = [x, y]
        app.canvas.draw()
        app.show_message(f"Eseguendo: {instruction}")

    app.current_instruction_index += 1

    if instruction.startswith('M30'):
        app.show_message("Simulazione completata")
        reset_simulation(app)

def pause_simulation(app):
    """Mette in pausa la simulazione."""
    app.simulation_paused = True
    app.show_message("Simulazione messa in pausa")

def resume_simulation(app):
    """Riprende la simulazione."""
    if app.simulation_paused:
        app.simulation_paused = False
        app.show_message("Simulazione ripresa")
        execute_next_instruction(app)

def execute_gcode_instruction(app, instruction, current_x, current_y):
    """Esegue una singola istruzione G-code e aggiorna la posizione."""
    x, y = current_x, current_y
    feed_rate = None
    if instruction.startswith('G1') or instruction.startswith('G0') or instruction.startswith('G00') or instruction.startswith('G01'):
        parts = instruction.split()
        for part in parts:
            if part.startswith('X'):
                x = float(part[1:])  # Aggiorna la coordinata X
            elif part.startswith('Y'):
                y = float(part[1:])  # Aggiorna la coordinata Y
            elif part.startswith('F'):
                feed_rate = float(part[1:])
    return x, y, feed_rate

def draw_line(app, start, end, style):
    """Disegna una linea sul grafico."""
    app.ax.plot([start[0], end[0]], [start[1], end[1]], style)
    app.canvas.draw()

def cancel_simulation(app):
    """Cancella la simulazione e pulisce il grafico."""
    app.clear_simulation_frame()
    clear_graph(app)
    app.initialize_left_frame()  

# Avvio dell'applicazione
if __name__ == "__main__":
    root = tk.Tk()
    app = CNCApp(root)
    root.mainloop()
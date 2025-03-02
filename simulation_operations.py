import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import math

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

    app.back_button = ttk.Button(app.left_frame, text="Indietro", command=app.cancel_new_program)
    app.back_button.pack(pady=10)

    app.show_message("Premi 'Avvia Simulazione' per iniziare o 'Esegui Istruzione' per eseguire un'istruzione alla volta.")

    # Inizializza l'indice dell'istruzione corrente e la posizione
    reset_simulation(app)

    # Mostra immediatamente il triangolino alla posizione iniziale
    app.show_graph()
    initialize_graph(app)

def reset_simulation(app):
    """Resetta la simulazione alle impostazioni iniziali."""
    app.current_instruction_index = 0
    app.current_position = [30, -10]  # Posizione iniziale
    app.simulation_paused = False
    initialize_graph(app)
    deselect_all_instructions(app)

def initialize_graph(app):
    """Inizializza il grafico."""
    app.ax.clear()
    app.ax.set_xlabel("X")
    app.ax.set_ylabel("Y")
    app.ax.set_xlim([0, 35])
    app.ax.set_ylim([-20, 20])
    triangle = [[30, -10], [30-1, -10-1], [30+1, -10-1]]
    app.ax.add_patch(plt.Polygon(triangle, closed=True, color='green'))
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
    x, y, duration, feed_rate = execute_gcode_instruction(app, instruction, x, y)

    if instruction.startswith('G00') or instruction.startswith('G01'):
        if instruction.startswith('G00'):
            draw_line(app, app.current_position, [x, y], 'ro-')
        else:
            draw_line_with_speed(app, app.current_position, [x, y], 'bo-', duration, feed_rate)
        app.current_position = [x, y]
        app.canvas.draw()
        app.show_message(f"Eseguendo: {instruction}")

    app.current_instruction_index += 1

    if instruction.startswith('M30'):
        app.show_message("Simulazione completata")
        return

    # Usa after per eseguire la prossima istruzione dopo la durata calcolata
    app.root.after(int(duration * 1000), lambda: execute_next_instruction(app))

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
    x, y, duration, feed_rate = execute_gcode_instruction(app, instruction, x, y)

    if instruction.startswith('G00') or instruction.startswith('G01'):
        if instruction.startswith('G00'):
            draw_line(app, app.current_position, [x, y], 'ro-')
        else:
            draw_line_with_speed(app, app.current_position, [x, y], 'bo-', duration, feed_rate)
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
    duration = 0  # Inizializza la variabile duration
    if instruction.startswith('G1') or instruction.startswith('G0') or instruction.startswith('G00') or instruction.startswith('G01'):
        parts = instruction.split()
        for part in parts:
            if part.startswith('X'):
                x = float(part[1:])  # Aggiorna la coordinata X
            elif part.startswith('Y'):
                y = float(part[1:])  # Aggiorna la coordinata Y
            elif part.startswith('F'):
                feed_rate = float(part[1:])
                
        # Calcola la durata basata sulla velocità di avanzamento (feed rate)
        if feed_rate:
            distance = math.sqrt((x - current_x)**2 + (y - current_y)**2)
            duration = distance / feed_rate
    return x, y, duration, feed_rate

def draw_line_with_speed(app, start, end, style, duration, feed_rate):
    """Disegna una linea sul grafico in modo incrementale rispettando la velocità di avanzamento."""
    x0, y0 = start
    x1, y1 = end
    steps = int(duration * 1000 / 10)  # Numero di passi per l'animazione
    dx = (x1 - x0) / steps
    dy = (y1 - y0) / steps

    def draw_step(step):
        if step > steps:
            return
        app.ax.plot([x0 + dx * (step - 1), x0 + dx * step], [y0 + dy * (step - 1), y0 + dy * step], style)
        app.canvas.draw()
        app.root.after(10, lambda: draw_step(step + 1))
    
    draw_step(1)

def draw_line(app, start, end, style):
    """Disegna una linea sul grafico."""
    app.ax.plot([start[0], end[0]], [start[1], end[1]], style)
    app.canvas.draw()
import os
import subprocess

def translate_gcode(app):
    """Traduci un programma G-code in un programma Arduino."""
    selected_program_index = app.program_listbox.curselection()
    if not selected_program_index:
        app.show_message("Errore: Nessun programma selezionato", "error")
        return

    program_path = app.program_listbox.get(selected_program_index)
    if program_path.endswith('.gcode'):
        app.translate_gcode_to_arduino(program_path)
    else:
        app.show_message("Errore: Seleziona un file G-code", "error")

def translate_gcode_to_arduino(app, program_path):
    """Traduci un programma G-code in comandi Arduino e scrivilo in un file .ino."""
    try:
        with open(program_path, 'r') as file:
            gcode_data = file.readlines()

        arduino_commands = app.convert_gcode_to_arduino(gcode_data)

        arduino_file_base = os.path.splitext(os.path.basename(program_path))[0]
        arduino_dir = os.path.join(os.path.dirname(program_path), arduino_file_base)
        os.makedirs(arduino_dir, exist_ok=True)

        arduino_file_path = os.path.join(arduino_dir, f"{arduino_file_base}.ino")
        with open(arduino_file_path, 'w') as arduino_file:
            arduino_file.write(arduino_commands)

        app.show_message(f"Programma tradotto e salvato in {arduino_file_path}", "info")
        return arduino_file_path
    except Exception as e:
        app.show_message(f"Errore: Impossibile tradurre il programma G-code: {e}", "error")
        return None

def convert_gcode_to_arduino(gcode_data):
    """Converti le istruzioni G-code in comandi Arduino."""
    arduino_code = """
// Dichiarazione delle funzioni
void blink(int x, int y, int z);
void turnOnPin(int pin, int duration);
void turnOnAnalogPin(int pin, int duration);

// Configurazione iniziale
void setup() {
  pinMode(13, OUTPUT);  // Pin per il controllo
  Serial.begin(115200);  // Inizializza la comunicazione seriale
}

// Funzioni di utilità
void blink(int x, int y, int z) {
  int onTime = y * 1000;  // Converti in millisecondi
  int offTime = z * 1000; // Converti in millisecondi

  for (int i = 0; i < x; i++) {
    digitalWrite(13, HIGH); // Accendi il pin
    delay(onTime);          // Aspetta il tempo di accensione
    digitalWrite(13, LOW);  // Spegni il pin
    delay(offTime);         // Aspetta il tempo di spegnimento
  }
}

void turnOnPin(int pin, int duration) {
  pinMode(pin, OUTPUT);
  digitalWrite(pin, HIGH);
  delay(duration * 1000); // Converti in millisecondi
  digitalWrite(pin, LOW);
}

void turnOnAnalogPin(int pin, int duration) {
  pinMode(pin, OUTPUT);
  analogWrite(pin, 255); // Imposta il valore analogico massimo
  delay(duration * 1000); // Converti in millisecondi
  analogWrite(pin, 0); // Spegni il pin analogico
}

void loop() {
"""
    for line in gcode_data:
        line = line.strip()
        if line.startswith('G1'):
            parts = line.split()
            x = y = z = None
            for part in parts:
                if part.startswith('X'):
                    x = part[1:]
                elif part.startswith('Y'):
                    y = part[1:]
                elif part.startswith('Z'):
                    z = part[1:]
            if x and y and z:
                arduino_code += f'  blink({x}, {y}, {z});\n'
        elif line.startswith('G2'):
            parts = line.split()
            pin = duration = None
            for part in parts:
                if part.startswith('X'):
                    pin = part[1:]
                elif part.startswith('Y'):
                    duration = part[1:]
            if pin and duration:
                arduino_code += f'  turnOnPin({pin}, {duration});\n'
        elif line.startswith('G3'):
            parts = line.split()
            pin = duration = None
            for part in parts:
                if part.startswith('X'):
                    pin = part[1:]
                elif part.startswith('Y'):
                    duration = part[1:]
            if pin and duration:
                arduino_code += f'  turnOnAnalogPin({pin}, {duration});\n'
    arduino_code += """
}
"""
    return arduino_code

def upload_to_arduino(app):
    """Carica il programma selezionato su Arduino."""
    selected_program_index = app.program_listbox.curselection()
    if not selected_program_index:
        app.show_message("Errore: Nessun programma selezionato", "error")
        return

    program_path = app.program_listbox.get(selected_program_index)

    if program_path.endswith('.gcode'):
        program_path = app.translate_gcode_to_arduino(program_path)
        if not program_path:
            return

    if program_path.endswith('.ino'):
        try:
            if not os.path.isfile(program_path):
                app.show_message(f"Errore: Il file {program_path} non esiste.", "error")
                return

            arduino_cli_path = os.path.join(os.path.dirname(__file__), 'arduino-cli', 'arduino-cli.exe')
            sketch_dir = os.path.dirname(program_path)

            compile_result = subprocess.run([arduino_cli_path, "compile", "--fqbn", "arduino:avr:uno", sketch_dir], capture_output=True, text=True)
            if compile_result.returncode != 0:
                app.show_message(f"Errore durante la compilazione: {compile_result.stderr}", "error")
                print(f"Errore durante la compilazione: {compile_result.stderr}")
                return

            upload_result = subprocess.run([arduino_cli_path, "upload", "-p", "COM3", "--fqbn", "arduino:avr:uno", sketch_dir], capture_output=True, text=True)
            if upload_result.returncode == 0:
                app.show_message("Programma caricato su Arduino con successo", "info")
            else:
                app.show_message(f"Errore durante il caricamento: {upload_result.stderr}", "error")
                print(f"Errore durante il caricamento: {upload_result.stderr}")
        except Exception as e:
            app.show_message(f"Errore: Impossibile caricare il programma su Arduino: {e}", "error")
            print(f"Impossibile caricare il programma su Arduino: {e}")
    else:
        app.show_message("Errore: Seleziona un file .ino per caricare su Arduino", "error")
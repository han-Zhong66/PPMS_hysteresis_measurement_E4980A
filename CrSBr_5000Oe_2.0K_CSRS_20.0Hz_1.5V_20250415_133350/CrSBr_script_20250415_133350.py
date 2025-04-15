import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pyvisa
import time
import csv
import matplotlib.pyplot as plt
import matplotlib
import MultiPyVu as mpv
import os
from datetime import datetime
import traceback
import shutil
import numpy as np

# Prepare for plotting
matplotlib.use("TkAgg")

class MeasurementGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PPMS + E4980B Measurement Config")

        self.lcr = None
        self.rm = None
        self.client = None
        self.available_lcrs = []

        # Initialize data storage lists
        self.fields = []
        self.caps = []
        self.ress = []
        self.temps = []

        # Measurement parameters
        self.lcr_mode = tk.StringVar(value="CSRS")
        self.lcr_freq = tk.StringVar(value="20")
        self.lcr_volt = tk.StringVar(value="0.3")
        self.settle_time_magnetic = tk.StringVar(value="1.0")
        self.settle_time_lcr = tk.StringVar(value="0.5")
        self.max_field = tk.StringVar(value="5000")
        self.magnetic_step = tk.StringVar(value="100")
        self.magnetic_rate = tk.StringVar(value="100")
        self.target_temp = tk.StringVar(value="100")
        self.temp_rate = tk.StringVar(value="20")
        self.stabilize_time = tk.StringVar(value="10")
        self.material = tk.StringVar(value="CrSBr")

        # Create GUI sections
        self.create_host_output_frame()
        self.create_magnetic_field_frame()
        self.create_temperature_frame()
        self.create_lcr_frame()
        self.create_visa_frame()
        self.create_run_button()

        # Auto-detect LCR meters on startup
        self.detect_lcr()

        # Set up trace callbacks for all filename components
        self.material.trace_add("write", self._handle_material_change)
        self.max_field.trace_add("write", self._handle_parameter_change)
        self.target_temp.trace_add("write", self._handle_parameter_change)
        self.lcr_mode.trace_add("write", self._handle_parameter_change)
        self.lcr_freq.trace_add("write", self._handle_parameter_change)
        self.lcr_volt.trace_add("write", self._handle_parameter_change)

    def create_magnetic_field_frame(self):
        frame = ttk.LabelFrame(self.root, text="Magnetic Field Parameters")
        frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        ttk.Label(frame, text="Max Field (Oe):").grid(row=0, column=0)
        ttk.Entry(frame, textvariable=self.max_field).grid(row=0, column=1)
        ttk.Label(frame, text="Step (Oe):").grid(row=1, column=0)
        ttk.Entry(frame, textvariable=self.magnetic_step).grid(row=1, column=1)
        ttk.Label(frame, text="Rate (Oe/s):").grid(row=2, column=0)
        ttk.Entry(frame, textvariable=self.magnetic_rate).grid(row=2, column=1)

    def create_temperature_frame(self):
        frame = ttk.LabelFrame(self.root, text="Temperature Parameters")
        frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        # Temperature mode selection
        self.temp_mode = tk.StringVar(value="single")  # "single" or "sweep"
        ttk.Radiobutton(frame, text="Single Temperature", variable=self.temp_mode,
                        value="single", command=self.update_temp_ui).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(frame, text="Temperature List", variable=self.temp_mode,
                        value="list", command=self.update_temp_ui).grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(frame, text="Temperature Sweep", variable=self.temp_mode,
                        value="sweep", command=self.update_temp_ui).grid(row=0, column=2, sticky="w")

        # Single temperature controls
        self.single_temp_frame = ttk.Frame(frame)
        ttk.Label(self.single_temp_frame, text="Target Temp (K):").grid(row=0, column=0)
        self.target_temp = tk.StringVar(value="100")
        ttk.Entry(self.single_temp_frame, textvariable=self.target_temp).grid(row=0, column=1)
        self.single_temp_frame.grid(row=1, column=0, columnspan=3, sticky="ew")

        # Temperature list controls
        self.temp_list_frame = ttk.Frame(frame)
        ttk.Label(self.temp_list_frame, text="Temp List (K, comma separated):").grid(row=0, column=0)
        self.temp_list = tk.StringVar(value="100,200,300")
        ttk.Entry(self.temp_list_frame, textvariable=self.temp_list, width=30).grid(row=0, column=1)
        self.temp_list_frame.grid(row=1, column=0, columnspan=3, sticky="ew")
        self.temp_list_frame.grid_remove()

        # Temperature sweep controls
        self.temp_sweep_frame = ttk.Frame(frame)
        ttk.Label(self.temp_sweep_frame, text="Start (K):").grid(row=0, column=0)
        self.temp_start = tk.StringVar(value="100")
        ttk.Entry(self.temp_sweep_frame, textvariable=self.temp_start).grid(row=0, column=1)

        ttk.Label(self.temp_sweep_frame, text="End (K):").grid(row=0, column=2)
        self.temp_end = tk.StringVar(value="300")
        ttk.Entry(self.temp_sweep_frame, textvariable=self.temp_end).grid(row=0, column=3)

        ttk.Label(self.temp_sweep_frame, text="Step (K):").grid(row=0, column=4)
        self.temp_step = tk.StringVar(value="50")
        ttk.Entry(self.temp_sweep_frame, textvariable=self.temp_step).grid(row=0, column=5)
        self.temp_sweep_frame.grid(row=1, column=0, columnspan=3, sticky="ew")
        self.temp_sweep_frame.grid_remove()

        # Common parameters
        ttk.Label(frame, text="Rate (K/min):").grid(row=2, column=0)
        self.temp_rate = tk.StringVar(value="20")
        ttk.Entry(frame, textvariable=self.temp_rate).grid(row=2, column=1)

        ttk.Label(frame, text="Stabilize (s):").grid(row=2, column=2)
        self.stabilize_time = tk.StringVar(value="10")
        ttk.Entry(frame, textvariable=self.stabilize_time).grid(row=2, column=3)

        # Initialize UI
        self.update_temp_ui()

    def update_temp_ui(self):
        """Show/hide appropriate temperature controls based on selected mode"""
        mode = self.temp_mode.get()
        self.single_temp_frame.grid_remove()
        self.temp_list_frame.grid_remove()
        self.temp_sweep_frame.grid_remove()

        if mode == "single":
            self.single_temp_frame.grid()
        elif mode == "list":
            self.temp_list_frame.grid()
        elif mode == "sweep":
            self.temp_sweep_frame.grid()
    # def create_temperature_frame(self):
    #     frame = ttk.LabelFrame(self.root, text="Temperature Parameters")
    #     frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
    #
    #     ttk.Label(frame, text="Target Temp (K):").grid(row=0, column=0)
    #     ttk.Entry(frame, textvariable=self.target_temp).grid(row=0, column=1)
    #     ttk.Label(frame, text="Rate (K/min):").grid(row=1, column=0)
    #     ttk.Entry(frame, textvariable=self.temp_rate).grid(row=1, column=1)
    #     ttk.Label(frame, text="Stabilize (s):").grid(row=2, column=0)
    #     ttk.Entry(frame, textvariable=self.stabilize_time).grid(row=2, column=1)

    def create_host_output_frame(self):
        frame = ttk.LabelFrame(self.root, text="Host and Output")
        frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        # Initialize variables
        self.host_ip = tk.StringVar(value="10.227.234.170")
        self.folder_path = tk.StringVar(value=os.getcwd())
        self.data_file = tk.StringVar()
        self.plot_file = tk.StringVar()

        # Generate timestamp only once at startup
        self._timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._current_material = self.material.get() or "material"

        # Set initial filenames
        self._update_filenames()

        # Create widgets
        ttk.Label(frame, text="Material:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.material).grid(row=0, column=1, sticky="ew")

        ttk.Label(frame, text="QD Server IP:").grid(row=1, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.host_ip).grid(row=1, column=1, sticky="ew")

        ttk.Label(frame, text="Folder:").grid(row=2, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.folder_path).grid(row=2, column=1, sticky="ew")
        ttk.Button(frame, text="Browse", command=self.browse_folder).grid(row=2, column=2)

        ttk.Label(frame, text="Data File:").grid(row=3, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.data_file).grid(row=3, column=1, sticky="ew")

        ttk.Label(frame, text="Plot File:").grid(row=4, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.plot_file).grid(row=4, column=1, sticky="ew")

        # Set up trace callbacks
        self.material.trace_add("write", self._handle_material_change)
        self.max_field.trace_add("write", self._handle_parameter_change)
        self.target_temp.trace_add("write", self._handle_parameter_change)
        self.data_file.trace_add("write", lambda *_: self._track_custom_part("data"))
        self.plot_file.trace_add("write", lambda *_: self._track_custom_part("plot"))

    def _handle_material_change(self, *args):
        """Update filenames when material changes"""
        new_material = self.material.get()
        if not new_material or new_material == self._current_material:
            return

        self._current_material = new_material
        self._update_filenames()

    def _handle_parameter_change(self, *args):
        """Update filenames when field or temperature changes"""
        self._update_filenames()

    def _track_custom_part(self, file_type):
        """Remember custom parts of filenames"""
        current_value = self.data_file.get() if file_type == "data" else self.plot_file.get()
        expected_base = self._generate_base_name()

        if current_value.startswith(expected_base):
            # Only update suffix if base matches
            suffix = current_value[len(expected_base):]
            if file_type == "data":
                self._data_suffix = suffix
            else:
                self._plot_suffix = suffix
        else:
            # Treat as completely custom filename
            if file_type == "data":
                self._data_suffix = current_value
            else:
                self._plot_suffix = current_value

    def _generate_base_name(self):
        """Generate the base filename with current parameters"""
        try:
            field = int(self.max_field.get())
            temp = float(self.target_temp.get())
            mode = self.lcr_mode.get()
            freq = float(self.lcr_freq.get())
            volt = float(self.lcr_volt.get())
            return f"{self._current_material}_{field}Oe_{temp}K_{mode}_{freq}Hz_{volt}V_{self._timestamp}"
        except (ValueError, AttributeError):
            return f"{self._current_material}_{self._timestamp}"

    def _update_filenames(self):
        """Update both filename displays using current components"""
        base = self._generate_base_name()

        # For data file
        if not hasattr(self, '_data_suffix') or not self._data_suffix.startswith("_"):
            self.data_file.set(f"{base}.dat")

        # For plot file
        if not hasattr(self, '_plot_suffix') or not self._plot_suffix.startswith("_"):
            self.plot_file.set(f"{base}.png")

    def create_visa_frame(self):
        frame = ttk.LabelFrame(self.root, text="LCR VISA Resource")
        frame.grid(row=5, column=0, padx=10, pady=5, sticky="ew")
        self.visa_info = tk.StringVar(value="No LCR connected.")

        ttk.Label(frame, textvariable=self.visa_info).pack(anchor="w", padx=5, pady=5)
        ttk.Button(frame, text="Refresh LCR", command=self.detect_lcr).pack(anchor="e", padx=5, pady=5)

    def create_lcr_frame(self):
        frame = ttk.LabelFrame(self.root, text="E4980B LCR Meter Parameters")
        frame.grid(row=4, column=0, padx=10, pady=5, sticky="ew")

        ttk.Label(frame, text="Mode:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ttk.Combobox(frame, textvariable=self.lcr_mode, values=["CSRS", "CPRP"], state="readonly").grid(row=0, column=1,
                                                                                                        padx=5, pady=5)

        ttk.Label(frame, text="Freq (Hz):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(frame, textvariable=self.lcr_freq).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Volt (V):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(frame, textvariable=self.lcr_volt).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Settle Time (s):").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        ttk.Entry(frame, textvariable=self.settle_time_lcr).grid(row=3, column=1, padx=5, pady=5)

        ttk.Button(frame, text="Configure LCR", command=self.configure_lcr).grid(row=4, column=1, padx=5, pady=5,
                                                                                 sticky="e")

    def create_run_button(self):
        self.run_btn = ttk.Button(self.root, text="Run Measurement", command=self.run_measurement)
        self.run_btn.grid(row=6, column=0, pady=10)

    def browse_folder(self):
        try:
            path = filedialog.askdirectory()
            if path:
                self.folder_path.set(path)
        except Exception as e:
            messagebox.showerror("Folder Error", f"Could not set folder path:\n{str(e)}")

    def detect_lcr(self):
        """Detect and connect to LCR meters with full identification"""
        try:
            # Close any existing connection
            if self.lcr:
                try:
                    self.lcr.close()
                except:
                    pass
                self.lcr = None

            self.rm = pyvisa.ResourceManager()
            resources = self.rm.list_resources()
            self.available_lcrs = []

            # Detect all available LCR meters
            for r in resources:
                try:
                    dev = self.rm.open_resource(r)
                    dev.timeout = 2000  # Set timeout for ID query
                    idn = dev.query("*IDN?").strip()
                    if "E4980" in idn:
                        # Store full identification info
                        self.available_lcrs.append((r, idn))
                    dev.close()
                except Exception as e:
                    continue

            if not self.available_lcrs:
                self.visa_info.set("No LCR meters found")
                self.run_btn['state'] = 'disabled'
                return False

            # If only one LCR found, connect automatically
            if len(self.available_lcrs) == 1:
                r, idn = self.available_lcrs[0]
                self.lcr = self.rm.open_resource(r)
                self.visa_info.set(f"Connected: {idn}")
                self.run_btn['state'] = 'normal'
                return True
            else:
                # Let user choose from multiple LCRs
                return self.choose_lcr()

        except Exception as e:
            self.visa_info.set(f"Detection Error: {str(e)}")
            self.run_btn['state'] = 'disabled'
            return False

    def choose_lcr(self):
        """Create a dialog to let user select from multiple LCR meters with full info"""
        choice_window = tk.Toplevel(self.root)
        choice_window.title("Select LCR Meter")
        choice_window.geometry("600x300")

        ttk.Label(choice_window,
                  text="Multiple LCR meters detected. Please select one:").pack(pady=10)

        lcr_listbox = tk.Listbox(choice_window, height=len(self.available_lcrs), width=80)
        for i, (r, idn) in enumerate(self.available_lcrs):
            lcr_listbox.insert(i, f"{idn} at {r}")
        lcr_listbox.pack(pady=10, fill=tk.BOTH, expand=True)

        refresh_btn = ttk.Button(choice_window, text="Refresh List",
                                 command=lambda: [self.detect_lcr(), choice_window.destroy()])
        refresh_btn.pack(side=tk.LEFT, padx=10)

        def on_select():
            selected = lcr_listbox.curselection()
            if selected:
                idx = selected[0]
                r, idn = self.available_lcrs[idx]
                try:
                    self.lcr = self.rm.open_resource(r)
                    self.visa_info.set(f"Connected: {idn}")
                    self.run_btn['state'] = 'normal'
                    choice_window.destroy()
                except Exception as e:
                    messagebox.showerror("Connection Error",
                                         f"Could not connect to selected LCR:\n{str(e)}")

        select_btn = ttk.Button(choice_window, text="Select", command=on_select)
        select_btn.pack(side=tk.RIGHT, padx=10)

        # Center the window
        choice_window.transient(self.root)
        choice_window.grab_set()
        self.root.wait_window(choice_window)

        return self.lcr is not None

    def configure_lcr(self):
        if self.lcr is None:
            self.visa_info.set("Error: LCR not connected.")
            return

        try:
            mode = self.lcr_mode.get().upper()
            freq = float(self.lcr_freq.get())
            volt = float(self.lcr_volt.get())

            self.lcr.write("*RST")
            self.lcr.write(f"FUNC:IMP {mode}")
            self.lcr.write(f"FREQ {freq}")
            self.lcr.write(f"VOLT {volt}")
            self.lcr.write("APER LONG")
            self.lcr.write(f":FORM:ELEM {mode}")

            self.visa_info.set(f"LCR configured: {mode}, {freq} Hz, {volt} V")
        except Exception as e:
            self.visa_info.set(f"Configuration failed: {str(e)}")

    def run_measurement(self):
        # Clear previous data
        self.fields = []
        self.caps = []
        self.ress = []
        self.temps = []

        # Get parameters from GUI
        try:
            max_field = int(self.max_field.get())
            step = int(self.magnetic_step.get())
            rate = float(self.magnetic_rate.get())
            temp = float(self.target_temp.get())
            temp_rate = float(self.temp_rate.get())
            stabilize = int(self.stabilize_time.get())
            mode = self.lcr_mode.get()
            freq = float(self.lcr_freq.get())
            volt = float(self.lcr_volt.get())
            settle_time = float(self.settle_time_lcr.get())
            folder = self.folder_path.get()
            host = self.host_ip.get()

            # Validate parameters
            if step <= 0 or max_field <= 0 or max_field > 90000:
                raise ValueError("Field parameters must be positive and < 90kOe")
            if step > max_field:
                raise ValueError("Step size cannot be larger than max field")

        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid parameter value:\n{str(e)}")
            return
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")
            return

        # Initialize plot
        plt.ion()
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
        ax1.set_ylabel("Capacitance (F)")
        ax2.set_ylabel("Resistance (Ohm)")
        ax2.set_xlabel("Magnetic Field (Oe)")
        ax1.grid(True)
        ax2.grid(True)
        line1, = ax1.plot([], [], 'b.-', label='Cs')
        line2, = ax2.plot([], [], 'r.-', label='Rs')
        plt.tight_layout()
        plt.show(block=False)

        try:
            with mpv.Client(host=host) as client:
                try:
                    # Write log file header
                    with open(logfile, 'w') as lf:
                        lf.write(f"Measurement Log - {self._timestamp}\n")
                        lf.write(f"Temperature: {temp} K\n")
                        lf.write(f"Max Field: {max_field} Oe\n")
                        lf.write(f"Field Step: {step} Oe\n")
                        lf.write(f"Field Rate: {rate} Oe/s\n\n")

                    print("Connected to MultiVu.")

                    # --- Field Sweep Path Calculation ---
                    current_field, _ = client.get_field()
                    current_field = round(current_field)
                    print(f"Current PPMS field: {current_field} Oe")

                    all_field_points = list(range(-max_field, max_field + step, step))
                    nearest_field = min(all_field_points, key=lambda x: abs(x - current_field))

                    if abs(max_field - nearest_field) < abs(-max_field - nearest_field):
                        first_leg = list(range(nearest_field, max_field + step, step))
                        second_leg = list(range(max_field, -max_field - step, -step))
                    else:
                        first_leg = list(range(nearest_field, -max_field - step, -step))
                        second_leg = list(range(-max_field, max_field + step, step))

                    field_list = first_leg + second_leg + second_leg[::-1]

                    print(f"Field sweep path:")
                    print(f"Start at: {field_list[0]} Oe")
                    print(f"Forward to: {first_leg[-1]} Oe")
                    print(f"Reverse to: {second_leg[-1]} Oe")
                    print(f"Return to: {field_list[-1]} Oe")

                    # Verify LCR is connected
                    if self.lcr is None:
                        messagebox.showerror("Error", "LCR meter not connected!")
                        return

                    # Configure LCR
                    try:
                        self.lcr.write("*RST")
                        self.lcr.write(f"FUNC:IMP {mode}")
                        self.lcr.write(f"FREQ {freq}")
                        self.lcr.write(f"VOLT {volt}")
                        self.lcr.write("APER LONG")
                        self.lcr.write(f":FORM:ELEM {mode}")
                    except Exception as e:
                        messagebox.showerror("LCR Error", f"Failed to configure LCR:\n{str(e)}")
                        return

                    # --- Temperature Set ---
                    # Get temperature parameters based on mode
                    temp_mode = self.temp_mode.get()

                    if temp_mode == "single":
                        temp_points = [float(self.target_temp.get())]
                    elif temp_mode == "list":
                        temp_points = [float(t.strip()) for t in self.temp_list.get().split(",")]
                    elif temp_mode == "sweep":
                        start = float(self.temp_start.get())
                        end = float(self.temp_end.get())
                        step = float(self.temp_step.get())
                        if start < end:
                            temp_points = list(np.arange(start, end + step / 2, step))
                        else:
                            temp_points = list(np.arange(start, end - step / 2, -step))

                    for temp in temp_points:
                        # Set temperature
                        appr = client.temperature.approach_mode.fast_settle
                        print(f"\nSetting temperature to {temp} K...")
                        client.set_temperature(temp, temp_rate, appr)

                        client.wait_for(stabilize, 0, client.temperature.waitfor)
                        t_meas, _ = client.get_temperature()
                        print(f"Temperature stable at {t_meas:.2f} K")

                        # Create session folder
                        try:
                            # Use the already generated timestamp and material from the class
                            material = self.material.get() or "material"

                            session_folder = os.path.join(folder,
                                                          f"{material}_{max_field}Oe_{temp}K_{mode}_{freq}Hz_{volt}V_{self._timestamp}")
                            os.makedirs(session_folder, exist_ok=True)

                            # Set up file paths using the consistent naming pattern
                            datafile = os.path.join(session_folder, self.data_file.get())
                            plotfile = os.path.join(session_folder, self.plot_file.get())
                            logfile = os.path.join(session_folder, f"{material}_log_{self._timestamp}.txt")

                            # Save a copy of the script for reference with consistent naming
                            script_copy_path = os.path.join(session_folder, f"{material}_script_{self._timestamp}.py")
                            shutil.copy2(__file__, script_copy_path)

                        except Exception as e:
                            messagebox.showerror("Folder Error", f"Could not create session folder:\n{str(e)}")
                            return

                        # --- Begin Sweep ---
                        with open(datafile, "w", newline="") as f, open(logfile, 'a') as lf:
                            writer = csv.writer(f, delimiter="\t")
                            writer.writerow(["Temperature (K)", "Field (Oe)", "Capacitance (F)", "Resistance (Ohm)"])
                            lf.write("\nStarting measurements...\n")

                            for field in field_list:
                                try:
                                    print(f"Setting field to {field} Oe...")
                                    lf.write(f"Setting field to {field} Oe... ")
                                    client.set_field(field, rate, client.field.approach_mode.linear)
                                    client.wait_for(0, 0, client.field.waitfor)
                                    time.sleep(0.1)
                                    lf.write("Done\n")

                                    # Take measurement
                                    self.lcr.write("INIT")
                                    time.sleep(settle_time)
                                    result = self.lcr.query("FETC?")
                                    try:
                                        Cs, Rs = [float(x) for x in result.strip().split(',')[:2]]
                                    except Exception as e:
                                        print(f"Error reading LCR data: {str(e)}")
                                        lf.write(f"Measurement error: {str(e)}\n")
                                        continue

                                    print(f"B = {field} Oe | Cs = {Cs:.3e} F | Rs = {Rs:.2f} Ω")
                                    lf.write(f"Measurement: Cs={Cs:.3e} F, Rs={Rs:.2f} Ω\n")

                                    # Store data
                                    self.fields.append(field)
                                    self.caps.append(Cs)
                                    self.ress.append(Rs)
                                    self.temps.append(t_meas)
                                    writer.writerow([t_meas, field, Cs, Rs])
                                    f.flush()

                                    # Update plot
                                    line1.set_data(self.fields, self.caps)
                                    line2.set_data(self.fields, self.ress)
                                    ax1.relim()
                                    ax1.autoscale_view()
                                    ax2.relim()
                                    ax2.autoscale_view()
                                    fig.canvas.draw()
                                    fig.canvas.flush_events()

                                except KeyboardInterrupt:
                                    print("\nMeasurement interrupted by user")
                                    lf.write("\nMeasurement interrupted by user\n")
                                    raise
                                except Exception as e:
                                    print(f"Error during measurement: {str(e)}")
                                    lf.write(f"Error: {str(e)}\n")
                                    continue

                            try:
                                plt.savefig(plotfile)
                                print(f"Data saved to: {datafile}")
                                print(f"Plot saved to: {plotfile}")
                                print(f"Log saved to: {logfile}")
                                with open(logfile, 'a') as lf:
                                    lf.write(f"\nData saved to: {datafile}\n")
                                    lf.write(f"Plot saved to: {plotfile}\n")
                                    lf.write(f"Measurement completed at {datetime.now()}\n")
                            except Exception as e:
                                print(f"Could not save plot: {str(e)}")
                                with open(logfile, 'a') as lf:
                                    lf.write(f"Plot save failed: {str(e)}\n")

                            except KeyboardInterrupt:
                                print("\nMeasurement interrupted by user")
                                lf.write("\nMeasurement interrupted by user\n")
                                raise
                            except Exception as e:
                                print(f"Error during measurement: {str(e)}")
                                lf.write(f"Error: {str(e)}\n")
                                continue
                    # temp_rate = float(self.temp_rate.get())
                    # stabilize = int(self.stabilize_time.get())
                    # appr = client.temperature.approach_mode.fast_settle
                    # print(f"\nSetting temperature to {temp} K...")
                    # client.set_temperature(temp, temp_rate, appr)
                    #
                    # client.wait_for(stabilize, 0, client.temperature.waitfor)
                    # t_meas, _ = client.get_temperature()
                    # print(f"Temperature stable at {t_meas:.2f} K")

                except KeyboardInterrupt:
                    print("\nMeasurement interrupted by user")
                    with open(logfile, 'a') as lf:
                        lf.write("\nMeasurement interrupted by user\n")
                except Exception as e:
                    print(f"\nMeasurement error: {str(e)}")
                    with open(logfile, 'a') as lf:
                        lf.write(f"\nMeasurement error: {str(e)}\n")
                    messagebox.showerror("Error", f"Measurement failed:\n{str(e)}")

                finally:
                    print("Closing instruments...")
                    with open(logfile, 'a') as lf:
                        lf.write("\nStarting instrument cleanup...\n")

                    # Ask user if they want to reset instruments with both options shown at once
                    reset_choices = messagebox.askyesnocancel(
                        "Reset Instruments",
                        "Do you want to reset all instruments?\n\n"
                        "- Return field to 0 Oe\n"
                        "- Return temperature to 300 K\n\n"
                        "Click 'Yes' to reset both, 'No' to reset nothing,\n"
                        "or 'Cancel' to select individually",
                        default=messagebox.YES  # Default to Yes
                    )

                    if reset_choices is not None:  # User didn't click Cancel
                        if reset_choices:  # User clicked Yes - reset both
                            reset_field = True
                            reset_temp = True
                        else:  # User clicked No - reset nothing
                            reset_field = False
                            reset_temp = False
                    else:  # User clicked Cancel - ask individually
                        reset_field = messagebox.askyesno(
                            "Reset Field",
                            "Return field to 0 Oe?",
                            default=messagebox.YES
                        )
                        reset_temp = messagebox.askyesno(
                            "Reset Temperature",
                            "Return temperature to 300 K?",
                            default=messagebox.YES
                        )

                    # Process field reset if requested
                    if reset_field:
                        try:
                            client.set_field(0, rate, client.field.approach_mode.linear)
                            client.wait_for(0, 0, client.field.waitfor)
                            print("Field returned to 0 Oe.")
                            with open(logfile, 'a') as lf:
                                lf.write("Field returned to 0 Oe\n")
                        except Exception as e:
                            print(f"Could not return field to 0: {str(e)}")
                            with open(logfile, 'a') as lf:
                                lf.write(f"Field reset failed: {str(e)}\n")

                    # Process temperature reset if requested
                    if reset_temp:
                        try:
                            client.set_temperature(300, temp_rate, client.temperature.approach_mode.fast_settle)
                            print("Temperature returning to 300 K.")
                            with open(logfile, 'a') as lf:
                                lf.write("Temperature returning to 300 K\n")
                        except Exception as e:
                            print(f"Could not return temperature: {str(e)}")
                            with open(logfile, 'a') as lf:
                                lf.write(f"Temperature reset failed: {str(e)}\n")

                    plt.ioff()
                    plt.close()

        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to PPMS:\n{str(e)}")
            with open(logfile, 'a') as lf:
                lf.write(f"PPMS connection failed: {str(e)}\n")

if __name__ == '__main__':
    try:
        root = tk.Tk()
        app = MeasurementGUI(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Fatal Error", f"Application crashed:\n{str(e)}")
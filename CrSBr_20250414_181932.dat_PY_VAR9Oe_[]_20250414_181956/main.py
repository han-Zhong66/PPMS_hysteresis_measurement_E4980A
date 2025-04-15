# import tkinter as tk
# from tkinter import ttk, filedialog, messagebox
# import pyvisa
# import time
# import csv
# import numpy as np
# import matplotlib.pyplot as plt
# import matplotlib
# import MultiPyVu as mpv
# import os
# from datetime import datetime
#
# # Prepare for plotting
# matplotlib.use("TkAgg")
# timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#
#
# # Define GUI class
# class MeasurementGUI:
#     def __init__(self, root):
#         self.root = root
#         self.root.title("PPMS + E4980B Measurement Config")
#
#         self.lcr = None
#         self.rm = None  # Added VISA resource manager instance variable
#
#         # Initialize data storage lists
#         self.fields = []
#         self.caps = []
#         self.ress = []
#         self.temps = []
#
#         self.lcr_mode = tk.StringVar(value="CSRS")
#         self.lcr_freq = tk.StringVar(value="20")
#         self.lcr_volt = tk.StringVar(value="0.3")
#         self.settle_time_magnetic = tk.StringVar(value="1.0")
#         self.settle_time_lcr = tk.StringVar(value="0.5")
#
#         # Create sections in proper order
#         self.create_host_output_frame()
#         self.create_magnetic_field_frame()
#         self.create_temperature_frame()
#         self.create_lcr_frame()
#         self.create_visa_frame()
#         self.create_run_button()
#
#     def create_magnetic_field_frame(self):
#         frame = ttk.LabelFrame(self.root, text="Magnetic Field Parameters")
#         frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
#
#         self.max_field = tk.StringVar(value="5000")
#         self.magnetic_step = tk.StringVar(value="100")
#         self.magnetic_rate = tk.StringVar(value="100")
#
#         ttk.Label(frame, text="Max Field (Oe):").grid(row=0, column=0)
#         ttk.Entry(frame, textvariable=self.max_field).grid(row=0, column=1)
#         ttk.Label(frame, text="Step (Oe):").grid(row=1, column=0)
#         ttk.Entry(frame, textvariable=self.magnetic_step).grid(row=1, column=1)
#         ttk.Label(frame, text="Rate (Oe/s):").grid(row=2, column=0)
#         ttk.Entry(frame, textvariable=self.magnetic_rate).grid(row=2, column=1)
#
#     def create_temperature_frame(self):
#         frame = ttk.LabelFrame(self.root, text="Temperature Parameters")
#         frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
#
#         self.target_temp = tk.StringVar(value="100")
#         self.temp_rate = tk.StringVar(value="20")
#         self.stabilize_time = tk.StringVar(value="10")
#
#         ttk.Label(frame, text="Target Temp (K):").grid(row=0, column=0)
#         ttk.Entry(frame, textvariable=self.target_temp).grid(row=0, column=1)
#         ttk.Label(frame, text="Rate (K/min):").grid(row=1, column=0)
#         ttk.Entry(frame, textvariable=self.temp_rate).grid(row=1, column=1)
#         ttk.Label(frame, text="Stabilize (s):").grid(row=2, column=0)
#         ttk.Entry(frame, textvariable=self.stabilize_time).grid(row=2, column=1)
#
#     def create_host_output_frame(self):
#         frame = ttk.LabelFrame(self.root, text="Host and Output")
#         frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
#
#         self.host_ip = tk.StringVar(value="10.227.234.170")
#         self.folder_path = tk.StringVar(value=os.getcwd())  # Use current working directory
#         self.data_file = tk.StringVar(value=f"field_sweep_csrs_{timestamp}.dat")
#         self.plot_file = tk.StringVar(value=f"field_sweep_csrs_plot_{timestamp}.png")
#
#         ttk.Label(frame, text="QD Server IP:").grid(row=0, column=0)
#         ttk.Entry(frame, textvariable=self.host_ip).grid(row=0, column=1)
#         ttk.Label(frame, text="Folder:").grid(row=1, column=0)
#         ttk.Entry(frame, textvariable=self.folder_path).grid(row=1, column=1)
#         ttk.Button(frame, text="Browse", command=self.browse_folder).grid(row=1, column=2)
#         ttk.Label(frame, text="Data Filename:").grid(row=2, column=0)
#         ttk.Entry(frame, textvariable=self.data_file).grid(row=2, column=1)
#         ttk.Label(frame, text="Plot Filename:").grid(row=3, column=0)
#         ttk.Entry(frame, textvariable=self.plot_file).grid(row=3, column=1)
#
#     def create_visa_frame(self):
#         frame = ttk.LabelFrame(self.root, text="LCR VISA Resource")
#         frame.grid(row=5, column=0, padx=10, pady=5, sticky="ew")
#         self.visa_info = tk.StringVar(value="No LCR connected.")
#
#         ttk.Label(frame, textvariable=self.visa_info).pack(anchor="w", padx=5, pady=5)
#         ttk.Button(frame, text="Detect LCR", command=self.detect_lcr).pack(anchor="e", padx=5, pady=5)
#
#     def create_lcr_frame(self):
#         frame = ttk.LabelFrame(self.root, text="E4980B LCR Meter Parameters")
#         frame.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
#
#         ttk.Label(frame, text="Mode:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
#         ttk.Combobox(frame, textvariable=self.lcr_mode, values=["CSRS", "CPRP"], state="readonly").grid(row=0, column=1,
#                                                                                                         padx=5, pady=5)
#
#         ttk.Label(frame, text="Freq (Hz):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
#         ttk.Entry(frame, textvariable=self.lcr_freq).grid(row=1, column=1, padx=5, pady=5)
#
#         ttk.Label(frame, text="Volt (V):").grid(row=2, column=0, padx=5, pady=5, sticky="e")
#         ttk.Entry(frame, textvariable=self.lcr_volt).grid(row=2, column=1, padx=5, pady=5)
#
#         ttk.Label(frame, text="Settle Time (s):").grid(row=3, column=0, padx=5, pady=5, sticky="e")
#         ttk.Entry(frame, textvariable=self.settle_time_lcr).grid(row=3, column=1, padx=5, pady=5)
#
#         ttk.Button(frame, text="Configure LCR", command=self.configure_lcr).grid(row=4, column=1, padx=5, pady=5,
#                                                                                  sticky="e")
#
#     def create_run_button(self):
#         self.run_btn = ttk.Button(self.root, text="Run Measurement", command=self.run_measurement)
#         self.run_btn.grid(row=6, column=0, pady=10)
#
#     def browse_folder(self):
#         path = filedialog.askdirectory()
#         if path:
#             self.folder_path.set(path)
#
#     def detect_lcr(self):
#         try:
#             self.rm = pyvisa.ResourceManager()
#             resources = self.rm.list_resources()
#             for r in resources:
#                 try:
#                     dev = self.rm.open_resource(r)
#                     idn = dev.query("*IDN?")
#                     if "E4980" in idn:
#                         self.lcr = dev
#                         self.visa_info.set(f"Found: {idn.strip()} at {r}")
#                         return
#                 except Exception as e:
#                     continue
#             self.visa_info.set("No E4980 LCR Meter found.")
#         except Exception as e:
#             self.visa_info.set(f"Error: {str(e)}")
#
#     def configure_lcr(self):
#         if self.lcr is None:
#             self.visa_info.set("Error: LCR not connected.")
#             return
#
#         try:
#             mode = self.lcr_mode.get().upper()
#             freq = float(self.lcr_freq.get())
#             volt = float(self.lcr_volt.get())
#
#             self.lcr.write("*RST")
#             self.lcr.write(f"FUNC:IMP {mode}")
#             self.lcr.write(f"FREQ {freq}")
#             self.lcr.write(f"VOLT {volt}")
#             self.lcr.write("APER LONG")
#             self.lcr.write(f":FORM:ELEM {mode}")
#
#             self.visa_info.set(f"LCR configured: {mode}, {freq} Hz, {volt} V")
#         except Exception as e:
#             self.visa_info.set(f"Configuration failed: {e}")
#
#     def run_measurement(self):
#         # Clear previous data
#         self.fields = []
#         self.caps = []
#         self.ress = []
#         self.temps = []
#
#         # Get parameters from GUI
#         try:
#             max_field = int(self.max_field.get())
#             step = int(self.magnetic_step.get())
#             rate = float(self.magnetic_rate.get())
#             temp = float(self.target_temp.get())
#             temp_rate = float(self.temp_rate.get())
#             stabilize = int(self.stabilize_time.get())
#             mode = self.lcr_mode.get()
#             freq = float(self.lcr_freq.get())
#             volt = float(self.lcr_volt.get())
#             settle_time = float(self.settle_time_lcr.get())
#             folder = self.folder_path.get()
#             datafile = os.path.join(folder, self.data_file.get())
#             plotfile = os.path.join(folder, self.plot_file.get())
#             host = self.host_ip.get()
#         except ValueError as e:
#             messagebox.showerror("Input Error", f"Invalid parameter value: {e}")
#             return
#
#         # Create output directory if it doesn't exist
#         os.makedirs(folder, exist_ok=True)
#
#         # Initialize plot
#         plt.ion()
#         fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
#         ax1.set_ylabel("Capacitance (F)")
#         ax2.set_ylabel("Resistance (Ohm)")
#         ax2.set_xlabel("Magnetic Field (Oe)")
#         ax1.grid(True)
#         ax2.grid(True)
#         line1, = ax1.plot([], [], 'b.-', label='Cs')
#         line2, = ax2.plot([], [], 'r.-', label='Rs')
#         plt.tight_layout()
#         plt.show(block=False)
#
#         with mpv.Client(host=host) as client:
#
#             try:
#                 print("Connected to MultiVu.")
#
#                 # --- Field Sweep Path Calculation ---
#                 current_field, _ = client.get_field()
#                 current_field = round(current_field)
#                 print(f"📡 Current PPMS field: {current_field} Oe")
#
#                 all_field_points = list(range(-max_field, max_field + step, step))
#                 nearest_field = min(all_field_points, key=lambda x: abs(x - current_field))
#
#                 if abs(max_field - nearest_field) < abs(-max_field - nearest_field):
#                     first_leg = list(range(nearest_field, max_field + step, step))
#                     second_leg = list(range(max_field, -max_field - step, -step))
#                 else:
#                     first_leg = list(range(nearest_field, -max_field - step, -step))
#                     second_leg = list(range(-max_field, max_field + step, step))
#
#                 field_list = first_leg + second_leg + second_leg[::-1]
#
#                 print(f"🔁 Field sweep path:")
#                 print(f"    Start at      : {field_list[0]} Oe")
#                 print(f"    Forward to    : {first_leg[-1]} Oe")
#                 print(f"    Reverse to    : {second_leg[-1]} Oe")
#                 print(f"    Return to     : {field_list[-1]} Oe")
#
#                 # --- Temperature Set ---
#                 appr = client.temperature.approach_mode.fast_settle
#                 print(f"\n🌡️ Setting temperature to {temp} K...")
#                 client.set_temperature(temp, temp_rate, appr)
#
#                 client.wait_for(stabilize, 0, client.temperature.waitfor)
#                 t_meas, _ = client.get_temperature()
#                 print(f"✅ Temperature stable at {t_meas:.2f} K")
#
#                 # Verify LCR is connected
#                 if self.lcr is None:
#                     messagebox.showerror("Error", "LCR meter not connected!")
#                     return
#
#                 # Configure LCR
#                 try:
#                     self.lcr.write("*RST")
#                     self.lcr.write(f"FUNC:IMP {mode}")
#                     self.lcr.write(f"FREQ {freq}")
#                     self.lcr.write(f"VOLT {volt}")
#                     self.lcr.write("APER LONG")
#                     self.lcr.write(f":FORM:ELEM {mode}")
#                 except Exception as e:
#                     messagebox.showerror("LCR Error", f"Failed to configure LCR: {e}")
#                     return
#
#                 # --- Begin Sweep ---
#                 with open(datafile, "w", newline="") as f:
#                     writer = csv.writer(f, delimiter="\t")
#                     writer.writerow(["Temperature (K)", "Field (Oe)", "Capacitance (F)", "Resistance (Ohm)"])
#
#                     for field in field_list:
#                         print(f"➡️ Setting field to {field} Oe...")
#                         client.set_field(field, rate, client.field.approach_mode.linear)
#                         client.wait_for(0, 0, client.field.waitfor)
#                         time.sleep(0.1)  # Small delay after field stabilization
#
#                         # Take measurement
#                         self.lcr.write("INIT")
#                         time.sleep(settle_time)  # Use the settle time from GUI
#                         result = self.lcr.query("FETC?")
#                         try:
#                             Cs, Rs = [float(x) for x in result.strip().split(',')[:2]]
#                         except Exception as e:
#                             print(f"⚠️ Error reading LCR data: {e}")
#                             continue
#
#                         print(f"📏 B = {field} Oe | Cs = {Cs:.3e} F | Rs = {Rs:.2f} Ω")
#
#                         # Store data
#                         self.fields.append(field)
#                         self.caps.append(Cs)
#                         self.ress.append(Rs)
#                         self.temps.append(t_meas)
#                         writer.writerow([t_meas, field, Cs, Rs])
#                         f.flush()  # Ensure data is written to file immediately
#
#                         # Update plot
#                         line1.set_data(self.fields, self.caps)
#                         line2.set_data(self.fields, self.ress)
#                         ax1.relim()
#                         ax1.autoscale_view()
#                         ax2.relim()
#                         ax2.autoscale_view()
#                         fig.canvas.draw()
#                         fig.canvas.flush_events()
#
#             except KeyboardInterrupt:
#                 print("\n⛔ Interrupted by user. Saving partial data and cleaning up...")
#             except Exception as e:
#                 messagebox.showerror("Error", f"Measurement failed: {e}")
#             finally:
#                 print("🔌 Closing instruments...")
#
#                 # Ask user if they want to reset instruments
#                 reset_field = messagebox.askyesno("Reset Field", "Do you want to return the field to 0 Oe?")
#                 if reset_field:
#                     try:
#                         client.set_field(0, rate, client.field.approach_mode.linear)
#                         client.wait_for(0, 0, client.field.waitfor)
#                         print("🧹 Field returned to 0 Oe.")
#                     except Exception as e:
#                         print(f"⚠️ Could not return field to 0: {e}")
#
#                 reset_temp = messagebox.askyesno("Reset Temperature", "Do you want to return the temperature to 300 K?")
#                 if reset_temp:
#                     try:
#                         client.set_temperature(300, temp_rate, client.temperature.approach_mode.fast_settle)
#                         client.wait_for(stabilize, 0, client.temperature.waitfor)
#                         print("🧹 Temperature returned to 300 K.")
#                     except Exception as e:
#                         print(f"⚠️ Could not return temperature to 300 K: {e}")
#
#                 try:
#                     plt.savefig(plotfile)
#                     print(f"\n📁 Data saved to: {datafile}")
#                     print(f"🖼️ Plot saved to: {plotfile}")
#                 except Exception as e:
#                     print(f"⚠️ Plot save failed: {e}")
#
#                 plt.ioff()
#                 plt.close()
#
#
# if __name__ == '__main__':
#     root = tk.Tk()
#     app = MeasurementGUI(root)
#     root.mainloop()

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

# Prepare for plotting
matplotlib.use("TkAgg")


class MeasurementGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PPMS + E4980B Measurement Config")

        self.lcr = None
        self.rm = None
        self.client = None
        self.available_lcrs = []  # Store all detected LCR meters

        # Initialize data storage lists
        self.fields = []
        self.caps = []
        self.ress = []
        self.temps = []

        self.lcr_mode = tk.StringVar(value="CSRS")
        self.lcr_freq = tk.StringVar(value="20")
        self.lcr_volt = tk.StringVar(value="0.3")
        self.settle_time_magnetic = tk.StringVar(value="1.0")
        self.settle_time_lcr = tk.StringVar(value="0.5")

        # Create GUI sections
        self.create_host_output_frame()
        self.create_magnetic_field_frame()
        self.create_temperature_frame()
        self.create_lcr_frame()
        self.create_visa_frame()
        self.create_run_button()

        # Auto-detect LCR meters on startup
        self.detect_lcr()

    def create_magnetic_field_frame(self):
        frame = ttk.LabelFrame(self.root, text="Magnetic Field Parameters")
        frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        self.max_field = tk.StringVar(value="5000")
        self.magnetic_step = tk.StringVar(value="100")
        self.magnetic_rate = tk.StringVar(value="100")

        ttk.Label(frame, text="Max Field (Oe):").grid(row=0, column=0)
        ttk.Entry(frame, textvariable=self.max_field).grid(row=0, column=1)
        ttk.Label(frame, text="Step (Oe):").grid(row=1, column=0)
        ttk.Entry(frame, textvariable=self.magnetic_step).grid(row=1, column=1)
        ttk.Label(frame, text="Rate (Oe/s):").grid(row=2, column=0)
        ttk.Entry(frame, textvariable=self.magnetic_rate).grid(row=2, column=1)

    def create_temperature_frame(self):
        frame = ttk.LabelFrame(self.root, text="Temperature Parameters")
        frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.target_temp = tk.StringVar(value="100")
        self.temp_rate = tk.StringVar(value="20")
        self.stabilize_time = tk.StringVar(value="10")

        ttk.Label(frame, text="Target Temp (K):").grid(row=0, column=0)
        ttk.Entry(frame, textvariable=self.target_temp).grid(row=0, column=1)
        ttk.Label(frame, text="Rate (K/min):").grid(row=1, column=0)
        ttk.Entry(frame, textvariable=self.temp_rate).grid(row=1, column=1)
        ttk.Label(frame, text="Stabilize (s):").grid(row=2, column=0)
        ttk.Entry(frame, textvariable=self.stabilize_time).grid(row=2, column=1)

    def create_host_output_frame(self):
        frame = ttk.LabelFrame(self.root, text="Host and Output")
        frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        self.host_ip = tk.StringVar(value="10.227.234.170")
        self.folder_path = tk.StringVar(value=os.getcwd())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.data_file = tk.StringVar(value=f"measurement_{timestamp}.dat")
        self.plot_file = tk.StringVar(value=f"measurement_{timestamp}.png")

        ttk.Label(frame, text="QD Server IP:").grid(row=0, column=0)
        ttk.Entry(frame, textvariable=self.host_ip).grid(row=0, column=1)
        ttk.Label(frame, text="Folder:").grid(row=1, column=0)
        ttk.Entry(frame, textvariable=self.folder_path).grid(row=1, column=1)
        ttk.Button(frame, text="Browse", command=self.browse_folder).grid(row=1, column=2)
        ttk.Label(frame, text="Data Filename:").grid(row=2, column=0)
        ttk.Entry(frame, textvariable=self.data_file).grid(row=2, column=1)
        ttk.Label(frame, text="Plot Filename:").grid(row=3, column=0)
        ttk.Entry(frame, textvariable=self.plot_file).grid(row=3, column=1)

    def create_visa_frame(self):
        frame = ttk.LabelFrame(self.root, text="LCR VISA Resource")
        frame.grid(row=5, column=0, padx=10, pady=5, sticky="ew")
        self.visa_info = tk.StringVar(value="No LCR connected.")

        ttk.Label(frame, textvariable=self.visa_info).pack(anchor="w", padx=5, pady=5)
        ttk.Button(frame, text="Detect LCR", command=self.detect_lcr).pack(anchor="e", padx=5, pady=5)

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
                return False

            # If only one LCR found, connect automatically
            if len(self.available_lcrs) == 1:
                r, idn = self.available_lcrs[0]
                self.lcr = self.rm.open_resource(r)
                self.visa_info.set(f"Connected: {idn}")
                return True
            else:
                # Let user choose from multiple LCRs
                return self.choose_lcr()

        except Exception as e:
            self.visa_info.set(f"Detection Error: {str(e)}")
            return False

    def choose_lcr(self):
        """Create a dialog to let user select from multiple LCR meters with full info"""
        choice_window = tk.Toplevel(self.root)
        choice_window.title("Select LCR Meter")
        choice_window.geometry("600x400")

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
    # def detect_lcr(self):
    #     try:
    #         self.rm = pyvisa.ResourceManager()
    #         resources = self.rm.list_resources()
    #         for r in resources:
    #             try:
    #                 dev = self.rm.open_resource(r)
    #                 idn = dev.query("*IDN?")
    #                 if "E4980" in idn:
    #                     self.lcr = dev
    #                     self.visa_info.set(f"Found: {idn.strip()} at {r}")
    #                     return
    #             except Exception as e:
    #                 continue
    #         self.visa_info.set("No E4980 LCR Meter found.")
    #     except Exception as e:
    #         self.visa_info.set(f"Error: {str(e)}")
    def create_session_folder(self):
        """Create folder for this measurement session with proper naming"""
        try:
            base_folder = self.folder_path.get()
            if not os.path.exists(base_folder):
                os.makedirs(base_folder)

            # Get parameters for folder name
            temp = self.target_temp.get()
            max_field = self.max_field.get()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Create session folder with descriptive name
            session_folder = os.path.join(
                base_folder,
                f"PPMS_{temp}K_{max_field}Oe_{timestamp}"
            )
            os.makedirs(session_folder)

            # Save a copy of this script for reference
            script_path = os.path.abspath(__file__)
            shutil.copy2(script_path, session_folder)

            return session_folder

        except Exception as e:
            messagebox.showerror("Folder Error",
                                 f"Could not create session folder:\n{str(e)}")
            return None

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
            datafile = os.path.join(folder, self.data_file.get())
            plotfile = os.path.join(folder, self.plot_file.get())
            host = self.host_ip.get()

            # Validate parameters
            if step <= 0 or max_field <= 0 or max_field > 90000:
                raise ValueError("Field parameters must be positive")
            if step > max_field:
                raise ValueError("Step size cannot be larger than max field")

        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid parameter value:\n{str(e)}")
            return
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error:\n{str(e)}")
            return

        # Create session folder with timestamp
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_folder = os.path.join(folder, f"{self.data_file.get()}_{self.max_field}Oe_{self.temps}_{timestamp}")
            os.makedirs(session_folder, exist_ok=True)

            # Update file paths to use session folder
            datafile = os.path.join(session_folder, f"data_{self.data_file.get()}_{timestamp}.dat")
            plotfile = os.path.join(session_folder, f"data_{self.plot_file.get()}_{timestamp}.png")
            logfile = os.path.join(session_folder, f"log_{timestamp}.txt")

            # Save a copy of the script for reference
            shutil.copy2(__file__, session_folder)

        except Exception as e:
            messagebox.showerror("Folder Error", f"Could not create session folder:\n{str(e)}")
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
                        lf.write(f"Measurement Log - {timestamp}\n")
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

                    # --- Temperature Set ---
                    appr = client.temperature.approach_mode.fast_settle
                    print(f"\nSetting temperature to {temp} K...")
                    client.set_temperature(temp, temp_rate, appr)

                    client.wait_for(stabilize, 0, client.temperature.waitfor)
                    t_meas, _ = client.get_temperature()
                    print(f"Temperature stable at {t_meas:.2f} K")

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

                    # Ask user if they want to reset instruments
                    reset_field = messagebox.askyesno("Reset Field", "Return field to 0 Oe?")
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

                    reset_temp = messagebox.askyesno("Reset Temperature", "Return temperature to 300 K?")
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


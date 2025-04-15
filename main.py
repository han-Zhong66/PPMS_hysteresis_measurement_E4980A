import time
import csv
import pyvisa
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import MultiPyVu as mpv
import os
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
matplotlib.use("TkAgg")

# ------------------------------
# Setup LCR Meter (E4980B)
# ------------------------------
rm = pyvisa.ResourceManager()
resources = rm.list_resources()
lcr = None
for r in resources:
    try:
        dev = rm.open_resource(r)
        idn = dev.query("*IDN?")
        if "E4980" in idn:
            lcr = dev
            print(f"Connected to LCR Meter: {idn.strip()}")
            break
    except:
        continue

if lcr is None:
    raise RuntimeError("E4980B not found.")
lcr.write("*RST")

# ------------------------------
# Plot Setup
# ------------------------------
plt.ion()
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
ax1.set_ylabel("Capacitance (F)")
ax2.set_ylabel("Resistance (Ohm)")
ax2.set_xlabel("Magnetic Field (Oe)")
ax1.grid(True)
ax2.grid(True)
line1, = ax1.plot([], [], 'b.-', label='Cs')
line2, = ax2.plot([], [], 'r.-', label='Rs')
fields, caps, ress, temps = [], [], [], []

maxField = 5000
magnetic_rate = 100.0
magnetic_step = 100

target_temp = 300
temp_rate = 20

stabilization_time_sec = 10  # temperature stabilization time
settle_time_magnetic = 0.3
settle_time_lcr = 0.3

# save path to file
# base_dir = os.path.expanduser("~/Desktop")  # or any path you want
# folder_name = os.path.join(base_dir, f"{target_temp}K_hysteresis_field_sweep_{maxField}Oe_{timestamp}")
# os.makedirs(folder_name, exist_ok=True)
folder_name = f"{target_temp}K_hysteresis_field_sweep_{maxField}Oe_{timestamp}"
os.makedirs(folder_name, exist_ok=True)
data_filename = os.path.join(folder_name, "FGaT_C_csrs_0Vg.dat")
plot_filename = os.path.join(folder_name, "FGaT_C_csrs_plot_0Vg.png")

with mpv.Client(host="10.227.234.170") as client:
    try:

        print("Connected to MultiVu.")

        # --- Sweep Parameters ---

        field_forward = list(range(-maxField, maxField + magnetic_step, magnetic_step))
        field_reverse = list(range(maxField, -maxField - magnetic_step, -magnetic_step))
        full_field_list = field_forward + field_reverse

        current_field, _ = client.get_field()
        current_field = round(current_field)
        print(f"📡 Current PPMS field: {current_field} Oe")

        all_field_points = list(range(-maxField, maxField + magnetic_step, magnetic_step))
        nearest_field = min(all_field_points, key=lambda x: abs(x - current_field))
        if abs(maxField - nearest_field) < abs(-maxField - nearest_field):
            first_leg = list(range(nearest_field, maxField + magnetic_step, magnetic_step))
            second_leg = list(range(maxField, -maxField - magnetic_step, -magnetic_step))
        else:
            first_leg = list(range(nearest_field, -maxField - magnetic_step, -magnetic_step))
            second_leg = list(range(-maxField, maxField + magnetic_step, magnetic_step))
        field_list = first_leg + second_leg + second_leg[::-1]
        # print(f"first_leg {first_leg}\n", f"second_leg {second_leg}\n", f"second_leg_reverse {second_leg[::-1]}")
        # print(f"🔁 Field sweep from {field_list[0]} → {first_leg[-1]} Oe → {second_leg[-1]} Oe → {field_list[-1]} Oe")
        print(f"🔁 Field sweep path:")
        print(f"    Start at      : {field_list[0]} Oe")
        print(f"    Forward to    : {first_leg[-1]} Oe")
        print(f"    Reverse to    : {second_leg[-1]} Oe")
        print(f"    Return to     : {field_list[-1]} Oe")

        # --- Temperature Set ---
        appr = client.temperature.approach_mode.fast_settle
        print(f"\n🌡️ Setting temperature to {target_temp} K...")
        client.set_temperature(target_temp, temp_rate, appr)
        client.wait_for(stabilization_time_sec, 0, client.temperature.waitfor)
        t_meas, _ = client.get_temperature()
        print(f"✅ Temperature stable at {t_meas:.2f} K")

        # E4980b lcr parameter
        lcr.write("FUNC:IMP CSRS")
        lcr.write("FREQ 20")
        lcr.write("VOLT 0.1")
        lcr.write("APER LONG")
        lcr.write(":FORM:ELEM CSRS")

        # --- Begin Sweep ---
        with open(data_filename, "w", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(["Temperature (K)", "Field (Oe)", "Capacitance (F)", "Resistance (Ohm)"])
            for field in field_list:
                print(f"➡️ Setting field to {field} Oe...")
                client.set_field(field, magnetic_rate, client.field.approach_mode.linear)
                client.wait_for(0, 0, client.field.waitfor)
                time.sleep(settle_time_magnetic)

                lcr.write("INIT")
                time.sleep(settle_time_lcr)
                result = lcr.query("FETC?")
                Cs, Rs = [float(x) for x in result.strip().split(',')[:2]]

                print(f"📏 B = {field} Oe | Cs = {Cs:.3e} F | Rs = {Rs:.2f} Ω")
                fields.append(field)
                caps.append(Cs)
                ress.append(Rs)
                temps.append(t_meas)
                writer.writerow([t_meas, field, Cs, Rs])

                line1.set_data(fields, caps)
                line2.set_data(fields, ress)
                ax1.relim();
                ax1.autoscale_view()
                ax2.relim();
                ax2.autoscale_view()
                plt.pause(0.01)
    except KeyboardInterrupt:
        print("\n⛔ Interrupted by user. Saving partial data and cleaning up...")

    finally:
        print("🔌 Closing instruments...")
        # Ask user if they want to reset instruments
        root = tk.Tk()
        root.withdraw()  # Hide the root window

        # Ask about resetting field
        reset_field = messagebox.askyesno("Reset Field", "Do you want to return the field to 0 Oe?")
        if reset_field:
            try:
                client.set_field(0, magnetic_rate, client.field.approach_mode.linear)
                client.wait_for(0, 0, client.field.waitfor)
                print("🧹 Field returned to 0 Oe.")
            except:
                print("⚠️ Could not return field to 0.")

        # Ask about resetting temperature
        reset_temp = messagebox.askyesno("Reset Temperature", "Do you want to return the temperature to 300 K?")
        if reset_temp:
            try:
                client.set_temperature(300, temp_rate, client.temperature.approach_mode.fast_settle)
                client.wait_for(stabilization_time_sec, 0, client.temperature.waitfor)
                print("🧹 Temperature returned to 300 K.")
            except:
                print("⚠️ Could not return temperature to 300 K.")
        # try:
        #     client.set_field(0, magnetic_rate, client.field.approach_mode.linear)
        #     client.wait_for(0, 0, client.field.waitfor)
        #     print("🧹 Field returned to 0 Oe.")
        # except:
        #     print("⚠️ Could not return field to 0.")
        # try:
        #     client.set_temperature(target_temp, temp_rate, appr)
        #     client.wait_for(stabilization_time_sec, 0, client.temperature.waitfor)
        #     print("🧹 Temperature returned to 300K.")
        # except:
        #     print("⚠️ Could not return temperature to 300K.")
        # try:
        #     client.close()
        # except:
        #     print("⚠️ Could not close MultiVu client.")
        try:
            lcr.close()
        except:
            print("⚠️ Could not close LCR meter.")
        try:
            rm.close()
        except:
            print("⚠️ Could not close VISA resource manager.")

        plt.ioff()
        plt.tight_layout()
        try:
            plt.savefig(plot_filename)
            print(f"\n📁 Data saved to: {data_filename}")
            print(f"🖼️ Plot saved to: {plot_filename}")
        except Exception as e:
            print(f"⚠️ Plot save failed: {e}")
        plt.show()




# # ------------------------------
# # Measurement Loop
# # ------------------------------
#
# try:
#     client = mpv.Client(host="10.227.234.170")
#     try:
#         print("✅ Connected to MultiVu. Can be interrupted by ctrl + c.")
#         # ------------------------------
#         # Field Sweep Parameters (Hysteresis)
#         # ------------------------------
#
#         # Define full hysteresis loop
#         maxField = 5000
#         magnetic_step = 100
#         field_forward = list(range(-maxField, maxField + magnetic_step, magnetic_step))
#         field_reverse = list(range(maxField, -maxField - magnetic_step, -magnetic_step))
#         # field_list = field_forward + field_reverse
#         full_field_list = field_forward + field_reverse
#
#         # Get current magnetic field from PPMS
#         current_field, _ = client.get_field()
#         current_field = round(current_field)
#         print(f"📡 Current PPMS field: {current_field} Oe")
#
#         # Find the closest field point
#         all_field_points = list(range(-maxField, maxField + magnetic_step, magnetic_step))
#         nearest_field = min(all_field_points, key=lambda x: abs(x - current_field))
#         nearest_field = max(min(nearest_field, maxField), -maxField)
#
#         print(f"🎯 Nearest sweep point: {nearest_field} Oe")
#
#         # Determine direction to nearest boundary
#         if abs(maxField - nearest_field) < abs(-maxField - nearest_field):
#             # Closer to +maxField → go to +maxField first, then reverse
#             first_leg = list(range(nearest_field, maxField + magnetic_step, magnetic_step))
#             second_leg = list(range(maxField, -maxField - magnetic_step, -magnetic_step))
#         else:
#             # Closer to -maxField → go to -maxField first, then reverse
#             first_leg = list(range(nearest_field, -maxField - magnetic_step, -magnetic_step))
#             second_leg = list(range(-maxField, maxField + magnetic_step, magnetic_step))
#
#         field_list = first_leg + second_leg + second_leg[::-1]
#
#         print(f"🔁 Starting hysteresis sweep from {field_list[0]} Oe → {field_list[-1]} Oe")
#
#         magnetic_rate = 100.0
#
#         target_temp = 200
#         temp_rate = 10.0
#
#         settle_time = 0.5  # seconds after field stabilizes
#
#         folder_name = f"{int(target_temp)}K_hysteresis_field_sweep_{int(maxField)}Oe_{timestamp}"
#         os.makedirs(folder_name, exist_ok=True)
#
#         data_filename = os.path.join(folder_name, "field_sweep_csrs_0.3Vg.dat")
#         plot_filename = os.path.join(folder_name, "field_sweep_csrs_plot_0.3Vg.png")
#
#         # Set temperature only once
#         appr = client.temperature.approach_mode.fast_settle
#         print(f"\n🌡️ Setting temperature to {target_temp} K...")
#         client.set_temperature(target_temp, temp_rate, appr)
#         client.wait_for(10, 0, client.temperature.waitfor)
#         t_meas, _ = client.get_temperature()
#         print(f"✅ Temperature stable at {t_meas:.2f} K")
#
#         lcr.write("FUNC:IMP CSRS")
#         lcr.write("FREQ 20")
#         lcr.write("VOLT 0.3")
#         lcr.write("APER LONG")
#         lcr.write(":FORM:ELEM CSRS")
#
#         with open(data_filename, "w", newline="") as f:
#             writer = csv.writer(f, delimiter="\t")
#             writer.writerow(["Temperature (K)", "Field (Oe)", "Capacitance (F)", "Resistance (Ohm)"])
#
#             for field in field_list:
#                 print(f"➡️ Setting field to {field} Oe...")
#                 client.set_field(field, magnetic_rate, client.field.approach_mode.linear)
#                 client.wait_for(0, 0, client.field.waitfor)
#                 time.sleep(settle_time)
#
#                 lcr.write("INIT")
#                 time.sleep(0.5)
#                 result = lcr.query("FETC?")
#                 Cp = [float(x) for x in result.strip().split(',')][0]
#                 Rp = [float(x) for x in result.strip().split(',')][1]
#
#                 print(f"📏 B = {field} Oe | Cs = {Cp:.3e} F | Rs = {Rp:.2f} Ω")
#                 fields.append(field)
#                 caps.append(Cp)
#                 ress.append(Rp)
#                 temps.append(t_meas)
#
#                 writer.writerow([t_meas, field, Cp, Rp])
#
#                 # Live plot
#                 line1.set_data(fields, caps)
#                 line2.set_data(fields, ress)
#                 ax1.relim();
#                 ax1.autoscale_view()
#                 ax2.relim();
#                 ax2.autoscale_view()
#                 plt.pause(0.01)
#
#
#     finally:
#
#         print("🔌 Closing instruments...")
#
#         try:
#             client.close()
#         except:
#             pass
#         try:
#             lcr.close()
#         except:
#             pass
#         try:
#             rm.close()
#         except:
#             pass
#
#         plt.ioff()
#         plt.tight_layout()
#
#         try:
#             plt.savefig(plot_filename)
#             print("\n✅ Hysteresis sweep complete.")
#             print(f"📁 Data saved to: {data_filename}")
#             print(f"🖼️ Plot saved to: {plot_filename}")
#
#         except Exception as e:
#
#             print(f"⚠️ Could not save plot or print final info: {e}")
#         # try:
#         #     print("🧹 Returning field to 0 Oe...")
#         #     client.set_field(0, magnetic_rate, client.field.approach_mode.linear)
#         #     client.wait_for(0, 0, client.field.waitfor)
#         # except:
#         #     print("⚠️ Could not return field to 0.")
#
#         plt.show()
#
# except KeyboardInterrupt:
#     print("\n⛔ Measurement interrupted by user.")



# print("🧹 Returning field to 0 Oe...")
# client.set_field(0, magnetic_rate, client.field.approach_mode.linear)
# client.wait_for(0, 0, client.field.waitfor)


# import tkinter as tk
# from tkinter import filedialog, messagebox
# import os
# import time
# import csv
# import pyvisa
# import numpy as np
# import matplotlib.pyplot as plt
# import matplotlib
# import MultiPyVu as mpv
# from datetime import datetime
#
# matplotlib.use("TkAgg")
#
# # ----------------------------
# # GUI for Measurement Settings
# # ----------------------------
# def start_measurement():
#     try:
#         # Fetch values from GUI
#         max_field = int(entry_field.get())
#         step_field = int(entry_step.get())
#         rate_field = float(entry_rate.get())
#         target_temp = int(entry_temp.get())
#         temp_rate = float(entry_temp_rate.get())
#         folder_path = filedialog.askdirectory(title="Select Save Directory")
#
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         folder_name = os.path.join(folder_path, f"{target_temp}K_hysteresis_field_sweep_{max_field}Oe_{timestamp}")
#         os.makedirs(folder_name, exist_ok=True)
#
#         data_filename = os.path.join(folder_name, "field_sweep_csrs_0Vg.dat")
#         plot_filename = os.path.join(folder_name, "field_sweep_csrs_plot_0Vg.png")
#
#         # Initialize LCR Meter
#         rm = pyvisa.ResourceManager()
#         resources = rm.list_resources()
#         lcr = None
#         for r in resources:
#             try:
#                 dev = rm.open_resource(r)
#                 idn = dev.query("*IDN?")
#                 if "E4980" in idn:
#                     lcr = dev
#                     print(f"Connected to LCR Meter: {idn.strip()}")
#                     break
#             except:
#                 continue
#
#         if lcr is None:
#             raise RuntimeError("E4980B not found.")
#
#         lcr.write("*RST")
#         lcr.write("FUNC:IMP CSRS")
#         lcr.write("FREQ 20")
#         lcr.write("VOLT 0.3")
#         lcr.write("APER LONG")
#         lcr.write(":FORM:ELEM CSRS")
#
#         plt.ion()
#         fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
#         ax1.set_ylabel("Capacitance (F)")
#         ax2.set_ylabel("Resistance (Ohm)")
#         ax2.set_xlabel("Magnetic Field (Oe)")
#         ax1.grid(True)
#         ax2.grid(True)
#         line1, = ax1.plot([], [], 'b.-', label='Cs')
#         line2, = ax2.plot([], [], 'r.-', label='Rs')
#         fields, caps, ress, temps = [], [], [], []
#
#         with mpv.Client(host="10.227.234.170") as client:
#             appr = client.temperature.approach_mode.fast_settle
#             client.set_temperature(target_temp, temp_rate, appr)
#             client.wait_for(10, 0, client.temperature.waitfor)
#             t_meas, _ = client.get_temperature()
#
#             field_forward = list(range(-max_field, max_field + step_field, step_field))
#             field_reverse = list(range(max_field, -max_field - step_field, -step_field))
#             field_list = field_forward + field_reverse
#
#             with open(data_filename, "w", newline="") as f:
#                 writer = csv.writer(f, delimiter="\t")
#                 writer.writerow(["Temperature (K)", "Field (Oe)", "Capacitance (F)", "Resistance (Ohm)"])
#                 for field in field_list:
#                     client.set_field(field, rate_field, client.field.approach_mode.linear)
#                     client.wait_for(0, 0, client.field.waitfor)
#                     time.sleep(0.3)
#                     lcr.write("INIT")
#                     time.sleep(0.3)
#                     result = lcr.query("FETC?")
#                     Cs, Rs = [float(x) for x in result.strip().split(',')[:2]]
#
#                     fields.append(field)
#                     caps.append(Cs)
#                     ress.append(Rs)
#                     temps.append(t_meas)
#                     writer.writerow([t_meas, field, Cs, Rs])
#
#                     line1.set_data(fields, caps)
#                     line2.set_data(fields, ress)
#                     ax1.relim(); ax1.autoscale_view()
#                     ax2.relim(); ax2.autoscale_view()
#                     plt.pause(0.01)
#
#             client.set_field(0, rate_field, client.field.approach_mode.linear)
#             client.wait_for(0, 0, client.field.waitfor)
#             plt.ioff()
#             plt.tight_layout()
#             plt.savefig(plot_filename)
#             plt.show()
#             messagebox.showinfo("Success", f"Measurement complete.\nData saved to:\n{data_filename}")
#
#     except Exception as e:
#         messagebox.showerror("Error", str(e))
#
# # ----------------------------
# # TKinter GUI Layout
# # ----------------------------
# root = tk.Tk()
# root.title("Magnetic Field Sweep GUI")
#
# frame = tk.Frame(root, padx=10, pady=10)
# frame.pack()
#
# labels = ["Max Field (Oe)", "Field Step (Oe)", "Field Rate (Oe/s)", "Target Temp (K)", "Temp Rate (K/min)"]
# def_vals = ["5000", "100", "100", "300", "20"]
# entries = []
#
# for i, (lbl, val) in enumerate(zip(labels, def_vals)):
#     tk.Label(frame, text=lbl).grid(row=i, column=0, sticky='e')
#     ent = tk.Entry(frame)
#     ent.insert(0, val)
#     ent.grid(row=i, column=1)
#     entries.append(ent)
#
# entry_field, entry_step, entry_rate, entry_temp, entry_temp_rate = entries
#
# btn = tk.Button(frame, text="Start Measurement", command=start_measurement, bg="green", fg="white")
# btn.grid(row=len(labels), columnspan=2, pady=10)
#
# root.mainloop()

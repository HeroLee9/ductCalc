import csv
import math
import tkinter as tk
from tkinter import ttk
import ezdxf
from ezdxf import units

# Lists used to store duct data
duct_name_list = []
duct_type_list = []
duct_qty_list = []
duct_thickness_list = []
duct_bwidth_list = []
duct_blength_list = []
duct_total_sqft_list = []
duct_total_weight_list = []
duct_diameter = []


def get_r(x, y, z):
    return math.sqrt((0.5 * x - 0.5 * y) ** 2 + z ** 2)


def get_p(x, y, z):
    return x * (math.sqrt((0.5 * x - 0.5 * y) ** 2 + z ** 2)) / (y - z)


def get_length(x, y, z):
    return (2 * x) * math.sin(y / (2 * x)) + z * 2


def get_arc(x, y, z):
    return (2 * x) * math.sin(y / (2 * x)) + z * 2


def get_sagitta(x, y):
    return x - (math.sqrt(x ** 2 - (y / 2) ** 2))


# --- DXF drawing helpers (copied from ductCalc.py) -------------------------

def draw_straight(width: float, length: float, filename: str) -> None:
    """Create a DXF flat pattern for a straight duct."""
    doc = ezdxf.new()
    doc.units = units.IN
    doc.header['$INSUNITS'] = units.IN
    doc.header['$MEASUREMENT'] = 0
    msp = doc.modelspace()

    msp.add_line((0, 0), (width, 0))
    msp.add_line((width, 0), (width, length))
    msp.add_line((width, length), (0, length))
    msp.add_line((0, length), (0, 0))
    doc.saveas(filename)


def draw_cone(filename: str, radius1: float, radius2: float, end_angle: float) -> None:
    """Create a DXF flat pattern for a cone."""
    doc = ezdxf.new()
    doc.units = units.IN
    doc.header['$INSUNITS'] = units.IN
    doc.header['$MEASUREMENT'] = 0
    msp = doc.modelspace()

    center = (0, 0)
    start_angle = 0

    msp.add_arc(center=center, radius=radius1, start_angle=start_angle, end_angle=end_angle)
    msp.add_arc(center=center, radius=radius2, start_angle=start_angle, end_angle=end_angle)

    x1_start = center[0] + radius1 * math.cos(math.radians(start_angle))
    y1_start = center[1] + radius1 * math.sin(math.radians(start_angle))
    x1_end = center[0] + radius1 * math.cos(math.radians(end_angle))
    y1_end = center[1] + radius1 * math.sin(math.radians(end_angle))

    x2_start = center[0] + radius2 * math.cos(math.radians(start_angle))
    y2_start = center[1] + radius2 * math.sin(math.radians(start_angle))
    x2_end = center[0] + radius2 * math.cos(math.radians(end_angle))
    y2_end = center[1] + radius2 * math.sin(math.radians(end_angle))

    msp.add_line((x1_start, y1_start), (x2_start, y2_start))
    msp.add_line((x1_end, y1_end), (x2_end, y2_end))

    doc.saveas(filename)


# ---------------------------------------------------------------------------

def display_csv_content(total_qty, total_sqft, total_weight):
    """Refresh the CSV preview in the GUI."""
    csv_content.delete(1.0, tk.END)
    with open(csv_filename, 'r') as file:
        for line in file:
            csv_content.insert(tk.END, line)
    csv_content.insert(tk.END, f"\nTotal QTY: {total_qty.get()}\n")
    csv_content.insert(tk.END, f"Total SQFT: {total_sqft.get()}\n")
    csv_content.insert(tk.END, f"Total Weight: {total_weight.get()}\n")


def csv_write():
    """Write the collected data to a CSV file."""
    with open(csv_filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            'Name', 'Type', 'QTY', 'Thickness', 'Diameter',
            'BBox Width', 'BBox Length', 'BBox Weight', 'BBox SQFT'])
        writer.writerows(
            zip(
                duct_name_list, duct_type_list, duct_qty_list,
                duct_thickness_list, duct_diameter, duct_bwidth_list,
                duct_blength_list, duct_total_weight_list,
                duct_total_sqft_list,
            )
        )
        writer.writerow([
            'Total:', sum(duct_qty_list), '', '', '', '',
            sum(duct_total_weight_list), sum(duct_total_sqft_list)
        ])


# ---------------------------------------------------------------------------

def duct_name_and_type():
    """Create widgets for entering duct information."""

    def updated_combo_value(event):
        duct_type = combo_value.get()
        duct_name = duct_name_entry.get()
        duct_name_list.append(duct_name)
        duct_type_list.append(duct_type)

        for widget in duct_widgets:
            widget.destroy()

        if duct_type == 'Straight':
            create_straight_duct_widgets()
        elif duct_type == 'Reducing Cone':
            create_reducing_cone_widgets()
        elif duct_type == 'Gored Elbow':
            create_gored_elbow_widgets()

    def create_straight_duct_widgets():
        def calculate_straight_values():
            total_qty = tk.DoubleVar()
            total_sqft = tk.DoubleVar()
            total_weight = tk.DoubleVar()

            thickness = float(thickness_entry.get())
            diameter = float(diameter_entry.get())
            circumference = diameter * math.pi
            length = float(length_entry.get())
            qty = float(qty_entry.get())
            steel_density = 0.2836
            weight = ((circumference * length * thickness) * steel_density) * qty
            sqft = ((circumference * length) / 144) * qty

            duct_qty_list.append(qty)
            duct_thickness_list.append(round(thickness, 2))
            duct_bwidth_list.append(round(circumference, 2))
            duct_blength_list.append(round(length, 2))
            duct_total_sqft_list.append(round(sqft, 2))
            duct_total_weight_list.append(round(weight, 2))
            duct_diameter.append(diameter)

            total_qty.set(sum(duct_qty_list))
            total_sqft.set(sum(duct_total_sqft_list))
            total_weight.set(sum(duct_total_weight_list))

            duct_name = duct_name_entry.get()
            draw_straight(circumference, length, f"{duct_name}.dxf")

            for w in duct_widgets:
                w.destroy()
            duct_name_entry.delete(0, 'end')
            csv_write()
            display_csv_content(total_qty, total_sqft, total_weight)

        global duct_widgets
        duct_widgets = []
        thickness_label = ttk.Label(root, text='Thickness: ')
        thickness_label.grid(row=6, column=0, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(thickness_label)
        thickness_entry = ttk.Entry(root)
        thickness_entry.grid(row=6, column=1, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(thickness_entry)

        diameter_label = ttk.Label(root, text='Diameter: ')
        diameter_label.grid(row=7, column=0, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(diameter_label)
        diameter_entry = ttk.Entry(root)
        diameter_entry.grid(row=7, column=1, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(diameter_entry)

        length_label = ttk.Label(root, text='Length: ')
        length_label.grid(row=8, column=0, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(length_label)
        length_entry = ttk.Entry(root)
        length_entry.grid(row=8, column=1, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(length_entry)

        qty_label = ttk.Label(root, text='QTY: ')
        qty_label.grid(row=9, column=0, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(qty_label)
        qty_entry = ttk.Entry(root)
        qty_entry.grid(row=9, column=1, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(qty_entry)

        submit_duct = ttk.Button(root, text='Enter', command=calculate_straight_values)
        submit_duct.grid(row=10, column=1, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(submit_duct)

    def create_reducing_cone_widgets():
        def calculate_reducing_cone():
            total_qty = tk.DoubleVar()
            total_sqft = tk.DoubleVar()
            total_weight = tk.DoubleVar()

            qty = float(qty_entry.get())
            steel_weight = 0.2836
            s_dia = float(small_diameter_entry.get())
            l_dia = float(large_diameter_entry.get())
            height = float(length_entry.get())
            thickness = float(thickness_entry.get())
            r = get_r(l_dia, s_dia, height)  # Slant height
            p = get_p(height, l_dia, s_dia)  # Flat pattern inside radius
            q = r + p  # Flat pattern outside radius (large diameter)
            l_inner_arc = math.pi * s_dia  # Length of inner arc
            l_outer_arc = math.pi * l_dia  # Length of outer arc
            a = l_inner_arc / p
            d = (a * 180) / math.pi
            b_length = get_length(q, l_outer_arc, thickness)
            b_arc = get_arc(p, l_inner_arc, thickness)
            sagitta = get_sagitta(p, b_arc)
            b_width = sagitta + r
            b_sqft = (b_width * b_length) / 144
            b_volume = b_width * b_length * thickness
            b_weight = b_volume * steel_weight

            duct_qty_list.append(qty)
            duct_thickness_list.append(round(thickness, 2))
            duct_bwidth_list.append(round(b_width, 2))
            duct_blength_list.append(round(b_length, 2))
            duct_total_sqft_list.append(round(b_sqft, 2))
            duct_total_weight_list.append(round(b_weight, 2))
            duct_diameter.append(round(s_dia, 2))

            total_qty.set(sum(duct_qty_list))
            total_sqft.set(sum(duct_total_sqft_list))
            total_weight.set(sum(duct_total_weight_list))

            duct_name = duct_name_entry.get()
            draw_cone(f"{duct_name}.dxf", p, q, d)

            for w in duct_widgets:
                w.destroy()
            duct_name_entry.delete(0, 'end')
            csv_write()
            display_csv_content(total_qty, total_sqft, total_weight)

        global duct_widgets
        duct_widgets = []
        thickness_label = ttk.Label(root, text='Thickness: ')
        thickness_label.grid(row=6, column=0, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(thickness_label)
        thickness_entry = ttk.Entry(root)
        thickness_entry.grid(row=6, column=1, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(thickness_entry)

        small_diameter_label = ttk.Label(root, text='Small Diameter: ')
        small_diameter_label.grid(row=7, column=0, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(small_diameter_label)
        small_diameter_entry = ttk.Entry(root)
        small_diameter_entry.grid(row=7, column=1, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(small_diameter_entry)

        large_diameter_label = ttk.Label(root, text='Large Diameter: ')
        large_diameter_label.grid(row=8, column=0, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(large_diameter_label)
        large_diameter_entry = ttk.Entry(root)
        large_diameter_entry.grid(row=8, column=1, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(large_diameter_entry)

        length_label = ttk.Label(root, text='Length: ')
        length_label.grid(row=9, column=0, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(length_label)
        length_entry = ttk.Entry(root)
        length_entry.grid(row=9, column=1, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(length_entry)

        qty_label = ttk.Label(root, text='QTY: ')
        qty_label.grid(row=10, column=0, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(qty_label)
        qty_entry = ttk.Entry(root)
        qty_entry.grid(row=10, column=1, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(qty_entry)

        submit_duct = ttk.Button(root, text='Enter', command=calculate_reducing_cone)
        submit_duct.grid(row=11, column=1, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(submit_duct)

    def create_gored_elbow_widgets():
        global duct_widgets
        duct_widgets = []

        def calculate_gored_elbow():
            total_qty = tk.DoubleVar()
            total_sqft = tk.DoubleVar()
            total_weight = tk.DoubleVar()

            qty = float(qty_entry.get())
            thickness = float(thickness_entry.get())
            diameter = float(diameter_entry.get())
            steel_weight = 0.2836
            clr = float(clr_entry.get())
            degree = float(degree_entry.get())
            blength = clr * 2
            bwidth = diameter * math.pi
            sqft = ((((blength * bwidth) / 144) * degree) / 90) * qty
            weight = (sqft * 144 * thickness * steel_weight)

            duct_qty_list.append(qty)
            duct_thickness_list.append(round(thickness, 2))
            duct_bwidth_list.append(round(bwidth, 2))
            duct_blength_list.append(round(blength, 2))
            duct_total_sqft_list.append(round(sqft, 2))
            duct_total_weight_list.append(round(weight, 2))
            duct_diameter.append(round(diameter, 2))

            total_qty.set(sum(duct_qty_list))
            total_sqft.set(sum(duct_total_sqft_list))
            total_weight.set(sum(duct_total_weight_list))

            for w in duct_widgets:
                w.destroy()
            duct_name_entry.delete(0, 'end')
            csv_write()
            display_csv_content(total_qty, total_sqft, total_weight)

        thickness_label = ttk.Label(root, text='Thickness: ')
        thickness_label.grid(row=6, column=0, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(thickness_label)
        thickness_entry = ttk.Entry(root)
        thickness_entry.grid(row=6, column=1, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(thickness_entry)

        diameter_label = ttk.Label(root, text='Diameter: ')
        diameter_label.grid(row=7, column=0, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(diameter_label)
        diameter_entry = ttk.Entry(root)
        diameter_entry.grid(row=7, column=1, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(diameter_entry)

        degree_label = ttk.Label(root, text='Degree: ')
        degree_label.grid(row=8, column=0, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(degree_label)
        degree_entry = ttk.Entry(root)
        degree_entry.grid(row=8, column=1, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(degree_entry)

        clr_label = ttk.Label(root, text='Center Line Radius: ')
        clr_label.grid(row=9, column=0, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(clr_label)
        clr_entry = ttk.Entry(root)
        clr_entry.grid(row=9, column=1, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(clr_entry)

        qty_label = ttk.Label(root, text='QTY: ')
        qty_label.grid(row=11, column=0, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(qty_label)
        qty_entry = ttk.Entry(root)
        qty_entry.grid(row=11, column=1, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(qty_entry)

        submit_duct = ttk.Button(root, text='Enter', command=calculate_gored_elbow)
        submit_duct.grid(row=12, column=1, pady=2, padx=5, sticky='NWES')
        duct_widgets.append(submit_duct)

    # --- initial widgets for duct name/type selection
    duct_name = ttk.Label(root, text='Duct Name: ')
    duct_name.grid(row=4, column=0, pady=2, padx=5, sticky='NWES')
    duct_name_entry = ttk.Entry(root)
    duct_name_entry.grid(row=4, column=1, pady=2, padx=5, sticky='NWES')
    duct_type = ttk.Label(root, text='Duct Type: ')
    duct_type.grid(row=5, column=0, pady=2, padx=5, sticky='NWES')

    global combo_value
    combo_value = tk.StringVar()
    types = ['Straight', 'Reducing Cone', 'Gored Elbow']
    duct_type_box = ttk.Combobox(root, values=types, state='readonly', textvariable=combo_value)
    duct_type_box.bind("<<ComboboxSelected>>", updated_combo_value)
    duct_type_box.current(0)
    duct_type_box.grid(row=5, column=1, pady=2, padx=5, sticky='NWES')

    global duct_widgets
    duct_widgets = []


def overview_info():
    """Grab overview information and show duct entry form."""
    global customer, quote, csv_filename
    customer = customer_name_entry.get()
    quote = quote_number_entry.get()
    project = project_name_entry.get()
    csv_filename = f"{customer}_{quote}.csv"

    ttk.Label(root, text=customer).grid(row=1, column=1, pady=2, padx=5, sticky='NWES')
    ttk.Label(root, text=quote).grid(row=2, column=1, pady=2, padx=5, sticky='NWES')
    ttk.Label(root, text=project).grid(row=3, column=1, pady=2, padx=5, sticky='NWES')

    customer_name_entry.destroy()
    quote_number_entry.destroy()
    project_name_entry.destroy()
    overview_info_button.destroy()

    duct_name_and_type()


# --- main window -----------------------------------------------------------
root = tk.Tk()
root.geometry('960x540')
root.title("Duct Calculator")

customer_name = ttk.Label(root, text='Customer Name: ')
customer_name.grid(row=1, column=0, pady=2, padx=5, sticky='NWES')
customer_name_entry = ttk.Entry(root)
customer_name_entry.grid(row=1, column=1, pady=2, padx=5, sticky='NWES')

quote_number = ttk.Label(root, text='Quote Number: ')
quote_number.grid(row=2, column=0, pady=2, padx=5, sticky='NWES')
quote_number_entry = ttk.Entry(root)
quote_number_entry.grid(row=2, column=1, pady=2, padx=5, sticky='NWES')

project_name = ttk.Label(root, text='Project Name: ')
project_name.grid(row=3, column=0, pady=2, padx=5, sticky='NWES')
project_name_entry = ttk.Entry(root)
project_name_entry.grid(row=3, column=1, pady=2, padx=5, sticky='NWES')

overview_info_button = ttk.Button(root, text='Enter', command=overview_info)
overview_info_button.grid(row=4, column=1, pady=2, padx=5, sticky='NWES')

csv_content = tk.Text(root, height=30, width=100)
csv_content.grid(row=1, rowspan=30, column=3, columnspan=2, padx=5, pady=5, sticky='NWES')

root.mainloop()

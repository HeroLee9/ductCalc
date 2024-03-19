import csv
import math
import ezdxf
import tkinter as tk
from tkinter import ttk

def getStraightWeight(length, width, thickness, qty):
    weight = float(qty * ((length * width * thickness) * 0.2833))
    return weight

def create_duct():
    # Initialize totals
    total_qty = tk.DoubleVar()
    total_sqft = tk.DoubleVar()
    total_weight = tk.DoubleVar()

    name = name_entry.get()
    qty = float(qty_entry.get())
    thickness = float(thickness_entry.get())
    dia = float(dia_entry.get())
    length = float(length_entry.get())

    circ = dia * math.pi
    weight = getStraightWeight(length, circ, thickness, qty)
    sqft = getStraightSqft(length, circ, qty)

    # Add data to lists
    nameList.append(name)
    qtyList.append(qty)
    thicknessList.append(thickness)
    diaList.append(dia)
    circList.append(circ)
    lengthList.append(length)
    weightList.append(weight)
    sqftList.append(sqft)

    # Update totals
    total_qty.set(sum(qtyList))
    total_sqft.set(sum(sqftList))
    total_weight.set(sum(weightList))

    # Write to CSV file
    with open('duct_data.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Name', 'QTY', 'Thickness', 'Diameter', 'Flat Width', 'Flat Length', 'Total Weight', 'Total SQFT'])
        writer.writerows(zip(nameList, qtyList, thicknessList, diaList, circList, lengthList, weightList, sqftList))
        writer.writerow(['Total:', sum(qtyList), '', '', '', '', sum(weightList), sum(sqftList)])

    # Create a DXF file for each duct
    for i in range(1, len(nameList)):
        doc = ezdxf.new(dxfversion='R2010')
        msp = doc.modelspace()
        
        circ = circList[i]
        length = lengthList[i]
        
        msp.add_lwpolyline([(0, 0), (0, circ), (length, circ), (length, 0)], close=True)
        
        duct_name = nameList[i].replace(" ", "_")  # Replace spaces with underscores
        doc.saveas(f"{duct_name}.dxf")

    # Clear input fields
    name_entry.delete(0, tk.END)
    qty_entry.delete(0, tk.END)
    thickness_entry.delete(0, tk.END)
    dia_entry.delete(0, tk.END)
    length_entry.delete(0, tk.END)

    # Display CSV content on the screen
    display_csv_content(total_qty, total_sqft, total_weight)

def display_csv_content(total_qty, total_sqft, total_weight):
    csv_content.delete(1.0, tk.END)
    with open('duct_data.csv', 'r') as file:
        for line in file:
            csv_content.insert(tk.END, line)
    csv_content.insert(tk.END, f"\nTotal QTY: {total_qty.get()}\n")
    csv_content.insert(tk.END, f"Total SQFT: {total_sqft.get()}\n")
    csv_content.insert(tk.END, f"Total Weight: {total_weight.get()}\n")

def getStraightSqft(length, width, qty):
    sqft = float(qty * ((length * width) / 144))
    return sqft

# Initialize lists
nameList = []
qtyList = []
thicknessList = []
diaList = []
circList = []
lengthList = []
weightList = []
sqftList = []

# Create the main window
root = tk.Tk()
root.title("Duct Calculator")

# Create and place input fields and labels
labels = ['Duct name:', 'QTY required:', 'Sheet thickness:', 'Duct Diameter:', 'Duct length:']
for i, label_text in enumerate(labels):
    label = ttk.Label(root, text=label_text)
    label.grid(row=i, column=0, sticky='w', padx=5, pady=5)

name_entry = ttk.Entry(root)
name_entry.grid(row=0, column=1, padx=5, pady=5)

qty_entry = ttk.Entry(root)
qty_entry.grid(row=1, column=1, padx=5, pady=5)

thickness_entry = ttk.Entry(root)
thickness_entry.grid(row=2, column=1, padx=5, pady=5)

dia_entry = ttk.Entry(root)
dia_entry.grid(row=3, column=1, padx=5, pady=5)

length_entry = ttk.Entry(root)
length_entry.grid(row=4, column=1, padx=5, pady=5)

# Create and place the 'Create Duct' button
create_button = ttk.Button(root, text="Create Duct", command=create_duct)
create_button.grid(row=5, columnspan=2, padx=5, pady=10)

# Create text widget to display CSV content
csv_content = tk.Text(root, height=10, width=70)
csv_content.grid(row=6, columnspan=2, padx=5, pady=5)

root.mainloop()

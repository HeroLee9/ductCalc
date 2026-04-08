from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import ezdxf
    from ezdxf import units
except Exception:  # ezdxf optional for data-only workflows
    ezdxf = None
    units = None

STEEL_DENSITY_LB_PER_IN3 = 0.2836
DEFAULT_LABOR_RATE = 82.0


@dataclass
class LineItem:
    item_id: int
    name: str
    fitting_type: str
    qty: float
    thickness: float
    diameter: float
    width: float
    length: float
    area_sqft: float
    weight_lb: float
    labor_hours: float
    material_cost: float
    labor_cost: float
    total_cost: float
    metadata: dict


class DuctEngine:
    @staticmethod
    def straight(qty: float, thickness: float, diameter: float, length: float, material_price_sqft: float, labor_rate: float) -> dict:
        width = diameter * math.pi
        area_sqft = qty * ((width * length) / 144.0)
        weight = qty * (width * length * thickness * STEEL_DENSITY_LB_PER_IN3)
        labor_hours = qty * (0.18 + 0.0018 * width + 0.0012 * length)
        material_cost = area_sqft * material_price_sqft
        labor_cost = labor_hours * labor_rate
        return {
            "diameter": diameter,
            "width": width,
            "length": length,
            "area_sqft": area_sqft,
            "weight_lb": weight,
            "labor_hours": labor_hours,
            "material_cost": material_cost,
            "labor_cost": labor_cost,
            "total_cost": material_cost + labor_cost,
            "metadata": {},
        }

    @staticmethod
    def reducing_cone(qty: float, thickness: float, small_dia: float, large_dia: float, height: float, material_price_sqft: float, labor_rate: float) -> dict:
        slant = math.sqrt(((large_dia - small_dia) / 2.0) ** 2 + height ** 2)
        lateral_area = math.pi * ((large_dia + small_dia) / 2.0) * slant
        area_sqft = qty * lateral_area / 144.0

        inner_radius = (small_dia / (large_dia - small_dia)) * slant if large_dia != small_dia else 0.0
        outer_radius = inner_radius + slant
        angle_deg = 360.0 * (small_dia / (2.0 * inner_radius)) if inner_radius > 0 else 360.0
        bbox_width, bbox_length = DuctEngine._cone_bbox(inner_radius, outer_radius, min(angle_deg, 360.0))

        weight = qty * (bbox_width * bbox_length * thickness * STEEL_DENSITY_LB_PER_IN3)
        labor_hours = qty * (0.35 + 0.0016 * (small_dia + large_dia) + 0.0022 * height)
        material_cost = area_sqft * material_price_sqft
        labor_cost = labor_hours * labor_rate
        return {
            "diameter": small_dia,
            "width": bbox_width,
            "length": bbox_length,
            "area_sqft": area_sqft,
            "weight_lb": weight,
            "labor_hours": labor_hours,
            "material_cost": material_cost,
            "labor_cost": labor_cost,
            "total_cost": material_cost + labor_cost,
            "metadata": {
                "small_dia": small_dia,
                "large_dia": large_dia,
                "height": height,
                "inner_radius": inner_radius,
                "outer_radius": outer_radius,
                "angle_deg": min(angle_deg, 360.0),
            },
        }

    @staticmethod
    def gored_elbow(qty: float, thickness: float, diameter: float, clr: float, angle_deg: float, gores: int, material_price_sqft: float, labor_rate: float) -> dict:
        center_length = (2.0 * clr) * (angle_deg / 90.0)
        width = diameter * math.pi
        area_sqft = qty * (center_length * width) / 144.0
        weight = qty * (center_length * width * thickness * STEEL_DENSITY_LB_PER_IN3)
        complexity = max(1, gores - 2)
        labor_hours = qty * (0.4 + 0.0024 * diameter + 0.0045 * complexity + 0.0015 * angle_deg)
        material_cost = area_sqft * material_price_sqft
        labor_cost = labor_hours * labor_rate
        return {
            "diameter": diameter,
            "width": width,
            "length": center_length,
            "area_sqft": area_sqft,
            "weight_lb": weight,
            "labor_hours": labor_hours,
            "material_cost": material_cost,
            "labor_cost": labor_cost,
            "total_cost": material_cost + labor_cost,
            "metadata": {
                "clr": clr,
                "angle_deg": angle_deg,
                "gores": gores,
            },
        }

    @staticmethod
    def offset(qty: float, thickness: float, diameter: float, rise: float, run: float, material_price_sqft: float, labor_rate: float) -> dict:
        travel = math.sqrt(rise ** 2 + run ** 2)
        width = diameter * math.pi
        area_sqft = qty * (travel * width) / 144.0
        weight = qty * (travel * width * thickness * STEEL_DENSITY_LB_PER_IN3)
        labor_hours = qty * (0.28 + 0.0018 * diameter + 0.0022 * travel)
        material_cost = area_sqft * material_price_sqft
        labor_cost = labor_hours * labor_rate
        return {
            "diameter": diameter,
            "width": width,
            "length": travel,
            "area_sqft": area_sqft,
            "weight_lb": weight,
            "labor_hours": labor_hours,
            "material_cost": material_cost,
            "labor_cost": labor_cost,
            "total_cost": material_cost + labor_cost,
            "metadata": {
                "rise": rise,
                "run": run,
                "travel": travel,
            },
        }

    @staticmethod
    def _cone_bbox(inner_radius: float, outer_radius: float, angle_deg: float) -> tuple[float, float]:
        angles = [0.0, angle_deg]
        for a in (90.0, 180.0, 270.0, 360.0):
            if 0.0 < a < angle_deg:
                angles.append(a)
        xs, ys = [], []
        for ang in angles:
            rad = math.radians(ang)
            for r in (inner_radius, outer_radius):
                xs.append(r * math.cos(rad))
                ys.append(r * math.sin(rad))
        return max(xs) - min(xs), max(ys) - min(0.0, min(ys))


class CamductLikeApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("DuctCalc Pro — CAMduct-style workflow")
        self.root.geometry("1300x760")

        self.items: list[LineItem] = []
        self.next_item_id = 1
        self.project = {
            "customer": "",
            "quote": "",
            "project": "",
            "created_utc": datetime.utcnow().isoformat(timespec="seconds"),
        }

        self.material_price_by_thickness = {
            "0.018": 8.50,
            "0.024": 9.75,
            "0.030": 11.10,
            "0.036": 12.40,
            "0.048": 14.85,
        }

        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        for idx, field in enumerate(("Customer", "Quote", "Project")):
            ttk.Label(top, text=f"{field}:").grid(row=0, column=idx * 2, padx=4, pady=2, sticky="w")

        self.customer_var = tk.StringVar()
        self.quote_var = tk.StringVar()
        self.project_var = tk.StringVar()
        self.labor_rate_var = tk.DoubleVar(value=DEFAULT_LABOR_RATE)

        ttk.Entry(top, textvariable=self.customer_var, width=22).grid(row=0, column=1, padx=4, pady=2)
        ttk.Entry(top, textvariable=self.quote_var, width=14).grid(row=0, column=3, padx=4, pady=2)
        ttk.Entry(top, textvariable=self.project_var, width=22).grid(row=0, column=5, padx=4, pady=2)

        ttk.Label(top, text="Labor $/hr:").grid(row=0, column=6, padx=4)
        ttk.Entry(top, textvariable=self.labor_rate_var, width=10).grid(row=0, column=7, padx=4)

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=8)

        self.add_tab = ttk.Frame(notebook, padding=10)
        self.takeoff_tab = ttk.Frame(notebook, padding=10)
        self.materials_tab = ttk.Frame(notebook, padding=10)

        notebook.add(self.add_tab, text="Fitting Entry")
        notebook.add(self.takeoff_tab, text="Takeoff & Costing")
        notebook.add(self.materials_tab, text="Material Library")

        self._build_add_tab()
        self._build_takeoff_tab()
        self._build_materials_tab()

    def _build_add_tab(self):
        left = ttk.Frame(self.add_tab)
        left.pack(side="left", fill="y")

        self.fit_type_var = tk.StringVar(value="Straight")
        self.name_var = tk.StringVar()
        self.qty_var = tk.DoubleVar(value=1.0)
        self.thickness_var = tk.StringVar(value="0.024")
        self.diameter_var = tk.DoubleVar(value=12.0)
        self.length_var = tk.DoubleVar(value=48.0)
        self.large_dia_var = tk.DoubleVar(value=16.0)
        self.height_var = tk.DoubleVar(value=24.0)
        self.clr_var = tk.DoubleVar(value=18.0)
        self.angle_var = tk.DoubleVar(value=90.0)
        self.gores_var = tk.IntVar(value=5)
        self.rise_var = tk.DoubleVar(value=12.0)
        self.run_var = tk.DoubleVar(value=12.0)

        row = 0
        ttk.Label(left, text="Fitting Type:").grid(row=row, column=0, sticky="w", pady=3)
        type_box = ttk.Combobox(left, state="readonly", textvariable=self.fit_type_var,
                                values=["Straight", "Reducing Cone", "Gored Elbow", "Offset"])
        type_box.grid(row=row, column=1, sticky="ew", pady=3)
        type_box.bind("<<ComboboxSelected>>", lambda _e: self._toggle_fields())

        controls = [
            ("Part Name", self.name_var),
            ("Quantity", self.qty_var),
            ("Thickness (in)", self.thickness_var),
            ("Diameter", self.diameter_var),
            ("Length", self.length_var),
            ("Large Dia", self.large_dia_var),
            ("Height", self.height_var),
            ("CLR", self.clr_var),
            ("Angle", self.angle_var),
            ("Gores", self.gores_var),
            ("Rise", self.rise_var),
            ("Run", self.run_var),
        ]
        self.form_rows = {}
        for label, var in controls:
            row += 1
            ttk.Label(left, text=f"{label}:").grid(row=row, column=0, sticky="w", pady=3)
            widget = ttk.Entry(left, textvariable=var)
            widget.grid(row=row, column=1, sticky="ew", pady=3)
            self.form_rows[label] = (row, widget)

        row += 1
        ttk.Button(left, text="Add Fitting", command=self.add_item).grid(row=row, column=0, columnspan=2, sticky="ew", pady=8)
        row += 1
        ttk.Button(left, text="Generate Selected DXF", command=self.generate_selected_dxf).grid(row=row, column=0, columnspan=2, sticky="ew", pady=3)

        right = ttk.LabelFrame(self.add_tab, text="CAMduct-like Workflow Notes", padding=10)
        right.pack(side="left", fill="both", expand=True, padx=10)
        notes = (
            "• Add fittings from a library (straight, cone, elbow, offset).\n"
            "• Automatic area, weight, labor, and total cost per fitting.\n"
            "• Batch takeoff table with by-thickness rollups.\n"
            "• Save/load complete projects as JSON.\n"
            "• Export CSV and generate DXF patterns for fabrication.\n"
            "\nThis is a production-style foundation, not feature parity with Autodesk CAMduct."
        )
        ttk.Label(right, text=notes, justify="left").pack(anchor="w")

        self._toggle_fields()

    def _build_takeoff_tab(self):
        cols = ("ID", "Name", "Type", "Qty", "Thk", "Dia", "Width", "Length", "SQFT", "Weight", "LaborHr", "Material$", "Labor$", "Total$")
        self.tree = ttk.Treeview(self.takeoff_tab, columns=cols, show="headings", height=23)
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=84, anchor="center")
        self.tree.pack(fill="both", expand=True)

        actions = ttk.Frame(self.takeoff_tab)
        actions.pack(fill="x", pady=8)
        ttk.Button(actions, text="Delete Selected", command=self.delete_selected).pack(side="left", padx=3)
        ttk.Button(actions, text="Export CSV", command=self.export_csv).pack(side="left", padx=3)
        ttk.Button(actions, text="Save Project JSON", command=self.save_project).pack(side="left", padx=3)
        ttk.Button(actions, text="Load Project JSON", command=self.load_project).pack(side="left", padx=3)
        ttk.Button(actions, text="Generate All DXFs", command=self.generate_all_dxfs).pack(side="left", padx=3)

        self.totals_label = ttk.Label(self.takeoff_tab, text="Totals: Qty 0 | SQFT 0 | Weight 0 | Labor 0 | Cost $0")
        self.totals_label.pack(anchor="w", pady=4)

        self.by_gauge = tk.Text(self.takeoff_tab, height=6, width=120)
        self.by_gauge.pack(fill="x")

    def _build_materials_tab(self):
        ttk.Label(self.materials_tab, text="Material cost by thickness ($/sqft)").pack(anchor="w")
        self.mat_tree = ttk.Treeview(self.materials_tab, columns=("thickness", "price"), show="headings", height=10)
        self.mat_tree.heading("thickness", text="Thickness")
        self.mat_tree.heading("price", text="$/SQFT")
        self.mat_tree.pack(fill="x", pady=8)

        for thk, price in sorted(self.material_price_by_thickness.items()):
            self.mat_tree.insert("", "end", values=(thk, f"{price:.2f}"))

        editor = ttk.Frame(self.materials_tab)
        editor.pack(fill="x")
        self.new_thk_var = tk.StringVar()
        self.new_price_var = tk.DoubleVar(value=10.0)
        ttk.Entry(editor, textvariable=self.new_thk_var, width=10).pack(side="left", padx=4)
        ttk.Entry(editor, textvariable=self.new_price_var, width=10).pack(side="left", padx=4)
        ttk.Button(editor, text="Upsert", command=self.upsert_material).pack(side="left", padx=4)

    def _toggle_fields(self):
        fit = self.fit_type_var.get()
        show_for = {
            "Straight": {"Part Name", "Quantity", "Thickness (in)", "Diameter", "Length"},
            "Reducing Cone": {"Part Name", "Quantity", "Thickness (in)", "Diameter", "Large Dia", "Height"},
            "Gored Elbow": {"Part Name", "Quantity", "Thickness (in)", "Diameter", "CLR", "Angle", "Gores"},
            "Offset": {"Part Name", "Quantity", "Thickness (in)", "Diameter", "Rise", "Run"},
        }
        visible = show_for.get(fit, set())
        for label, (row, widget) in self.form_rows.items():
            label_widget = self.add_tab.nametowidget(widget.winfo_parent()).grid_slaves(row=row, column=0)[0]
            if label in visible:
                label_widget.grid()
                widget.grid()
            else:
                label_widget.grid_remove()
                widget.grid_remove()

    def add_item(self):
        try:
            name = self.name_var.get().strip() or f"{self.fit_type_var.get()}-{self.next_item_id}"
            qty = float(self.qty_var.get())
            thickness = float(self.thickness_var.get())
            price_sqft = self.material_price_by_thickness.get(f"{thickness:.3f}", 10.0)
            labor_rate = float(self.labor_rate_var.get())
            fit = self.fit_type_var.get()

            if fit == "Straight":
                data = DuctEngine.straight(qty, thickness, float(self.diameter_var.get()), float(self.length_var.get()), price_sqft, labor_rate)
            elif fit == "Reducing Cone":
                data = DuctEngine.reducing_cone(qty, thickness, float(self.diameter_var.get()), float(self.large_dia_var.get()), float(self.height_var.get()), price_sqft, labor_rate)
            elif fit == "Gored Elbow":
                data = DuctEngine.gored_elbow(qty, thickness, float(self.diameter_var.get()), float(self.clr_var.get()), float(self.angle_var.get()), int(self.gores_var.get()), price_sqft, labor_rate)
            else:
                data = DuctEngine.offset(qty, thickness, float(self.diameter_var.get()), float(self.rise_var.get()), float(self.run_var.get()), price_sqft, labor_rate)

            item = LineItem(
                item_id=self.next_item_id,
                name=name,
                fitting_type=fit,
                qty=qty,
                thickness=thickness,
                diameter=round(data["diameter"], 3),
                width=round(data["width"], 3),
                length=round(data["length"], 3),
                area_sqft=round(data["area_sqft"], 3),
                weight_lb=round(data["weight_lb"], 3),
                labor_hours=round(data["labor_hours"], 3),
                material_cost=round(data["material_cost"], 2),
                labor_cost=round(data["labor_cost"], 2),
                total_cost=round(data["total_cost"], 2),
                metadata=data["metadata"],
            )
            self.items.append(item)
            self.next_item_id += 1
            self.refresh_takeoff()
        except Exception as exc:
            messagebox.showerror("Input error", str(exc))

    def refresh_takeoff(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        for item in self.items:
            self.tree.insert("", "end", iid=str(item.item_id), values=(
                item.item_id, item.name, item.fitting_type, item.qty, item.thickness,
                item.diameter, item.width, item.length, item.area_sqft, item.weight_lb,
                item.labor_hours, item.material_cost, item.labor_cost, item.total_cost,
            ))

        tq = sum(i.qty for i in self.items)
        ta = sum(i.area_sqft for i in self.items)
        tw = sum(i.weight_lb for i in self.items)
        tl = sum(i.labor_hours for i in self.items)
        tc = sum(i.total_cost for i in self.items)
        self.totals_label.config(text=f"Totals: Qty {tq:.2f} | SQFT {ta:.2f} | Weight {tw:.2f} | Labor {tl:.2f} | Cost ${tc:,.2f}")

        rollup = {}
        for i in self.items:
            k = f"{i.thickness:.3f}"
            if k not in rollup:
                rollup[k] = {"sqft": 0.0, "weight": 0.0, "cost": 0.0}
            rollup[k]["sqft"] += i.area_sqft
            rollup[k]["weight"] += i.weight_lb
            rollup[k]["cost"] += i.total_cost

        self.by_gauge.delete("1.0", tk.END)
        self.by_gauge.insert(tk.END, "By thickness summary:\n")
        for thk, vals in sorted(rollup.items()):
            self.by_gauge.insert(tk.END, f"  {thk} in -> SQFT {vals['sqft']:.2f}, Weight {vals['weight']:.2f} lb, Cost ${vals['cost']:.2f}\n")

    def delete_selected(self):
        selection = self.tree.selection()
        ids = {int(s) for s in selection}
        self.items = [i for i in self.items if i.item_id not in ids]
        self.refresh_takeoff()

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ItemID", "Name", "Type", "Qty", "Thickness", "Diameter", "Width", "Length", "AreaSQFT", "WeightLB", "LaborHours", "MaterialCost", "LaborCost", "TotalCost"])
            for i in self.items:
                writer.writerow([i.item_id, i.name, i.fitting_type, i.qty, i.thickness, i.diameter, i.width, i.length, i.area_sqft, i.weight_lb, i.labor_hours, i.material_cost, i.labor_cost, i.total_cost])
        messagebox.showinfo("Export complete", f"CSV exported to\n{path}")

    def save_project(self):
        self._pull_project_header()
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        payload = {
            "project": self.project,
            "labor_rate": self.labor_rate_var.get(),
            "material_price_by_thickness": self.material_price_by_thickness,
            "items": [asdict(i) for i in self.items],
        }
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        messagebox.showinfo("Project saved", path)

    def load_project(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        self.project = payload.get("project", self.project)
        self.customer_var.set(self.project.get("customer", ""))
        self.quote_var.set(self.project.get("quote", ""))
        self.project_var.set(self.project.get("project", ""))
        self.labor_rate_var.set(float(payload.get("labor_rate", DEFAULT_LABOR_RATE)))

        self.material_price_by_thickness = payload.get("material_price_by_thickness", self.material_price_by_thickness)
        self.mat_tree.delete(*self.mat_tree.get_children())
        for thk, price in sorted(self.material_price_by_thickness.items()):
            self.mat_tree.insert("", "end", values=(thk, f"{float(price):.2f}"))

        self.items = [LineItem(**i) for i in payload.get("items", [])]
        self.next_item_id = 1 + max((i.item_id for i in self.items), default=0)
        self.refresh_takeoff()

    def generate_selected_dxf(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Select an item in the takeoff tab first.")
            return
        if ezdxf is None:
            messagebox.showwarning("DXF disabled", "ezdxf is not installed.")
            return

        outdir = filedialog.askdirectory(title="DXF output folder")
        if not outdir:
            return
        selected_ids = {int(i) for i in sel}
        generated = 0
        for item in self.items:
            if item.item_id in selected_ids:
                self._write_item_dxf(item, Path(outdir))
                generated += 1
        messagebox.showinfo("DXF", f"Generated {generated} DXF file(s).")

    def generate_all_dxfs(self):
        if ezdxf is None:
            messagebox.showwarning("DXF disabled", "ezdxf is not installed.")
            return
        outdir = filedialog.askdirectory(title="DXF output folder")
        if not outdir:
            return
        for item in self.items:
            self._write_item_dxf(item, Path(outdir))
        messagebox.showinfo("DXF", f"Generated {len(self.items)} DXF file(s).")

    def _write_item_dxf(self, item: LineItem, outdir: Path):
        doc = ezdxf.new()
        doc.units = units.IN
        doc.header['$INSUNITS'] = units.IN
        doc.header['$MEASUREMENT'] = 0
        msp = doc.modelspace()

        if item.fitting_type in ("Straight", "Offset"):
            msp.add_lwpolyline([(0, 0), (item.width, 0), (item.width, item.length), (0, item.length)], close=True)
        elif item.fitting_type == "Reducing Cone":
            md = item.metadata
            msp.add_arc(center=(0, 0), radius=md.get("inner_radius", 1), start_angle=0, end_angle=md.get("angle_deg", 90))
            msp.add_arc(center=(0, 0), radius=md.get("outer_radius", 2), start_angle=0, end_angle=md.get("angle_deg", 90))
        elif item.fitting_type == "Gored Elbow":
            gores = int(item.metadata.get("gores", 5))
            amp = item.diameter / 4
            seg = item.length / max(gores - 1, 1)
            points_top = []
            x = 0.0
            for idx in range(gores):
                steps = 20
                for i in range(steps):
                    t = i / (steps - 1)
                    wave = math.sin(math.pi * t) if idx in (0, gores - 1) else math.sin(2 * math.pi * t)
                    points_top.append((x + t * seg, (item.width / 2) + amp * wave))
                x += seg
            points_bottom = [(px, item.width - py) for px, py in reversed(points_top)]
            msp.add_lwpolyline(points_top + points_bottom, close=True)

        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in item.name)
        doc.saveas(str(outdir / f"{item.item_id:03d}_{safe_name}.dxf"))

    def _pull_project_header(self):
        self.project["customer"] = self.customer_var.get().strip()
        self.project["quote"] = self.quote_var.get().strip()
        self.project["project"] = self.project_var.get().strip()

    def upsert_material(self):
        try:
            thk = f"{float(self.new_thk_var.get()):.3f}"
            price = float(self.new_price_var.get())
            self.material_price_by_thickness[thk] = price
            self.mat_tree.delete(*self.mat_tree.get_children())
            for t, p in sorted(self.material_price_by_thickness.items()):
                self.mat_tree.insert("", "end", values=(t, f"{float(p):.2f}"))
        except Exception as exc:
            messagebox.showerror("Material update error", str(exc))


def main():
    root = tk.Tk()
    CamductLikeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

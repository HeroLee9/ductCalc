import csv
import math
import ezdxf
from ezdxf import units

def getName():
    print("Enter the duct name: ")
    name = input()
    return name

def getQty():
    print("QTY required: ")
    qty = float(input())
    return qty

def getThickness():
    print("Enter sheet thickness: ")
    thickness = float(input())
    return thickness

def getDia():
    print("Enter the duct Diameter: ")
    dia = float(input())
    return dia

def getLength():
    print("Enter duct length: ")
    length = float(input())
    return length

#.2833 steel weight per cubic inch
def getStraightWeight(length, width, thickness, qty):
    weight = float(qty * ((length * width * thickness) * 0.2833))
    return weight

def getStraightSqft(length, width, qty):
    sqft = float(qty * ((length * width) / 144))
    return sqft

#Cone Calcs
def get_small_dia():
    print("Small Diameter: ", end="")
    dia = float(input())
    return dia

def get_large_dia():
    print("Large Diameter: ", end="")
    dia = float(input())
    return dia

def get_height():
    print("Height (Nearest Inch): ", end="")
    h = float(input())
    return h

def get_thick():
    print("Material Thickness: ", end="")
    h = float(input())
    return h

def get_r(x, y, z):
    r = math.sqrt((0.5 * x - 0.5 * y) ** 2 + z ** 2)
    return r

def get_p(x, y, z):
    p = x * (math.sqrt((0.5 * x - 0.5 * y) ** 2 + z ** 2)) / (y - z)
    return p

def get_length(x, y, z):
    d = (2 * x) * math.sin(y / (2 * x)) + z * 2
    return d

def get_arc(x, y, z):
    d = (2 * x) * math.sin(y / (2 * x)) + z * 2
    return d

def get_sagitta(x, y):
    s = x - (math.sqrt(x ** 2 - (y / 2) ** 2))
    return s

def draw_straight(width, length, filename):
    doc = ezdxf.new()
    doc.units = units.IN
    doc.header['$INSUNITS'] = units.IN
    doc.header['$MEASUREMENT'] = 0
    msp = doc.modelspace()

    start = (0,0)
    msp.add_line((start), (width, 0))
    msp.add_line((width, 0), (width, length))
    msp.add_line((width, length), (0, length))
    msp.add_line((0, length), (start))
    doc.saveas(filename)

def draw_arcs_and_connect(filename, radius1, radius2, end_angle):
    # Create a new DXF drawing
    doc = ezdxf.new()
    doc.units = units.IN
    doc.header['$INSUNITS'] = units.IN
    doc.header['$MEASUREMENT'] = 0
    # Add a new model space layout
    msp = doc.modelspace()

    # Define the center of the arcs
    center = (0, 0)

    # Define the start and end angles of the arcs
    start_angle = 0

    # Draw the first arc
    msp.add_arc(center=center, radius=radius1, start_angle=start_angle, end_angle=end_angle)

    # Calculate the start and endpoint of the first arc
    x1_start = center[0] + radius1 * math.cos(math.radians(start_angle))
    y1_start = center[1] + radius1 * math.sin(math.radians(start_angle))
    x1_end = center[0] + radius1 * math.cos(math.radians(end_angle))
    y1_end = center[1] + radius1 * math.sin(math.radians(end_angle))

    # Draw the second arc
    msp.add_arc(center=center, radius=radius2, start_angle=start_angle, end_angle=end_angle)

    # Calculate the start and endpoint of the second arc
    x2_start = center[0] + radius2 * math.cos(math.radians(start_angle))
    y2_start = center[1] + radius2 * math.sin(math.radians(start_angle))
    x2_end = center[0] + radius2 * math.cos(math.radians(end_angle))
    y2_end = center[1] + radius2 * math.sin(math.radians(end_angle))

    # Connect the starting points of the arcs with lines
    msp.add_line((x1_start, y1_start), (x2_start, y2_start))  # Connect the starting points of the arcs

    # Connect the endpoints of the arcs with lines
    msp.add_line((x1_end, y1_end), (x2_end, y2_end))  # Connect the endpoints of the arcs

    # Save the DXF file
    doc.saveas(filename)

# Start of runtime program

# Lists
nameList =          ["Name"]
qtyList =           ["QTY"]
thicknessList =     ["Thickness"]
diaList =           ["Diameter"]
circList =          ["Flat Width"]
lengthList =        ["Flat Length"]
weightList =        ["Total Weight"]
sqftList =          ["Total SQFT"]

# Loop that keeps asking for input
# Loop that keeps asking for input
while True:
        type = input("Duct type 'S' for Straight 'C' for Cone or '0' to quit:")
        if type == "0":
            break
        # Variables
        if type == 'S':
            name = getName()
            qty = getQty()       
            thickness = getThickness()       
            dia = getDia()        
            circ = dia * math.pi        
            length = getLength()        
            weight = getStraightWeight(length, circ, thickness, qty)
            sqft = getStraightSqft(length, circ, qty)        
            
            # Debug print statements
            print("Appending Straight duct values to lists:")
            print("Name:", name)
            print("Qty:", qty)
            print("Thickness:", thickness)
            print("Diameter:", dia)
            print("Length:", length)
            print("Weight:", weight)
            print("SQFT:", sqft)
            
            # Adding variables to lists 
            nameList.append(name)
            qtyList.append(qty)
            thicknessList.append(thickness)
            diaList.append(dia)
            circList.append(circ)
            lengthList.append(length)
            weightList.append(weight)
            sqftList.append(sqft)
            
            #Draw the duct
            draw_straight(circ, length, name + '.dxf')
        
        elif type == 'C':
            steel_weight = 0.2833
            name = getName()
            qty = getQty()       
            thickness = getThickness() 
            s_dia = get_small_dia()  # User input
            l_dia = get_large_dia()  # User input
            height = get_height()  # User input
            r = get_r(l_dia, s_dia, height)  # Slant height
            p = get_p(height, l_dia, s_dia)  # Flat pattern inside radius
            q = r + p  # Flat pattern outside radius (large diameter)
            l_inner_arc = 3.14 * s_dia  # Length of inner arc along perimeter
            l_outer_arc = 3.14 * l_dia  # Length of outer arc along perimeter
            a = l_inner_arc / p  # Angle in radians
            d = (a * 180) / 3.14  # Angle in degrees
            b_length = get_length(q, l_outer_arc, thickness)  # Bounding box length
            b_arc = get_arc(p, l_inner_arc, thickness)  # Bounding box arc
            sagitta = get_sagitta(p, b_arc)
            b_width = sagitta + r
            b_sqft = (b_width * b_length)/144
            b_volume = b_width * b_length * thickness
            b_weight = b_volume * steel_weight
            
            # Debug print statements
            print("Appending Cone duct values to lists:")
            print("Name:", name)
            print("Qty:", qty)
            print("Thickness:", thickness)
            print("Small Diameter:", s_dia)
            print("Large Diameter:", l_dia)
            print("Height:", height)
            print("Weight:", b_weight)
            print("SQFT:", b_sqft)
            
            # Adding variables to lists
            nameList.append(name)
            qtyList.append(qty)
            thicknessList.append(thickness)
            diaList.append(s_dia)
            circList.append(b_width)
            lengthList.append(b_length)
            weightList.append(b_weight)
            sqftList.append(b_sqft)

            #draw the duct
            draw_arcs_and_connect(name +'.dxf', p, q, d)


# Writing to CSV file
# Writing to CSV file
with open('duct_data.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    for data in zip(nameList, qtyList, thicknessList, diaList, circList, lengthList, weightList, sqftList, ):
        writer.writerow(data)

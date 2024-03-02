import csv
import math
import ezdxf

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

#start of runtime program

#lists
nameList =          ["Name"]
qtyList =           ["QTY"]
thicknessList =     ["Thickness"]
diaList =           ["Diameter"]
circList =          ["Flat Width"]
lengthList =        ["Flat Length"]
weightList =        ["Total Weight"]
sqftList =          ["Total SQFT"]

#loop that keeps asking for input
while 0 < 1 :
        type = input("Duct type or 0 to quit:")
        if type == "0":
            break
        #variables
        name = getName()
        qty = getQty()       
        thickness = getThickness()       
        dia = getDia()        
        circ = dia * math.pi        
        length = getLength()        
        weight = getStraightWeight(length, circ, thickness, qty)
        sqft = getStraightSqft(length, circ, qty)
        
        #adding variables to lists
        nameList.append(name)
        qtyList.append(qty)
        thicknessList.append(thickness)
        diaList.append(dia)
        circList.append(circ)
        lengthList.append(length)
        weightList.append(weight)
        sqftList.append(sqft)

# Writing to CSV file
with open('duct_data.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerows(zip(nameList, qtyList, thicknessList, diaList, circList, lengthList, weightList, sqftList))

# Create a DXF file for each duct
for i in range(1, len(nameList)):
    doc = ezdxf.new(dxfversion='R2010')
    msp = doc.modelspace()
    
    circ = circList[i]
    length = lengthList[i]
    
    msp.add_lwpolyline([(0, 0), (0, circ), (length, circ), (length, 0)], close=True)
    
    duct_name = nameList[i].replace(" ", "_")  # Replace spaces with underscores
    doc.saveas(f"{duct_name}.dxf")

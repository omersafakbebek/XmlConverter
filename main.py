import xml.etree.ElementTree as ET


# Get attribute definitions
def get_attribute_definitions(root):
  attribute_definitions_xml = root[0][2]
  attribute_definitions = {}
  for attribute in attribute_definitions_xml:
    id = attribute.attrib["id"]
    name = attribute[0].text
    unit = None
    type = attribute.attrib["CESAttributeType"]
    if (attribute[1].tag[47:] != "Unitless"):
      unit = attribute[1][0][0].text
    attribute_definitions[id] = (name, unit, type)
  return attribute_definitions

def set_attribute_values(bulk, attribute, attribute_definitions):
  id = attribute.attrib["attributeID"]
  name = attribute_definitions[id][0]
  type = attribute_definitions[id][2]
  format = "exponential" if type == "point" else "string"
  value = ""
  for j in range(len(attribute[0])):
    value += attribute[0][j].text + ", "
  value = value.replace("≤", "<=")
  value = value.replace("≥", ">=")
  value = value.rstrip(", ")
  property = ET.SubElement(bulk, "PropertyData")
  property.set("property", name)
  data = ET.SubElement(property, "Data")
  data.set("format", format)
  data.text = value
  
def get_records_and_convert_to_tc(root, attribute_definitions, tc_root):
  # Get records and their attributes
  records = root[1][0]
  masters = []
  # Convert attributes
  for record in records:
    attribute_values_xml = record[0]
    fullname = record.attrib["fullname"]
    basis_index = fullname.rfind(",")
    fullname_without_basis = fullname[:basis_index]
    master_index = 0
    material = ET.SubElement(tc_root, "Material")
    bulk = ET.SubElement(material, "BulkDetails")
    name = ET.SubElement(bulk, "Name")
    name.text = fullname
    if (fullname_without_basis not in masters):
      masters.append(fullname_without_basis)
      master_material = ET.SubElement(tc_root, "Material")
      master_bulk = ET.SubElement(master_material, "BulkDetails")
      master_name = ET.SubElement(master_bulk, "Name")
      master_name.text = fullname_without_basis
      for i in range(len(attribute_values_xml)):
        attribute = attribute_values_xml[i]
        id = attribute.attrib["attributeID"]
        name = attribute_definitions[id][0]
        if (name == "Statistical Basis"):
          master_index = i
          break
        set_attribute_values(master_bulk, attribute, attribute_definitions)
        set_attribute_values(bulk, attribute, attribute_definitions)
    # Set remaining basis material attributes
    for i in range(master_index , len(attribute_values_xml)):
      attribute = attribute_values_xml[i]
      set_attribute_values(bulk, attribute, attribute_definitions)
  return tc_root

def convert_definitions_to_metadata(attribute_definitions, tc_root):
  metadata = ET.SubElement(tc_root, "Metadata")
  for id in attribute_definitions:
    name = attribute_definitions[id][0]
    unit = attribute_definitions[id][1]
    detail = ET.SubElement(metadata, "PropertyDetails")
    # Set attribute id to name
    detail.set("id", name)
    detail.set("type", "")
    name_element = ET.SubElement(detail, "Name")
    name_element.text = name
    units_element = ET.SubElement(detail, "Units")
    if unit is None:
      units_element.set("name", "UNITLESS")
      ET.SubElement(units_element, "Unitless")
    else:
      units_element.set("name", unit)
      unit_element = ET.SubElement(units_element, "Unit")
      unit_name_element = ET.SubElement(unit_element, "Name")
      unit_name_element.text = unit
  return tc_root

def write_to_xml(root, filename):
  ET.indent(root)
  b_xml = ET.tostring(root)
  with open(filename, "wb") as f:
    f.write(b_xml)

def parse_and_get_root(filename):
  tree = ET.parse(filename)
  root = tree.getroot()
  return root

def convert_to_tc(root, attribute_definitions):
  tc_root = ET.Element("MatML_Doc")
  tc_root = get_records_and_convert_to_tc(root, attribute_definitions, tc_root)
  tc_root = convert_definitions_to_metadata(attribute_definitions, tc_root)
  return tc_root

if __name__ == '__main__':
  root = parse_and_get_root("3RecordsGranta.xml")
  attribute_definitions = get_attribute_definitions(root)
  tc_root = convert_to_tc(root, attribute_definitions)
  write_to_xml(tc_root, "output.xml")
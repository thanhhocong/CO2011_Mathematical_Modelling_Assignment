# src/parser.py
import xml.etree.ElementTree as ET
from petri_net import PetriNet

def parse_pnml(filename: str) -> PetriNet:
    tree = ET.parse(filename)
    root = tree.getroot()
    ns = {'pnml': 'http://www.pnml.org/version-2009/grammar/pnmlcoremodel'}

    net = PetriNet()
    net_element = root.find('.//pnml:net', ns)
    if not net_element:
        raise ValueError("No <net> found")

    # Places
    for place in net_element.findall('.//pnml:place', ns):
        pid = place.get('id')
        name_tag = place.find('pnml:name/pnml:text', ns)
        name = name_tag.text if name_tag is not None else pid
        marking_tag = place.find('pnml:initialMarking/pnml:text', ns)
        tokens = int(marking_tag.text) if marking_tag is not None else 0
        net.add_place(pid, name, tokens)

    # Transitions
    for trans in net_element.findall('.//pnml:transition', ns):
        tid = trans.get('id')
        name_tag = trans.find('pnml:name/pnml:text', ns)
        name = name_tag.text if name_tag is not None else tid
        net.add_transition(tid, name)

    # Arcs
    for arc in net_element.findall('.//pnml:arc', ns):
        source = arc.get('source')
        target = arc.get('target')
        net.add_arc(source, target)

    return net
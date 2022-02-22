from flask import Flask, request, abort
import os
import sys
import traceback
import xml.etree.ElementTree as ET
from flask.wrappers import Response

sys.path.append("/usr/lib/python3/dist-packages")
import pymol
import urllib

app = Flask(__name__, static_url_path = "", static_folder = "./")


@app.route("/status")
def status():
    return("The Visualisation Protein Structure Plugin Flask Server is up and running")


@app.route("/evaluate", methods=["POST"])
def evaluate():
    data = request.get_json(force=True)
    rdf_type = data['type']

    # uses rdf types
    #accepted_types = {'Activity', 'Agent', 'Association', 'Attachment',
    #                   'Collection', 'CombinatorialDerivation', 'Component',
    #                   'ComponentDefinition', 'Cut', 'Experiment',
    #                   'ExperimentalData', 'FunctionalComponent',
    #                   'GenericLocation', 'Implementation', 'Interaction',
    #                   'Location', 'MapsTo', 'Measure', 'Model', 'Module',
    #                   'ModuleDefinition', 'Participation', 'Plan', 'Range',
    #                   'Sequence', 'SequenceAnnotation', 'SequenceConstraint',
    #                   'Usage', 'VariableComponent'}

    accepted_types = {'Component', 'ComponentDefinition'}
    
    acceptable = rdf_type in accepted_types

    if acceptable:
        return f'The type sent ({rdf_type}) is an accepted type', 200
    else:
        return f'The type sent ({rdf_type}) is NOT an accepted type', 415


@app.route("/run", methods=["POST"])
def run():
    plugin_ip = request.headers.get('host')#'127.0.0.1'
    print("plugin_ip{}".format(plugin_ip), file=sys.stderr)
    data = request.get_json(force=True)

    print("RECEIVED: {}".format(data), file=sys.stderr)
    complete_sbol = data['complete_sbol']
    instance_url = data['instanceUrl']
    cwd = os.getcwd()
    filename = os.path.join(cwd, "result_template.html")

    try: 
        subtest_sbol_url = complete_sbol.replace('public/igem/', 'download/sbol_').replace('/1/sbol','.xml') # This is temporary.
        sbol_url = subtest_sbol_url 
       
        print("Downloading SBOL file: {}".format(sbol_url), file=sys.stderr)
        urllib.request.urlretrieve(sbol_url, "sbol.xml")

        # Parse the SBOL xml to determine pdb id
        sbol_tree=ET.parse("sbol.xml")
        sbol_root=sbol_tree.getroot()
        print("Root = {}".format(sbol_root.tag), file=sys.stderr)
        print("Attrib = {}".format(sbol_root.attrib),file=sys.stderr)

        for sbol_child in sbol_root:
            if "ComponentDefinition" in sbol_child.tag:
                for sbol_child_child in sbol_child:
                    if "pdbId" in sbol_child_child.tag:
                        print("pdb_id: {} - {}".format(sbol_child_child.tag, sbol_child_child.text),file=sys.stderr)
                        pdb_id = sbol_child_child.text.lower()


        # Download the pdb file
        pdb_url_base='https://www.ebi.ac.uk/pdbe/entry-files/download/pdb'
        pdb_file_url = pdb_url_base + pdb_id + '.ent';
        print("Downloading pdb file: {}".format(pdb_file_url), file=sys.stderr)
        urllib.request.urlretrieve(pdb_file_url, "protein.pdb")

        # Get the png image using pymol
        convert_to_png("protein.pdb")
    
        print("Created PNG file!", file=sys.stderr)

        protein_name = complete_sbol.replace(instance_url+'public/igem/', '').replace('/1/sbol', '')
        with open(filename, 'r') as htmlfile:
            result = htmlfile.read()
            result = result.replace("PLUGIN_IP", plugin_ip)
#            result = result.replace("PLUGIN_PORT", plugin_port)
            result = result.replace("PROTEIN_NAME", protein_name)
      
        print("Returning HTML: {}".format(result), file=sys.stderr)
        return result

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lnum = exc_tb.tb_lineno
        abort(400, f'Exception is: {e}, exc_type: {exc_type}, exc_obj: {exc_obj}, fname: {fname}, line_number: {lnum}, traceback: {traceback.format_exc()}')

def convert_to_png(pdb_filename):
    if os.path.exists("protein.png"):
        os.remove("protein.png")
    pymol.pymol_argv = [ 'pymol', '-qc']
    pdb_file =pdb_filename
    pdb_name =pdb_filename
    pymol.cmd.load(pdb_file, pdb_name)
    pymol.cmd.disable("all")
    pymol.cmd.enable(pdb_name)
    pymol.cmd.png("protein.png")
    pymol.cmd.delete("all")
    os.remove(pdb_filename)


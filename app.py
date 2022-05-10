from flask import Flask, request, abort
import os
import subprocess
import sys
import traceback
import xml.etree.ElementTree as ET
from flask.wrappers import Response

sys.path.append("/usr/lib/python3/dist-packages")
import pymol
import urllib
from prody import *

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
    print("plugin_ip: {}".format(plugin_ip), file=sys.stderr)
    data = request.get_json(force=True)

    print("RECEIVED: {}".format(data), file=sys.stderr)
    complete_sbol = data['complete_sbol']
    instance_url = data['instanceUrl']
    cwd = os.getcwd()
    filename = os.path.join(cwd, "result_template.html")

    data_dir = "/data"

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
            if "Sequence" in sbol_child.tag:
                for sbol_child_child in sbol_child:
                    if "elements" in sbol_child_child.tag:
                        print("elements: {} - {}".format(sbol_child_child.tag, sbol_child_child.text),file=sys.stderr)
                        sequence = sbol_child_child.text.lower()
        
        pdb_list_file = os.path.join(data_dir, "blast_pdb.txt")
        print("pdb_list_file: {}".format(pdb_list_file), file=sys.stderr)
        found_pdb_id = False
        if os.path.exists(pdb_list_file):
            f=open(pdb_list_file, 'r')
            for line in f:
                if sequence in line:
                    print("Found: {}".format(line), file=sys.stderr)
                    found_pdb_id = True
                    pdb_match_line = line
            f.close()

        if found_pdb_id:
            pdb_id = pdb_match_line.strip().split(':')[-1]
            print("pdb_id: {}".format(pdb_id), file=sys.stderr)
        else:
            blast_record=blastPDB(sequence)
            best = blast_record.getBest()
            pdb_id = best['pdb_id']
            f=open(pdb_list_file, 'w')      
            f.write(sequence + ":" + pdb_id + "\n")
            f.close()

        print("Retrieved PDB ID: {}".format(pdb_id), file=sys.stderr)

        protein_imagename = os.path.join(data_dir, "protein_"+pdb_id+".png")
        print("protein_imagename: {}".format(protein_imagename), file=sys.stderr)

        if not os.path.exists(protein_imagename):
            # Download the pdb file
            pdb_file_name = "protein_"+pdb_id+".pdb"
            pdb_url_base='https://www.ebi.ac.uk/pdbe/entry-files/download/pdb'
            pdb_file_url = pdb_url_base + pdb_id + '.ent';
            print("Downloading pdb file: {}".format(pdb_file_url), file=sys.stderr)
            urllib.request.urlretrieve(pdb_file_url, pdb_file_name)

            # Check data directory size
            data_size = subprocess.check_output(['du','-sm', data_dir]).split()[0].decode('utf-8')
            print("data_size={}".format(data_size), file=sys.stderr)
            data_files = os.listdir(data_dir)
            png_files = [os.path.join(data_dir, x) for x in data_files if x.endswith('.png')]
            if len(png_files) > 0:
                oldest_png_file = min(png_files, key=os.path.getctime)
                print("Oldest PNG file: {}".format(oldest_png_file), file=sys.stderr)

                data_limit = 1024 # MiB
                if int(data_size) >= data_limit:
                    print("Deleting oldest PNG file: {}".format(oldest_png_file), file=sys.stderr)
                    os.remove(oldest_png_file)

            # Get the png image using pymol
            convert_to_png(pdb_id)
            print("Created PNG file!", file=sys.stderr)

#        protein_name = complete_sbol.replace(instance_url+'public/igem/', '').replace('/1/sbol', '')
        with open(filename, 'r') as htmlfile:
            result = htmlfile.read()
            result = result.replace("PLUGIN_IP", plugin_ip)
            result = result.replace("PROTEIN_IMAGEFILE", protein_imagename)
      
        print("Returning HTML: {}".format(result), file=sys.stderr)

        return result

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        lnum = exc_tb.tb_lineno
        abort(400, f'Exception is: {e}, exc_type: {exc_type}, exc_obj: {exc_obj}, fname: {fname}, line_number: {lnum}, traceback: {traceback.format_exc()}')

def convert_to_png(pdb_id):
    data_dir = "/data"
    protein_imagename = os.path.join(data_dir, "protein_"+pdb_id+".png")
    pdb_file = "protein_"+pdb_id+".pdb"
    
    if not os.path.exists(protein_imagename):
        print("Converting PDB to PNG ... {}".format(protein_imagename), file=sys.stderr)
        pymol.pymol_argv = [ 'pymol', '-qc']
        pdb_name = "protein_"+pdb_id+".pdb"   
        pymol.cmd.load(pdb_file, pdb_name)
        pymol.cmd.disable("all")
        pymol.cmd.enable(pdb_name)
        pymol.cmd.png(protein_imagename)
        pymol.cmd.delete("all")

    os.remove(pdb_file)


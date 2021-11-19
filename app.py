from flask import Flask, request, abort
import os
import sys
import traceback
import pymol
import urllib

app = Flask(__name__, static_url_path = "", static_folder = "./")


@app.route("/status")
def status():
    return("The Visualisation Test Plugin Flask Server is up and running")


@app.route("/evaluate", methods=["POST"])
def evaluate():
    data = request.get_json(force=True)
    rdf_type = data['type']

    # ~~~~~~~~~~~~ REPLACE THIS SECTION WITH OWN RUN CODE ~~~~~~~~~~~~~~~~~~~
    # uses rdf types
    accepted_types = {'Activity', 'Agent', 'Association', 'Attachment',
                      'Collection', 'CombinatorialDerivation', 'Component',
                      'ComponentDefinition', 'Cut', 'Experiment',
                      'ExperimentalData', 'FunctionalComponent',
                      'GenericLocation', 'Implementation', 'Interaction',
                      'Location', 'MapsTo', 'Measure', 'Model', 'Module',
                      'ModuleDefinition', 'Participation', 'Plan', 'Range',
                      'Sequence', 'SequenceAnnotation', 'SequenceConstraint',
                      'Usage', 'VariableComponent'}

    acceptable = rdf_type in accepted_types

    # # to ensure it shows up on all pages
    # acceptable = True
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~ END SECTION ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    if acceptable:
        return f'The type sent ({rdf_type}) is an accepted type', 200
    else:
        return f'The type sent ({rdf_type}) is NOT an accepted type', 415


@app.route("/run", methods=["POST"])
def run():
    print("In Plugin!!!")
    data = request.get_json(force=True)

    top_level_url = data['top_level']
    complete_sbol = data['complete_sbol']
    instance_url = data['instanceUrl']
    size = data['size']
    rdf_type = data['type']
    shallow_sbol = data['shallow_sbol']

    url = complete_sbol.replace('/sbol', '')

    cwd = os.getcwd()
    filename = os.path.join(cwd, "Test.html")

    #pdb_filename=["4ogs.pdb", "6hl7.pdb"]
    #pdb_file_id = int(size)
    #convert_to_png(pdb_filename[pdb_file_id])
    pdb_links={'https://dev.synbiohub.org/public/igem/gfp/1':'https://files.rcsb.org/download/4OGS.pdb', 'https://dev.synbiohub.org/public/igem/aTc/1':'https://files.rcsb.org/download/6HL7.pdb'}
    print("Downloading pdb file: {}".format(pdb_links[url]))
    urllib.request.urlretrieve(pdb_links[url], "protein.pdb")

    convert_to_png("protein.pdb")
    
    print("Created PNG file!")
    try:
        with open(filename, 'r') as htmlfile:
            result = htmlfile.read()
      
        print(result,file=sys.stderr)
        print("Returning HTML")
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
    #pymol.finish_launching()
    pdb_file =pdb_filename
    pdb_name =pdb_filename
    #pdb_file ="4ogs.pdb"
    #pdb_name ="4ogs_pdb"
    pymol.cmd.load(pdb_file, pdb_name)
    pymol.cmd.disable("all")
    pymol.cmd.enable(pdb_name)
    pymol.cmd.png("protein.png")
    pymol.cmd.delete("all")
    os.remove(pdb_filename)


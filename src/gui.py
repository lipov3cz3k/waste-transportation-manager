import logging
from flask import Flask, request, redirect, url_for, render_template, jsonify

from common.config import ftp_config, local_config
from graph.api import getOSMList, getGraphList, loadGraph, getImportList
from graph.bounding_box import BoundingBox
from common.utils import get_float_coord, CheckFolders
from web.long_task_threads import DDR_thread, GRAPH_thread, GRAPH_update_thread

logger = logging.getLogger(__name__)


######################################## FLASK APPLICATION INITIALIZATION #############################################
class WebApplication(Flask):

   def __init__(self, *args, **kwargs):
            super(WebApplication, self).__init__(*args, **kwargs)

            self.thread = None
            self.thread_name = ""
            self.graph_pool = []
            CheckFolders()

app = WebApplication(__name__, static_folder="web/static", template_folder="web/templates")


########################################################################################################################

######################################## METHODS FOR RUN LONG TASK #####################################################
@app.route('/ddr/run', methods=['POST'])
def run_ddr():
    if app.thread and app.thread.isAlive():
        # something already running
        return jsonify("")
    elif app.thread and not app.thread.isAlive():
        app.thread = None
        app.thread_name = ""

    app.thread = DDR_thread()
    app.thread_name = "DDR"
    app.thread.start()

    return jsonify("")

@app.route('/graph/run', methods=['POST'])
def run_graph():
    if request.method == 'POST':
        if request.form['submit'] == 'start':
            if app.thread and app.thread.isAlive():
                # something already running
                if request.referrer:
                    return redirect(request.referrer)
                else:
                    return redirect(url_for('index'))
            elif app.thread and not app.thread.isAlive():
                app.thread = None
                app.thread_name = ""

            longitude = (
                get_float_coord(request.form.get('longitude-min', None)),
                get_float_coord(request.form.get('longitude-max', None))
            )

            latitude = (
                get_float_coord(request.form.get('latitude-min', None)),
                get_float_coord(request.form.get('latitude-max', None))
            )

            region_id = request.form.get('regionId', None)

            #if (not longitude[0] or not longitude[1] or not latitude[0] or not latitude[1]) or not region_id:
            if not region_id:
                if request.referrer:
                    return redirect(request.referrer)
                else:
                    return redirect(url_for('index'))

            if region_id:
                logger.info(region_id)
                app.thread = GRAPH_thread(region_id=region_id, graph_pool=app.graph_pool)
            else:
                bbox = BoundingBox(longitude[0], latitude[0], longitude[1], latitude[1])
                app.thread = GRAPH_thread(bbox=bbox, graph_pool=app.graph_pool, processCitiesMap=True)
            app.thread_name = "GRAPH"
            app.thread.start()

    if request.referrer:
        return redirect(request.referrer)
    else:
        return redirect(url_for('index'))


@app.route('/graph/<graphID>/update', methods=['POST'])
def graphUpdate(graphID):
    if request.method == 'POST':
        if request.form['ddr'] == 'update':
            if app.thread and app.thread.isAlive():
                # something already running
                if request.referrer:
                    return redirect(request.referrer)
                else:
                    return redirect(url_for('index'))
            elif app.thread and not app.thread.isAlive():
                app.thread = None
                app.thread_name = ""

            app.thread = GRAPH_update_thread(graphID, app.graph_pool)
            app.thread_name = "GRAPH-Update"
            app.thread.start()

    return redirect(url_for('index'))


@app.route('/stop', methods=['POST', 'GET'])
def stop():
    if app.thread:
        if app.thread.isAlive():
            app.thread.stop()
            app.thread.join()
        app.thread = None
        app.thread_name = ""

    if request.referrer:
        return redirect(request.referrer)
    else:
        return redirect(url_for('index'))

@app.route('/status', methods=['POST', 'GET'])
def status():
    if app.thread and app.thread.isAlive():
        status = app.thread.status()
        status['thread_name'] = app.thread_name
        return jsonify(status)
    elif app.thread and not app.thread.isAlive():
        app.thread = None
        app.thread_name = ""

    status = {'action':"none", 'percentage':0, 'thread_name':'none'}
    return jsonify(status)
########################################################################################################################

######################################## GRAPH OPERATIONS ##############################################################
@app.route('/graph/list')
def graphGetList():
    logger.info("graphGetList")
    return jsonify(graphs=getGraphList())

def _graphGetAttributes(graphID):
    graph = loadGraph(app.graph_pool, graphID)
    return {"hasCitiesMap":graph.has_city_graph()}

@app.route('/graph/<graphID>/nodes')
def graphGetNodes(graphID):
    graph = loadGraph(app.graph_pool, graphID)
    return str(graph.get_nodes_geojson())

@app.route('/graph/<graphID>/<suffix>/list')
def graphGetPaths(graphID, suffix):
    return jsonify(paths=getImportList(graphID, suffix))

@app.route('/graph/<graphID>/edges-containers')
def graphGetEdgesWithContainers(graphID):
    graph = loadGraph(app.graph_pool, graphID)
    return str(graph.get_edges_with_containers())

@app.route('/graph/<graphID>/containers', methods=['POST', 'GET'], defaults={'n1': None, 'n2': None})
@app.route('/graph/<graphID>/containers/<n1>/<n2>', methods=['GET'])
def graphGetContainers(graphID, n1, n2):
    graph = loadGraph(app.graph_pool, graphID)
    if request.method == 'POST':
        n1 = request.form['n1']
        n2 =  request.form['n2']
    return jsonify(graph.get_containers_geojson(n1, n2))

@app.route('/graph/<graphID>/container/details', methods=['POST'])
def graphGetContainerDetails(graphID):
    if request.method == 'POST':
        id = request.form['id']
        graph = loadGraph(app.graph_pool, graphID)
        details = graph.GetContainerDetails(id)
        return jsonify(**details)
    return redirect(url_for('graphDetail', graphID=graphID))

@app.route('/graph/<graphID>/edges')
def graphGetEdges(graphID):
    graph = loadGraph(app.graph_pool, graphID)
    return str(graph.get_edges())

@app.route('/graph/<graphID>/edge/details', methods=['POST'])
def graphGetEdgeDetails(graphID):
    if request.method == 'POST':
        n1 = request.form['n1']
        n2 =  request.form['n2']
        graph = loadGraph(app.graph_pool, graphID)
        details = graph.get_edge_details(n1, n2)
        return jsonify(**details)
    return redirect(url_for('graphDetail', graphID=graphID))

@app.route('/graph/<graphID>/pathFromFile', methods=['POST'])
def graphGetPathFromFile(graphID):
    if request.method == 'POST':
        pathID = request.form['pathID']
        graph = loadGraph(app.graph_pool, graphID)
        return jsonify(graph.get_path_from_file_geojson(pathID))
    return redirect(url_for('graphDetail', graphID=graphID))

@app.route('/graph/<graphID>/updateFrequencyFile', methods=['POST'])
def graphUpdateFrequencyFile(graphID):
    if request.method == 'POST':
        fileName = request.form['fileName']
        graph = loadGraph(app.graph_pool, graphID)
        return jsonify(graph.LoadAndFillFrequecy(fileName))
    return redirect(url_for('graphDetail', graphID=graphID))

############################ Export ################

@app.route('/graph/<graphID>/export/simple', methods=['POST', 'GET'])
def graphExportSimple(graphID):
    graph = loadGraph(app.graph_pool, graphID)
    return str(graph.ExportSimple())

@app.route('/graph/<graphID>/export/containers', methods=['POST', 'GET'])
def graphExportContainers(graphID):
    graph = loadGraph(app.graph_pool, graphID)
    return str(graph.ExportConainers())

@app.route('/graph/<graphID>/export/tracks', methods=['POST', 'GET'])
def graphExportTracks(graphID):
    graph = loadGraph(app.graph_pool, graphID)
    return str(graph.ExportTracksWithPaths())

@app.route('/graph/<graphID>/export/showCitiesMap', methods=['POST', 'GET'])
def graphSaveAndShowCitiesMap(graphID):
    graph = loadGraph(app.graph_pool, graphID)
    return str(graph.SaveAndShowCitiesMap())

@app.route('/graph/<graphID>/export/cityDistanceMatrix', methods=['POST', 'GET'])
def graphExportCityDistanceMatrix(graphID):
    graph = loadGraph(app.graph_pool, graphID)
    return str(graph.ExportCityDistanceMatrix())


############################
@app.route('/graph/<graphID>/affected')
def graphGetAffectedEdges(graphID):
    graph = loadGraph(app.graph_pool, graphID)
    return str(graph.GetAffectedEdges())

@app.route('/graph/<graphID>/path', methods=['POST', 'GET'], defaults={'startId': None, 'endId': None})
@app.route('/graph/<graphID>/path/<startId>/<endId>', methods=['GET'])
def graphGetSortestPath(graphID, startId, endId):
    if request.method == 'POST':
        if request.form['submit'] == 'start':
            startId = request.form['start']
            endId = request.form['end']


    graph = loadGraph(app.graph_pool, graphID)
    path = graph.route_by_nodeId(startId, endId)
    return jsonify(**path)

@app.route('/graph/<graphID>/restrictions', methods=['POST', 'GET'])
def graphRestrictions(graphID):
    from ddr.restrictions import LoadFromFile, ExportGeoJSON
    from os.path import join
    fileName = join(local_config.folder_restrictions_root, 'Barier_All_pro Vlastika_fin.xlsx')
    return jsonify(ExportGeoJSON(LoadFromFile(fileName)))


########################################################################################################################

######################################## PAGES HANDLERS ################################################################
@app.route('/')
def index():
    return render_template('pages/app.html', osmList=getOSMList())

@app.route('/graph/')
def graphList():
    return render_template('pages/graphList.html', graphList=getGraphList())

@app.route('/graph/<graphID>')
def graphDetail(graphID):
    coords = graphID.split("_")[1:-1]
    graph = loadGraph(app.graph_pool, graphID)

    return render_template('pages/graphWTM.html', graphID=graphID, bbox=graph.get_bounding_box(), paths=getImportList(graphID, 'path'), frequencies=getImportList(graphID, 'freq'), attributes=_graphGetAttributes(graphID))

@app.route('/contact', methods=['POST', 'GET'])
def contact():
    return render_template('pages/contact.html')

@app.route('/settings')
def settings():
    local_config_members = {key:value for key, value in local_config.__dict__.items() if not key.startswith('__') and not callable(key)}
    ftp_config_members = {key:value for key, value in ftp_config.__dict__.items() if not key.startswith('__') and not callable(key) and key != 'password'}

    return render_template('pages/settings.html', local_config_members=local_config_members, ftp_config_members=ftp_config_members)

########################################################################################################################

@app.route('/update')
def gitUpdate():
    from os import system
    result = system("git pull")
    return str(result);


if __name__ == '__main__':
    from argparse import ArgumentParser

    logging.basicConfig(
        format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
        handlers=[
            logging.FileHandler("{0}/{1}.log".format(local_config.folder_log_files, local_config.log_filename)),
            logging.StreamHandler()
        ],
        level=logging.INFO)
    logging.info('Started')

    parser = ArgumentParser(description='Waste transportation manager ...')
    parser.add_argument("-r", "--release",
                        action="store_true", dest="release_config", default=None,
                        help="Disable debugging and set visiblity to 0.0.0.0:5432")
    args = parser.parse_args()
        # Load default config and override config from an environment variable
    if args.release_config:
        app.config.update(dict(
            DEBUG=False,
            SECRET_KEY='development key secret'
        ))
    else:
        app.config.update(dict(
            DEBUG=True,
            SECRET_KEY='development key secret'
        ))
    app.run(host='0.0.0.0')
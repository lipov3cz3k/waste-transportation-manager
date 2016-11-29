from flask import Flask, request, redirect, url_for, render_template, jsonify

from common.config import ftp_config, local_config
from graph.api import getOSMList, getGraphList, loadGraph, getPathsList
from graph.bounding_box import BoundingBox
from common.utils import get_float_coord, CheckFolders
from web.long_task_threads import DDR_thread, GRAPH_thread, GRAPH_update_thread


######################################## FLASK APPLICATION INITIALIZATION #############################################
class WebApplication(Flask):

   def __init__(self, *args, **kwargs):
            super(WebApplication, self).__init__(*args, **kwargs)

            self.thread = None
            self.thread_name = ""
            self.graph_pool = []
            CheckFolders()

app = WebApplication(__name__, static_folder="web/static", template_folder="web/templates")


# Load default config and override config from an environment variable
app.config.update(dict(
    DEBUG=True,
    SECRET_KEY='development key secret'
))
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

            if not longitude[0] or not longitude[1] or not latitude[0] or not latitude[1]:
                if request.referrer:
                    return redirect(request.referrer)
                else:
                    return redirect(url_for('index'))

            bbox = BoundingBox(longitude[0], latitude[0], longitude[1], latitude[1])

            app.thread = GRAPH_thread(bbox, app.graph_pool)
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
    return jsonify(graphs=getGraphList())

@app.route('/graph/<graphID>/nodes')
def graphGetNodes(graphID):
    graph = loadGraph(app.graph_pool, graphID)
    return str(graph.GetNodesGeoJSON())

@app.route('/graph/<graphID>/path/list')
def graphGetPaths(graphID):
    return jsonify(paths=getPathsList(graphID))

@app.route('/graph/<graphID>/edges-containers')
def graphGetEdgesWithContainers(graphID):
    graph = loadGraph(app.graph_pool, graphID)
    return str(graph.GetEdgesWithContainers())

@app.route('/graph/<graphID>/containers', methods=['GET','POST'])
def graphGetContainers(graphID):
    graph = loadGraph(app.graph_pool, graphID)
    n1 = n2 = None
    if request.method == 'POST':
        n1 = request.form['n1']
        n2 =  request.form['n2']
    return str(graph.GetContainersGeoJSON(n1, n2))

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
    return str(graph.GetEdges())

@app.route('/graph/<graphID>/edge/details', methods=['POST'])
def graphGetEdgeDetails(graphID):
    if request.method == 'POST':
        n1 = request.form['n1']
        n2 =  request.form['n2']
        graph = loadGraph(app.graph_pool, graphID)
        details = graph.GetEdgeDetails(n1, n2)
        return jsonify(**details)
    return redirect(url_for('graphDetail', graphID=graphID))

@app.route('/graph/<graphID>/pathFromFile', methods=['POST'])
def graphGetPathFromFile(graphID):
    if request.method == 'POST':
        pathID = request.form['pathID']
        graph = loadGraph(app.graph_pool, graphID)
        return jsonify(graph.LoadPath(pathID))
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

############################
@app.route('/graph/<graphID>/affected')
def graphGetAffectedEdges(graphID):
    graph = loadGraph(app.graph_pool, graphID)
    return str(graph.GetAffectedEdges())

@app.route('/graph/<graphID>/path', methods=['POST', 'GET'])
def graphGetSortestPath(graphID):
    if request.method == 'POST':
        if request.form['submit'] == 'start':
            startId = request.form['start']
            endId = request.form['end']
            routingType = int(request.form['routingType'])
            season = request.form['season']
            dayTime = request.form['dayTime']
            graph = loadGraph(app.graph_pool, graphID)
            path = graph.Route(startId, endId, routingType, season, dayTime)
            return jsonify(**path)
    return redirect(url_for('graphDetail', graphID=graphID))

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
    return render_template('pages/graphDetail.html', graphID=graphID, bbox=coords, paths=getPathsList(graphID))

@app.route('/contact', methods=['POST', 'GET'])
def contact():
    return render_template('pages/contact.html')

@app.route('/settings')
def settings():
    local_config_members = {key:value for key, value in local_config.__dict__.items() if not key.startswith('__') and not callable(key)}
    ftp_config_members = {key:value for key, value in ftp_config.__dict__.items() if not key.startswith('__') and not callable(key) and key != 'password'}

    return render_template('pages/settings.html', local_config_members=local_config_members, ftp_config_members=ftp_config_members)

########################################################################################################################



if __name__ == '__main__':
    app.run()
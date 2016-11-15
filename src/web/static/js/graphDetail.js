var map, bounds, affectedEdges, containers
var pathsLayer = []

function init(bounds) {
    bounds = bounds

    ///////// Map box ///////////
    // More maps can be found here: http://leaflet-extras.github.io/leaflet-providers/preview/
    tiles = L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors, Points &copy 2012 LINZ'
    });
    map = L.map('map', {layers: [tiles]});
    affectedEdges = null;


    ///////// Trigger zoomed event ///////////
    map.fitBounds(bounds);
}

///////// Crossroads loader ///////////
function loadCrossroads(apiURL, iconURL) {
    var markers = L.markerClusterGroup({ spiderfyOnMaxZoom: false, disableClusteringAtZoom: 17 });
    map.addLayer( markers );

    map.spin(true);
    $.ajax({
        type: 'GET',
        dataType: 'json',
        url: apiURL,
        success: function(data) {
            var iconUrl = L.icon({ iconUrl: iconURL })
            features = data.features
            for (var i = 0; i < features.length; i++) {
                var a = features[i];
                var id = a.id;
                var marker = L.marker(new L.LatLng(a.geometry.coordinates[1], a.geometry.coordinates[0]), { id: id, icon: iconUrl });
                markers.addLayer(marker);
            }
            markers.on('click', function (a) {
                if($("#end").val())
                {
	                $("#start").val("");
	                $("#end").val("");
                }
                if(!$("#start").val())
	                $("#start").val(a.layer.options.id);
                else
	                $("#end").val(a.layer.options.id);
            });
            map.spin(false);
        },
        error: function(e) {
            alert('Unexpected error! Cannot load graph nodes');
            map.spin(false);
        }
    });
}


///////// Containers loader ///////////
function loadContainers(containersAPIUrl, containerAPIUrl, containerDetailApi, iconURL) {
    containers = L.markerClusterGroup();
    map.addLayer(containers);

    map.spin(true);
    $.ajax({
        type: 'GET',
        dataType: 'json',
        url: containersAPIUrl,
        success: function(data) {
            var iconUrl = L.icon({ iconUrl: iconURL})
            edgesWithContainers = L.geoJson(data, {
                pointToLayer : function(feature, latlng) {
                    return L.marker(latlng, {icon: iconUrl});
                },
                onEachFeature: loadEdgeContainers,
                containerApi: containerAPIUrl,
                containerDetailApi: containerDetailApi
            }).addTo(map);
            map.spin(false);
        },
        error: function(e) {
            alert('Unexpected error! Cannot load street with containers');
            map.spin(false);
        }
    });
}

function loadEdgeContainers(feature, layer) {
        layer.on('click', function(e) {
            var n1 = e.target.feature.properties.n1;
            var n2 = e.target.feature.properties.n2;
            $.ajax({
                type: 'POST',
                data: {'n1': n1, 'n2': n2},
                dataType: 'json',
                url: layer.options.containerApi,
                success: function(data) {
                    map.removeLayer(containers)
                    containers = L.geoJson(data, {
                        pointToLayer: layer.options.pointToLayer,
                        onEachFeature: containerPopup,
                        containerDetailApi: layer.options.containerDetailApi
                    }).addTo(map);
                    map.spin(false);
                },
                error: function(e) {
                    alert('Unexpected error! Cannot load edge detail ' . e);
                }
            });
        });
}

function containerPopup(feature, layer) {
    if (feature.properties){
        apiURL = this.containerDetailApi;
        l = layer.bindPopup("Loading...", {maxWidth: 600, maxHeight: 400, className: 'map-popup'});
        l.on('click', function(e) {
            var popup = e.target._popup;
            popup.setContent("Loading...");
            popup.update();
            var container_id = e.target.feature.id;
            $.ajax({
                type: 'POST',
                data: {'id': container_id},
                dataType: 'json',
                url: apiURL,
                success: function(data) {

                    var containersHTML = ""
                    for (container of data.containers)
                        containersHTML += parse('<li><b>%s %s, %s</b>, %s, %s, %s, %s</li>', container.street, container.house_number, container.city, container.waste_name, container.container_type, container.interval, container.days);


                    var contentHTML = parse('<ul>%s</ul>', containersHTML);
                    popup.setContent(contentHTML);
                    popup.update();
                },
                error: function(e) {
                    alert('Unexpected error! Cannot load edge detail ' . e);
                }
            });
        });
    }
        
}


///////// Path loader ///////////
function wastePath(apiURL, pathID)
{
        $.ajax({
            type: 'POST',
            data: {'pathID': pathID},
            dataType: 'json',
            url: apiURL,
            success: function(data) {
                if(data.succeded)
                {
                    paths_pool = data.paths;
                    path = L.geoJson(paths_pool, {
                        style: function(feature) { return {color: 'red'};}
                    }).addTo(map);
                    pathsLayer.push(path);
                }
                else
                {
                    alert(data.message.toString());
                }
                map.spin(false);
            },
            error: function(e) {
                alert('Unexpected error! Cannot get path');
                map.spin(false);
            }
        });    
}

function removeAllPaths() {
    for (path of pathsLayer)
    {
        map.removeLayer(path);
    }
    pathsLayer.length = 0;
    $("#foundPaths tbody").empty();
}


///////// Export ///////////
function exportGraph(type) {
    // send ajax POST request to start background job
    $.ajax({
        type: 'POST',
        url: type,
        success: function () {
            alert('DONE! Look to export folder.');
        },
        error: function () {
            alert('Unexpected error');
        }
    });
}
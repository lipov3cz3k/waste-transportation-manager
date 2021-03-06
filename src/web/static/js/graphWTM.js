﻿var map, bounds, crossroads;
var pathsLayer = [];
var containers = L.layerGroup();
var overlayMaps;
var overlayPaths;
var allContainersBtn;
function init(bounds) {
    bounds = bounds

    ///////// Map box ///////////
    // More maps can be found here: http://leaflet-extras.github.io/leaflet-providers/preview/
    var OpenStreetMap_Mapnik = L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    });
    map = L.map('map', { layers: [OpenStreetMap_Mapnik], preferCanvas: true });

    overlayMaps = L.control.layers(null, null, { collapsed: false }).addTo(map);
    overlayPaths = L.control.layers(null, null, { collapsed: false });

    ///////// Trigger zoomed event ///////////
    map.fitBounds(bounds);
}


function saveMapPNG()
{
    var crossLayerEnabled = false;
    if (map.hasLayer(crossroads)) {
        crossLayerEnabled = true
        map.removeLayer(crossroads);
    }
    map.spin(true);
    leafletImage(map, doImage);
    if (crossLayerEnabled)
        map.addLayer(crossroads);
}

function doImage(err, canvas) {
    var img = document.createElement('img');
    var dimensions = map.getSize();
    img.width = dimensions.x;
    img.height = dimensions.y;
    img.src = canvas.toDataURL("image/png");
    var w = window.open('about:blank', 'image from canvas');
    w.document.body.appendChild(img);
    map.spin(false);
}

function addAllContainersButton(containerAPIUrl, containerDetailApi, iconURLs)
{
    allContainersBtn = L.easyButton('fa-trash-o', function (btn, map) {
        loadAllContainers(containerAPIUrl, containerDetailApi, iconURLs);
    }, { position: 'topright' }).addTo(map);
}

///////// Crossroads loader ///////////
function preloadCrossroads(apiURL, iconURL) {
    crossroads = L.markerClusterGroup({ spiderfyOnMaxZoom: false, disableClusteringAtZoom: 17 });
    overlayMaps.addOverlay(crossroads, "Crossroads");

    map.spin(true);
    $.ajax({
        type: 'GET',
        dataType: 'json',
        url: apiURL,
        success: function (data) {
            var iconUrl = L.icon({ iconUrl: iconURL })
            features = data.features
            for (var i = 0; i < features.length; i++) {
                var a = features[i];
                var id = a.id;
                var marker = L.marker(new L.LatLng(a.geometry.coordinates[1], a.geometry.coordinates[0]), { id: id, icon: iconUrl });
                crossroads.addLayer(marker);
            }
            crossroads.on('click', function (a) {
                if ($("#end").val()) {
                    $("#start").val("");
                    $("#end").val("");
                }
                if (!$("#start").val())
                    $("#start").val(a.layer.options.id);
                else
                    $("#end").val(a.layer.options.id);
            }).addTo(map);
            map.spin(false);
        },
        error: function (e) {
            alert('Unexpected error! Cannot load graph nodes');
            map.spin(false);
        }
    });
}

///////// Restrictions loader ///////////
function preloadRestrictions(apiUrl) {
    map.spin(true);
    $.ajax({
        type: 'POST',
        dataType: 'json',
        url: apiUrl,
        success: function (geojson) {


            var geojsonMarkerOptions = {
                radius: 8,
                fillColor: "blue",
                color: "#000",
                weight: 1,
                opacity: 1,
                fillOpacity: 0.8
            };

            restrictions = L.geoJSON(geojson, {
                pointToLayer: function (feature, latlng) {
                    return L.circleMarker(latlng, geojsonMarkerOptions);
                },
                onEachFeature: function (feature, layer) { layer.bindPopup("no:" + feature.id); }
            });

            overlayMaps.addOverlay(restrictions, "Restrictions");

            map.spin(false);
        },
        error: function (e) {
            alert('Unexpected error! Cannot load restriction file.');
            map.spin(false);
        }
    });
}

///////// Containers loader ///////////

function preloadEdgesWithContainers(containersAPIUrl, containerAPIUrl, containerDetailApi, iconURLs) {
    map.spin(true);
    $.ajax({
        type: 'GET',
        dataType: 'json',
        url: containersAPIUrl,
        success: function (data) {
            var iconDefaultUrl = iconURLs[0]
            var iconSkoUrl = iconURLs[1]
            var iconBioUrl = iconURLs[2]
            var iconPlastUrl = iconURLs[3]
            var iconSkloUrl = iconURLs[4]
            var iconPapirUrl = iconURLs[5]
            edgesWithContainers = L.geoJson(data, {
                onEachFeature: loadEdgeContainersClick,
                containerApi: containerAPIUrl,
                containerDetailApi: containerDetailApi,
                iconDefault: L.icon({ iconUrl: iconDefaultUrl }),
                iconSko: L.icon({ iconUrl: iconSkoUrl }),
                iconBio: L.icon({ iconUrl: iconBioUrl }),
                iconPlast: L.icon({ iconUrl: iconPlastUrl }),
                iconSklo: L.icon({ iconUrl: iconSkloUrl }),
                iconPapir: L.icon({ iconUrl: iconPapirUrl }),
            }).addTo(map);
            overlayMaps.addOverlay(edgesWithContainers, "Edges with containers");
            map.spin(false);
        },
        error: function (e) {
            alert('Unexpected error! Cannot load street with containers');
            map.spin(false);
        }
    });
}

function loadAllContainers(containerAPIUrl, containerDetailApi, iconURLs) {
    map.spin(true);
    var options = {
        iconDefault: L.icon({ iconUrl: iconURLs[0] }),
        iconSko: L.icon({ iconUrl: iconURLs[1] }),
        iconBio: L.icon({ iconUrl: iconURLs[2] }),
        iconPlast: L.icon({ iconUrl: iconURLs[3] }),
        iconSklo: L.icon({ iconUrl: iconURLs[4] }),
        iconPapir: L.icon({ iconUrl: iconURLs[5] }),
    }
    if (map.hasLayer(containers))
        map.removeLayer(containers)
    loadEdgeContainers(null, null, containerAPIUrl, containerDetailApi, options);
    allContainersBtn.disable();
}

function loadEdgeContainersClick(feature, layer) {
    layer.on('click', function (e) {
        map.spin(true);
        var n1 = e.target.feature.properties.n1;
        var n2 = e.target.feature.properties.n2;
        loadEdgeContainers(n1, n2, layer.options.containerApi, layer.options.containerDetailApi, e.target.options);
        map.addLayer(containers);
        allContainersBtn.enable();
    });
}

function loadEdgeContainers(n1, n2, containerAPIUrl, containerDetailApi, options) {
    containers.eachLayer(function (layer) {
        overlayMaps.removeLayer(layer);
        if (map.hasLayer(layer)) {
            map.removeLayer(layer);
        }
    });
    containers.clearLayers();

    $.ajax({
        type: 'POST',
        data: { 'n1': n1, 'n2': n2 },
        dataType: 'json',
        url: containerAPIUrl,
        success: function (data) {
            for (waste_code in data)
            {
                container_layer = L.geoJson(data[waste_code], {
                    pointToLayer: function (feature, latlng) {
                        switch (feature.properties.waste_code) {
                            case 200101: // Papír a lepenka
                                return L.marker(latlng, { icon: options.iconPapir });
                            case 200102: // Sklo
                                return L.marker(latlng, { icon: options.iconSklo });
                            case 200139: // Plasty
                                return L.marker(latlng, { icon: options.iconPlast });
                            case 200201: // Biologicky rozložitelný odpad
                                return L.marker(latlng, { icon: options.iconBio });
                            case 200301: //Směsný komunální odpad
                                return L.marker(latlng, { icon: options.iconSko });
                            default:
                                return L.marker(latlng, { icon: options.iconDefault });
                        }
                    },
                    onEachFeature: containerPopup,
                    containerDetailApi: containerDetailApi
                });
                containers.addLayer(container_layer);
                overlayMaps.addOverlay(container_layer,  waste_code + " - " + data[waste_code].features.length );
            }
            map.spin(false);
        },
        error: function (e) {
            alert('Unexpected error! Cannot load edge detail '.e);
        }
    });
}

function containerPopup(feature, layer) {
    if (feature.properties) {
        apiURL = this.containerDetailApi;
        l = layer.bindPopup("Loading...", { maxWidth: 600, maxHeight: 400, className: 'map-popup' });
        l.on('click', function (e) {
            var popup = e.target._popup;
            popup.setContent("Loading...");
            popup.update();
            var container_id = e.target.feature.id;
            $.ajax({
                type: 'POST',
                data: { 'id': container_id },
                dataType: 'json',
                url: apiURL,
                success: function (data) {

                    var containersHTML = ""
                    for (container of data.containers)
                        containersHTML += parse('<li>(%s)<b>%s %s, %s</b>, %s, %s, %s, %s</li>', container.id, container.street, container.house_number, container.city, container.waste_name, container.container_type, container.interval, container.days);


                    var contentHTML = parse('<ul>%s</ul>', containersHTML);
                    popup.setContent(contentHTML);
                    popup.update();
                },
                error: function (e) {
                    alert('Unexpected error! Cannot load edge detail '.e);
                }
            });
        });
    }

}

///////// Wastepath loader ///////////

function preloadAllWastePath(apiUrl, paths) {
    for (key in paths) {
        wastePath(apiUrl, paths[key]);
    }
    if (paths.length) {
        overlayPaths.addTo(map);
    }
}

function wastePath(apiURL, pathID) {
    $.ajax({
        type: 'POST',
        data: { 'pathID': pathID },
        dataType: 'json',
        url: apiURL,
        success: function (data) {
            if (data.succeded) {
                paths_pool = data.paths;
                path = L.geoJson(paths_pool, {
                    style: function (feature) { return feature.style; }
                });
                overlayPaths.addOverlay(path, data.name);
            }
            else {
                alert(data.message.toString());
            }
            map.spin(false);
        },
        error: function (e) {
            alert('Unexpected error! Cannot get path');
            map.spin(false);
        }
    });
}

/////// Frequency files /////////

function updateFrequencyFile(apiURL, fileName) {
    $.ajax({
        type: 'POST',
        data: { 'fileName': fileName },
        dataType: 'json',
        url: apiURL,
        success: function (data) {
            if (data.succeded) {
                alert('DONE!');
            }
            else {
                alert(data.message.toString());
            }
            map.spin(false);
        },
        error: function (e) {
            alert('Unexpected error!');
            map.spin(false);
        }
    });

}


///////// Path loader ///////////
var blueLineColors = ["#00001A", "#00004D", "#000080", "#0000CC", "#001AE6", "#0033FF", "#3366FF", "#7FB2FF", "#B3E6FF", "#E5FFFF"];
var yellowLineColors = ["#E3EE68", "#FCFF81", "#FFFF9B", "#FFFFB5", "#000900", "#172200", "#313C00", "#646F00", "#B0BB35", "#CAD54F"];
var greenLineColors = ["#03B00B", "#1DCA25", "#36E33E", "#50FD58", "#69FF71", "#82FF8A", "#9CFFA4", "#B6FFBE", "#CFFFD7", "#E8FFF0"];

function removeAllPaths() {
    for (path of pathsLayer)
    {
        map.removeLayer(path);
    }
    pathsLayer.length = 0;
    $("#foundPaths tbody").empty();
}


function dijkstraPath(apiUrl, startInputID, endInputID, routingTypeInputID, seasonInputID, dayTimeInputID) {
    start = $("#" + startInputID).val();
    end = $("#" + endInputID).val();
    routingType = $('#' + routingTypeInputID + ' input:radio:checked').val();
    season = $('#' + seasonInputID + ' input:radio:checked').val();
    dayTime = $('#' + dayTimeInputID + ' input:radio:checked').val();
    GetShortestPath(apiUrl, start, end, routingType, season, dayTime);
}

function GetShortestPath(apiUrl, start, end, routingType, season, dayTime) {
    map.spin(true);
    switch (routingType) {
        case "0":
            typeColor = greenLineColors;
            break;
        case "1":
            typeColor = yellowLineColors;
            break;
        default:
            typeColor = blueLineColors;
    }
    $.ajax({
        type: 'POST',
        data: { 'start': start, 'end': end, 'routingType': routingType, 'season': season, 'dayTime': dayTime, 'submit': 'start' },
        dataType: 'json',
        url: apiUrl,
        success: function (data) {
            if (data.succeded) {
                experiments = data.number_of_experiments;
                paths_pool = data.paths;
                paths_pool.features.sort(function (a, b) {
                    return b.properties.weight - a.properties.weight
                });
                counter = 0;
                path = L.geoJson(paths_pool, {
                    onEachFeature: function (feature, layer) {
                        percentil = (feature.properties.count / experiments) * 100;
                        var tableRow = parse('<tr><td bgcolor=%s>%s.</td><td>%s m</td><td>%s %</td></tr>',
                                                    typeColor[counter % 10],
                                                    (counter + 1).toString(),
                                                    feature.properties.length.toString(),
                                                    percentil.toString());
                        $("#foundPaths tbody").append(tableRow);

                        var contentHTML = parse('real length: %s</br>evaluation: %s</br> Frequency: %s </br> Frequency: %s %',
                                                     feature.properties.length.toString(),
                                                     feature.properties.eval.toString(),
                                                    feature.properties.count.toString(),
                                                    percentil.toString());
                        layer.bindPopup(contentHTML);
                        layer.setStyle({ weight: feature.properties.weight.toString(), color: typeColor[counter % 10] });
                        counter++;
                    }
                }).addTo(map);
                pathsLayer.push(path);
            }
            else {
                alert(data.message.toString());
            }
            map.spin(false);
        },
        error: function (e) {
            alert('Unexpected error! Cannot get path');
            map.spin(false);
        }
    });
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
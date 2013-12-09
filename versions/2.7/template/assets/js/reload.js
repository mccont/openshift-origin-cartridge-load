var skipstart = 0;
var iteration = 0;
var debugmode = 0;
var baseconfig;

function getdebug() { 
    if ($('#debug').is(':checked')) {
        debugmode = 1;
    } else {
        debugmode = 0;
    }
}

function refresh() {

    url = '?m=load&skip=' + skipstart + '&_=' + iteration++;

    $.getJSON(url, '')
        .done(function(data) {
                $('#loadmessage').html(data.currmsg);
                $('#hostmessage').html(data.hostname);
                
                if (data.status === 'error') {
                    stoprefresh();
                    return;
                }
                
                if (data.counter == 0) {
                    skipstart++;
                }
                
                var m4_read_a={data: data.reads, color: '#ffffff', label: 'Reads'};
                var m4_write_a={data: data.writes, color: '#3399FF', label: 'Writes'};
                var plot1=[m4_read_a,m4_write_a,];
                var options1 = {
                    xaxis: { mode: "time", ticks: 6, timeformat: "%H:%M:%S", color: "#888888", tickColor: "#888888", font: "color #888888" },
                    yaxis: { min: 0, color: "#888888", tickColor: "#888888", font: "color #888888" },
                    grid: { hoverable: true, clickable: true, aboveData: false, color: "#888888" },
                    legend: { position: "sw", backgroundOpacity: 0, margin: 4, color: "#888888"  }
                };

                if (localStorage.theme == 'theme-openshift') {
                    options1 = {
                        xaxis: { mode: "time", ticks: 6, timeformat: "%H:%M:%S", color: "#cd1f2b", tickColor: "#cd1f2b", font: "color #cd1f2b" },
                        yaxis: { min: 0, color: "#cd1f2b", tickColor: "#cd1f2b", font: "color #cd1f2b" },
                        grid: { hoverable: true, clickable: true, aboveData: false, color: "#cd1f2b" },
                        legend: { position: "sw", backgroundOpacity: 0, margin: 4, color: "#cd1f2b"  }
                    };
                }
                
                $.plot($("#plot1"),plot1, options1);
                
                getdebug();
                
                if (debugmode) {
                    data.reads = '';
                    data.writes = '';
                    $('#loadmessage').html(JSON.stringify(data));
                }
                
                refreshtimer = setTimeout(refresh, 2000);
            })
        .fail(function(data) {
                $('#loadmessage').html("Error: Couldn't contact host");
                $('#hostmessage').html('');
                stoprefresh();
            });
}

function stoprefresh() {
    clearTimeout(refreshtimer);
}

var refreshtimer;

function stopload() {

    url = '?m=stop';

    $.getJSON(url, '', function(data,status,jqhxr) {
            $('#loadmessage').html('Load generator stopped');
        });
    stoprefresh();
}

function startload() {

    stoprefresh();
    skipstart = 0;
    iteration = 0;

    vars = baseconfig;

    $("input[type=text]").each(function() {
            args = $(this).attr('id').split("_");
            vars[args[1]][args[2]] = $(this).val();
            console.log('Updated vars ' + args[1] + ' - ' + args[2] + ' to ' + $(this).val());
        });

    vars['connections'] = $('#connections').val();

    url = '?m=start&vars=' + encodeURIComponent(JSON.stringify(vars));

    $.getJSON(url, '', function(data,status,jqhxr) {
            console.log(new Date() + " Load Started: " + textStatus + " " + jqxhr.msg); //success
            $('#loadmessage').html('Waiting for data load to start');
        });
    refreshtimer = setTimeout(refresh, 2000);
}

$(document).ready(function() { 

        html.classList.add('theme-openshift');

        var urlParams;
        var match,
            pl     = /\+/g,  // Regex for replacing addition symbol with a space
            search = /([^&=]+)=?([^&]*)/g,
            decode = function (s) { return decodeURIComponent(s.replace(pl, " ")); },
            query  = window.location.search.substring(1);

            $.getJSON('config.json', function(data) { 
                    baseconfig = data;
                    $.each(data,function(basekey, baseval) {
                            $.each(baseval,function(key,val) { 
                                    controlvalue = '#config_' + basekey + '_' + key;
                                    $(controlvalue).val(val);
                                });
                        });
                });
            
            urlParams = {};
            while (match = search.exec(query)) {
                urlParams[decode(match[1])] = decode(match[2]);
            }
            
            $("#logocontrol").click(function(){ $("#controldialog").dialog(
                                                                           {buttons: { "Start": function() { startload(); $(this).dialog("close"); },
                                                                                       "Stop": function() { stopload(); $(this).dialog("close"); }, 
                                                                                           "Refresh": function() { refresh(); $(this).dialog("close"); },
                                                                                               },
                                                                                   width: '500px',
                                                                                   resizable: false,
                                                                                   });
                });
            

            var paramlist = new Array('user','host','password',
                                      'connections',
                                      'rthreads','rreadsize',
                                      'wthreads','wreadsize','winserts','wdeletes','wupdates',
                                      'duration');

            if (urlParams.user)
                $('#user').val(urlParams.user);
            if (urlParams.password)
                $('#password').val(urlParams.password);
            if (urlParams.host)
                $('#host').val(urlParams.host);
            if (urlParams.connections)
                $('#connections').val(urlParams.connections);
            if (urlParams.rthreads)
                $('#rthreads').html(urlParams.rthreads);
            if (urlParams.wthreads)
                $('#wthreads').html(urlParams.wthreads);

            if (urlParams.mode && urlParams.mode == 'start') {
                startload();
            }
            if (urlParams.mode && urlParams.mode == 'refresh') {
                refresh();
            }


    });


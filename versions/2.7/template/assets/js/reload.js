var skipstart = 0;
var iteration = 0;

function refresh() {

    url = '?m=load&skip=' + skipstart + '&_=' + iteration++;

    $.getJSON(url, function(data, textStatus, jqxhr) {
            //            console.log(new Date() + " Loaded data " + data.counter + " :"+ textStatus + " " + jqxhr.status);

            $('#loadmessage').html(data.datastatus);
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
                xaxis: { mode: "time", ticks: 6, timeformat: "%H:%M:%S", color: "#cd1f2b", tickColor: "#cd1f2b", font: "color #cd1f2b" },
                yaxis: { min: 0, color: "#cd1f2b", tickColor: "#cd1f2b", font: "color #cd1f2b" },
                grid: { hoverable: true, clickable: true, aboveData: false, color: "#cd1f2b" },
                legend: { position: "sw", backgroundOpacity: 0, margin: 4, color: "#cd1f2b"  }
	    };

            $.plot($("#plot1"),plot1, options1);
            refreshtimer = setTimeout(refresh, 2000);
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

    skipstart = 0;
    iteration = 0;

    vars = { 'conn' : { 'host' : $('#host').val(),
                        'user' : $('#user').val(),
                        'password' : $('#password').val(),
        },
             'connections' : $('#connections').val(),
             'rosettings' : { 'threadCount' :  $('#rthreads').html(),
                              'readSize' : $('#rreadsize').val(),
                 },
             'rwsettings' : { 'threadCount' :  $('#wthreads').html(),
                              'readSize' : $('#wreadsize').val(),
                              'inserts' : $('#winserts').val(),
                              'deletes' : $('#wdeletes').val(),
                              'updates' : $('#wupdates').val(),
                 },
             'core' : { 'testDuration' : $('#duration').val(),
             },
    };

    url = '?m=start&vars=' + encodeURIComponent(JSON.stringify(vars));

    $.getJSON(url, '', function(data,status,jqhxr) {
            console.log(new Date() + " Load Started: " + textStatus + " " + jqxhr.msg); //success
            $('#loadmessage').html('Waiting for data load to start');
        });
    refresh();
}

$(document).ready(function() { 

        var urlParams;
        var match,
            pl     = /\+/g,  // Regex for replacing addition symbol with a space
            search = /([^&=]+)=?([^&]*)/g,
            decode = function (s) { return decodeURIComponent(s.replace(pl, " ")); },
            query  = window.location.search.substring(1);
            
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
            
            $(function() {
                    $( "#sliderrthreads" ).slider({
                            range: "min",
                                min: 1,
                                max: 330,
                                value: 330,
                                slide: function( event, ui ) {
                                $( "#rthreads" ).html( ui.value );
                            }
                        });
                    $( "#rthreads" ).html($( "#sliderrthreads" ).slider( "value" ) );
                });

            $(function() {
                    $( "#sliderwthreads" ).slider({
                            range: "min",
                                value: 150,
                                min: 1,
                                max: 300,
                                slide: function( event, ui ) {
                                $( "#wthreads" ).html( ui.value );
                            }
                        });
                    $( "#wthreads" ).html( $( "#sliderwthreads" ).slider( "value" ) );
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


var skipstart = 0;
var iteration = 0;

function refresh() {

    url = '?m=load&_=' + iteration++;

    $.getJSON(url, function(data, textStatus, jqxhr) {
            console.log(new Date() + " Loaded data " + data.counter + " :"+ textStatus + " " + jqxhr.status);

            $('#loadmessage').html(data.datastatus);
            $('#hostmessage').html(data.hostname);

            if (data.counter > 0) {
                skipstart++;
            }

            var m4_read_a={data: data.reads, color: '#EFEFEF', label: 'Reads'};
            var m4_write_a={data: data.writes, color: '#3399FF', label: 'Writes'};
            var plot1=[m4_read_a,m4_write_a,];
            var options1 = {
                xaxis: { mode: "time", ticks: 6, timeformat: "%H:%M:%S", color: "#cccccc" },
                yaxis: { min: 0, color: "#FFFFFF" },
                grid: { hoverable: true, clickable: true, aboveData: false },
                legend: { position: "sw", backgroundOpacity: 0, margin: 4, color: "#cccccc"  }
	    };

            $.plot($("#plot1"),plot1, options1);
            refreshtimer = setTimeout(refresh, 5000);
        });
}

function stoprefresh() {
    clearTimeout(refreshtimer);
}

var refreshtimer;

function stopload() {

    url = '?m=stop';

    $.getJSON(url, '', function(data,status,jqhxr) {
            console.log(new Date() + " Load Started: " + textStatus + " " + jqxhr.msg); //success
            $('#loadmessage').html('Waiting for data load to start');
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
              
    };

    url = '?m=start&vars=' + encodeURIComponent(JSON.stringify(vars));

    $.getJSON(url, '', function(data,status,jqhxr) {
            console.log(new Date() + " Load Started: " + textStatus + " " + jqxhr.msg); //success
            $('#loadmessage').html('Waiting for data load to start');
        });
    refresh();
}

$(document).ready(function() { 

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
                            max: 50,
                            value: 30,
                            slide: function( event, ui ) {
                            $( "#rthreads" ).html( ui.value );
                        }
                    });
                $( "#rthreads" ).html($( "#sliderrthreads" ).slider( "value" ) );
            });

        $(function() {
                $( "#sliderwthreads" ).slider({
                        range: "min",
                            value: 10,
                            min: 1,
                            max: 50,
                            slide: function( event, ui ) {
                            $( "#wthreads" ).html( ui.value );
                        }
                    });
                $( "#wthreads" ).html( $( "#sliderwthreads" ).slider( "value" ) );
            });



    });


"use strict"; // use strict javaScript!

var USERID;

var socket;
var importing = [];

function add_porgress_bar(file_id) {
  return '<td><div class="progress active"><div class="progress-bar progress-bar-success" style="width:0%"' +
      ' id="update-'+file_id +'"></div></div></td>';
}

function start_import2() {
  console.log("Start_import was clicked");
  console.log("***** USERID: "+USERID);

  $.ajax({
    type: 'GET',
    url: '/import/'+USERID,
    contentType: "application/json; charset=utf-8",
    dataType: "json",
    success: function(data, status, request) {
    },
    error: function() {
      alert('Could not start the import');
    }
  });
}

function start_import_xml_file(button) {
  var tr = button.closest("tr");
  var file_id = tr.attr('data-file-id');
  // Set text to import
  tr.find('td').eq(1).text('Importing...');
  tr.find('.update-xml-import').replaceWith(add_porgress_bar(file_id));
  if( importing.indexOf(file_id) < 0) {
    socket.emit('import', USERID, file_id);
    importing.push(file_id);
  }
};


$(document).ready(function(){

  socket = io.connect('http://' + document.domain + ':' + location.port + '/events');

  socket.on('connect', function() {
    console.log("on connect " +USERID);
  });

  socket.on('userid', function(msg) {
     console.log("New Userid: " +msg.userid);
    USERID = msg.userid;
  });


  socket.on('update_progress_bar', function (event) {
    var tr = $("#update-"+event.file_id);

    if( tr === undefined || tr.length === 0 ) {
      // Go through all tr and check if file_id match our id
      $(".import-file").map(function () {
        if ($(this).attr('data-file-id') == event.file_id) {
          $(this).find('td').eq(1).replaceWith(add_porgress_bar(event.file_id));
          tr = $(this);
        }
      });
    }

    if( event.error ) {
      tr.addClass("danger");
      tr.addClass("error_import_xml");
      tr.find('td').eq(2).text(event.error_message);
      window.setTimeout( () => tr.removeClass("error_import_xml"), 4000);
      return;
    }

    // Aktualisiere den lade balken
    $("#update-"+event.file_id).animate({
      width: (event.current/event.total)*100+'%'
    }, 100);

    console.log(event.current == event.total);
    if( event.current == event.total) {
      tr.find('td').eq(1).text('Successful imported');
      tr.addClass("finish_import_xml");
      window.setTimeout( () => tr.removeClass("finish_import_xml"), 2000);
    }
  });


  socket.on('update_xmlFile_information', function (event) {
    update_progress_bar(event.file_id, (event.current/event.total));
  });

});

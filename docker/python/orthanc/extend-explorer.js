$('#study').live('pagebeforecreate', function() {

  var b = $('<a>')
    .attr('data-role', 'button')
    .attr('href', '#')
    .attr('data-icon', 'search')
    .attr('data-theme', 'e')
    .text('Show metadatas');

  b.insertBefore($('#study-delete').parent().parent());
  b.click(function() {
    if ($.mobile.pageData) {
      var study = $.mobile.pageData.uuid;

      window.open('/studies/' + study + '/metadata?expand');
    }
  });
});

$('#instance').live('pagebeforecreate', function() {

  var b = $('<a>')
    .attr('data-role', 'button')
    .attr('href', '#')
    .attr('data-icon', 'search')
    .attr('data-theme', 'e')
    .text('Show pydicom');

  b.insertBefore($('#instance-delete').parent().parent());
  b.click(function() {
    if ($.mobile.pageData) {
      var instance = $.mobile.pageData.uuid;

      window.open('/pydicom/' + instance);
    }
  });
});

$(document).ready(function () {
  var table = $('#viewrecords').DataTable({
      "order": [[0, "desc"]],  // Sort by the first column (date) in descending order
      "columnDefs": [
          { "targets": 0, "type": "date" } // Ensure Date column is treated as a date
      ]
  });

  // Ensure the sorting arrow is pointing down on the first column (date)
  $('#dataTable thead th').removeClass('sorting_asc').removeClass('sorting_desc'); // Clear default classes
  $('#dataTable thead th:first-child').addClass('sorting_desc'); // Set arrow to down
});

$(document).ready(function() {
  $('#dataTable').DataTable({
    "order": [] // Disable initial sorting
  });
});

$(document).ready(function() {
  $('#dataTable1').DataTable({
      pageLength: 5,         // Show 5 entries per page
      order: [[2, 'desc']],  // Sort by Timestamp (3rd column) in descending order
      columnDefs: [
          { targets: 2, className: 'dt-head-left dt-body-left' } // Apply left alignment to header and body
      ]
  });
});


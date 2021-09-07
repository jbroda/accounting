$(document).ready(function ()
{
    // Add natural sort for sorting by the account ID.
    $.extend($.fn.dataTableExt.oSort, {
        "natural-asc": function (a, b) {
            return naturalSort(a, b);
        },

        "natural-desc": function (a, b) {
            return naturalSort(a, b) * -1;
        }
    });

    // Add sorting of HTML tags with numeric data for sorting by the account balance.
    $.extend(jQuery.fn.dataTableExt.oSort, {
        "num-html-pre": function (a) {
            // Remove HTML tags.
            var x1 = String(a).replace(/<[\s\S]*?>/g, "");

            // Remove commas.
            var x = String(x1).replace( /,/, "" );

            return parseFloat(x);
        },

        "num-html-asc": function (a, b) {
            return ((a < b) ? -1 : ((a > b) ? 1 : 0));
        },

        "num-html-desc": function (a, b) {
            return ((a < b) ? 1 : ((a > b) ? -1 : 0));
        }
    });

    // Initialize the accounts table.
    $('#accounts-table').dataTable({
        dom: "<'row'<'col-sm-4'l><'col-sm-4'f>r<'col-sm-4'<'pull-right'TB>>>t<'row'<'col-sm-6'i><'col-sm-6'p>>",
        buttons: [
            'copy',
            'csv',
            'print',
        ],
        "aaSorting": [[1, 'asc']],
        "aoColumns": [
            null,
            {"sType": "natural"},
            null,
            {"sType": "num-html"},
            null
        ],
        "aoColumnDefs": [
            { "bSortable": false, "aTargets": [0, 2, 4] }
        ],
        //"sPaginationType": "bootstrap",
        "bPaginate": true,
        "bLengthChange": true,
        "bFilter": true,
        "bSort": true,
        "bInfo": true,
        "bAutoWidth": true,
        "asStripeClasses": ['odd', 'even'],
        "iDisplayLength": -1,
        "oLanguage": {
            "sLengthMenu": 'Display <select>' +
            '<option value="10">10</option>' +
            '<option value="20">20</option>' +
            '<option value="30">30</option>' +
            '<option value="40">40</option>' +
            '<option value="60">60</option>' +
            '<option value="-1">All</option>' +
            '</select> accounts per page'
        }
    });

    // Select all checkboxes from the header.
    $("#select_all_head").click(function () {
        $(".selectedId").prop("checked", this.checked);
        var oTable = $('#accounts-table').dataTable();
        $(".selectedId", oTable.fnGetNodes()).prop("checked", this.checked);
    });

    // Select all checkboxes from the footer.
    $("#select_all_foot").click(function () {
        $(".selectedId").prop("checked", this.checked);
        var oTable = $('#accounts-table').dataTable();
        $(".selectedId", oTable.fnGetNodes()).prop("checked", this.checked);
    });

    // Select the header and footer checkbox when all the other checkboxes are selected.
    $('.selectedId').change(function () {
        var check =
            ($('.selectedId').filter(":checked").length ==
             $('.selectedId').length);
        $('#select_all_header').prop("checked", check);
        $('#select_all_footer').prop("checked", check);
    });
});

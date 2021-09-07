$(document).ready(function() {
    var account = $("input[name='accounts']").val(); // Only one account.
    var balance = $("#balance").text();

    // Re-check the single account check box that was unchecked in entry_form.js.
    $("#select_" + account).prop("checked", true);
    
    // Initialize the accounts table.
    $('#accounts-table').dataTable();

    // Sort by US date and time.
    $.extend($.fn.dataTableExt.oSort, {
        "datetime-us-pre": function(a) {
            return dateTimeSort(a);
        },
        "datetime-us-asc": function (a, b) {
            return a - b;
        },

        "datetime-us-desc": function (a, b) {
            return b - a;
        }
    });

    // Add 'datetime-us' sort type.
    $.fn.dataTableExt.aTypes.unshift(
        function(sData) {
            return dateTimeSortType(sData);
        }
    );

    // Initialize the transaction data table.
    var oTransactionTable = $('#transaction-table').dataTable({
        dom: "<'row'<'col-sm-4'l><'editmode'><'col-sm-4'f>r<'col-sm-3 tools'<'pull-right'TB>>>t<'row'<'col-sm-6'i><'col-sm-6'p>>",
        buttons: [
            'copy',
            'csv',
            'print',
        ],
        "aaSorting": [[0, 'desc']],
        "aoColumns": [
            null,
            null,
            null,
            { "sType": "numeric" },
            { "sType": "datetime-us" }
        ],
        "aoColumnDefs": [
            { "bSortable": false, "aTargets": [1,2,3] },
            { "sWidth": "5em", "aTargets": [0] },
            { "sWidth": "5em", "aTargets": [2] },
            { "sWidth": "5em", "aTargets": [3] },
            { "aDataSort": [4, 3], "aTargets": [0] },
        ],
        "bPaginate": true,
        "bLengthChange": true,
        "bFilter": true,
        "bSort": true,
        "bInfo": true,
        "bAutoWidth": false,
        "asStripeClasses": ['odd', 'even'],
        "iDisplayLength": 10,
        "stateSave" : false,
        "oLanguage": {
            "sSearch": 'Filter:',
            "sInfo" :  "Showing _START_ to _END_ of _TOTAL_ transactions",
            "sLengthMenu": 'Display <select>' +
                '<option value="10">10</option>' +
                '<option value="20">20</option>' +
                '<option value="30">30</option>' +
                '<option value="40">40</option>' +
                '<option value="60">60</option>' +
                '<option value="-1">All</option>' +
                '</select> transactions per page'
        }
    });

    // Create a div for the Edit Mode toggle button.
    $("div.editmode").html("<div class='col-sm-1'><button id='toggle_edit' title='Toggle Edit Mode'\
        type='button' class='btn btn-xs btn-default'>\
        <span aria-hidden='true' class='glyphicon glyphicon-edit'/> \
        <span id='text'>Off</span></button></div>");

    // Configure the edit mode.
    $.fn.editable.defaults.mode = 'inline';

    // Expand the transaction table before configuring the editable memo.
    var oSettings = oTransactionTable.fnSettings();
    var iDisplayLength = oSettings._iDisplayLength;
    var iDisplayStart = oSettings._iDisplayStart;
    oSettings._iDisplayLength = -1;
    oTransactionTable.fnDraw();

    // Configure the editable memo.
    $('.editable_memo').editable('disable', {
        type: 'text',
        title: 'Edit Memo',
    });

    // Restore the transaction table.
    oSettings._iDisplayLength = iDisplayLength;
    oSettings._iDisplayStart = iDisplayStart;
    oTransactionTable.fnDraw();

    // toggleText function.
    $.fn.toggleText = function(t1, t2) {
        var txtSpan = $('#text', this);
        if (txtSpan.text() == t1) txtSpan.text(t2);
        else txtSpan.text(t1);
        return this;
    };

    // Toggle edit mode button handler.
    $('#toggle_edit').click(function () {
        // Save transaction table settings.
        var oSettings = oTransactionTable.fnSettings();
        var iDisplayLength= oSettings._iDisplayLength;
        var iDisplayStart = oSettings._iDisplayStart;

        // Show all transactions in the table.
        oSettings._iDisplayLength = -1;
        oTransactionTable.fnDraw();

        // Toggle the editable property.
        $('.editable_memo').editable('toggleDisabled');
        $(this).toggleClass('btn-default');
        $(this).toggleClass('btn-primary');
        $(this).toggleClass('active');
        $(this).toggleText('On','Off');

        // Restore the transaction table settings.
        oSettings._iDisplayLength = iDisplayLength;
        oSettings._iDisplayStart = iDisplayStart;
        oTransactionTable.fnDraw(true);
    });

    // Handle the Payment Plan checkbox.
    $('input:checkbox[id=payment_plan]').click(function() {
        var isChecked = $(this).prop('checked');
        var unitAddress = $('#unit_address').val();
        var unitNumber = $('#unit_number').val();

        bootbox.dialog({
            message: "Updating <b>Payment Plan</b> status for " + unitAddress + " #" + unitNumber + " ...",
            animate: false,
            closeButton: false
        });

        var request = $.ajax({
            type: "POST",
            url: "update/",
            traditional: true,
            data: {
                unit_address: unitAddress,
                unit_number: unitNumber,
                is_payment_plan: isChecked,
            },
            dataType: "html"
        });

        request.done(function (msg) {
            var newIsChecked = $('input:checkbox[id=payment_plan]').prop('checked');
            console.log("Payment Plan flag: " + newIsChecked);
            bootbox.hideAll();
        });

        request.fail(function (jqXHR, textStatus) {
            console.log("failure: " + textStatus);
            bootbox.hideAll();
            alert("Request failed: " + textStatus);
        });
    });

    // Handle the No Statement checkbox.
    $('input:checkbox[id=no_statement]').click(function () {
        var isChecked = $(this).prop('checked');
        var unitAddress = $('#unit_address').val();
        var unitNumber = $('#unit_number').val();

        bootbox.dialog({
            message: "Updating <b>No Statement</b> status for " + unitAddress + " #" + unitNumber + " ...",
            animate: false,
            closeButton: false
        });

        var request = $.ajax({
            type: "POST",
            url: "update/",
            traditional: true,
            data: {
                unit_address: unitAddress,
                unit_number: unitNumber,
                is_no_statement: isChecked,
            },
            dataType: "html"
        });

        request.done(function (msg) {
            var newIsChecked = $('input:checkbox[id=no_statement]').prop('checked');
            console.log("No Statement flag: " + newIsChecked);
            bootbox.hideAll();
        });

        request.fail(function (jqXHR, textStatus) {
            console.log("failure: " + textStatus);
            bootbox.hideAll();
            alert("Request failed: " + textStatus);
        });
    });

    // Handle the E-Statement checkbox.
    $('input:checkbox[id=email_statement]').click(function () {
        var isChecked = $(this).prop('checked');
        var unitAddress = $('#unit_address').val();
        var unitNumber = $('#unit_number').val();

        bootbox.dialog({
            message: "Updating <b>E-Statement</b> status for " + unitAddress + " #" + unitNumber + " ...",
            animate: false,
            closeButton: false
        });

        var request = $.ajax({
            type: "POST",
            url: "update/",
            traditional: true,
            data: {
                unit_address: unitAddress,
                unit_number: unitNumber,
                is_email_statement: isChecked,
            },
            dataType: "html"
        });

        request.done(function (msg) {
            var newIsChecked = $('input:checkbox[id=email_statement]').prop('checked');
            console.log("E-Statement flag: " + newIsChecked);
            bootbox.hideAll();
        });

        request.fail(function (jqXHR, textStatus) {
            console.log("failure: " + textStatus);
            bootbox.hideAll();
            alert("Request failed: " + textStatus);
        });
    });

    // Handle statement request.
    $('.statement').click(function (e) {
        console.log(this.id + " statement requested: " + this.href);

        e.preventDefault();

        // Save the statement HREF.
        var statementHref = this.href;

        // Initialize the start date to today.
        var d = new DateTime();
        var startDate = d.sym.d.yyyy + '-' + d.sym.d.mm + '-' + d.sym.d.dd;

        if (this.id == 'reo') {
            // Format the today's date for display.
            var todayStr = d.sym.d.mmmm + " " + d.sym.d.dd + ", " + d.sym.d.yyyy;

            bootbox.dialog({
                animate: false,
                title: 'Select starting date',
                message: (''+
                            '<div class="input-group date"' +
                                  'id="dtpicker_reo" data-date-format="MMMM DD, YYYY">' + 
                                    '<input class="form-control"' +
                                           'id="reo_statement_date" name="reo_statement_date"' +
                                           'type="text"' +
                                           'value="' + todayStr + '" />' +
                                    '<span class="input-group-addon">' +
                                        '<span class="fa fa-calendar"></span>' +
                                    '</span>' +
                                '</div>'),
                buttons: {
                    success: {
                        label: 'Get Statement',
                        className: 'btn-success',
                        callback: function() {
                            d = new DateTime($("#reo_statement_date").val());
                            startDate = d.sym.d.yyyy + '-' + d.sym.d.mm + '-' + d.sym.d.dd;
                            console.log("New start date: " + startDate);

                            getStatement(statementHref, startDate);
                        }
                    }
                }
            });

            // Initialize the date picker for REO statements.
            $("#dtpicker_reo").datetimepicker({
                pickTime: false
            });

            return false;
        }

        getStatement(statementHref, startDate);
    });

    // Get statement.
    function getStatement(href, startDate) {
        console.log("getStatement(): start date is " + startDate);

        // Replace the start date in href.
        if (startDate) {
            href = href.replace(/\d{4}-\d{2}-\d{2}/, startDate);
            console.log("new href: " + href);
        }

        // Get a random unique request id.
        var reqId = getUUID();

        // Send an AJAX GET request to generate a statement for this account. 
        var request = $.ajax({
            type: "GET",
            url: href + reqId + "/",
        });

        // Display a cancel dialog.
        bootbox.dialog({
            animate: false,
            message: ("<p>Generating a statement for " + account + " ... </p>" +
                "<div class='progress'>" +
                "<div class='progress-bar progress-bar-striped active'" +
                "role='progressbar' aria-valuemin='0' aria-valuemax='100'" + 
                "aria-valuenow='100' style='width: 100%'></div></div>"),
            closeButton: false,
            buttons: {
                danger: {
                    label: "Cancel",
                    className: "btn-danger",
                    callback: function () {
                        console.log('Cancel for statement request "' + reqId + '" pressed!');

                        // Send an AJAX request to cancel on the server side.
                        var cancelRq = $.ajax({
                            type: "POST",
                            url: "/accounting/report/cancel/statement/" + reqId + "/",
                        });

                        cancelRq.done(function (r) {
                            console.log("cancelRq done " + r);
                        });

                        cancelRq.fail(function (jqXhr, status) {
                            console.log("cancelRq fail " + status);
                        });

                        cancelRq.always(function () {
                            console.log("cancelRq complete");
                        });

                        // Cancel the request on the client side.
                        request.abort();
                    }
                },
            },
        });

        // Handle success.
        request.done(function (pdf) {
            url = pdf.url;
            path = pdf.path;
            console.log("Received statement URL: " +url);
            bootbox.hideAll();
            var win = window.open(url, "_blank");
            popupBlockerChecker.check(win);
            if (!win) {
                bootbox.dialog({
                    message: "Click <a href=" + url + "><b><u>here</u></b></a> the account "
                    + account + " statement!"
                });
            }
        });

        // Handle failure.
        request.fail(function (jqXhr, textStatus) {
            console.log("failure: " + textStatus);
            bootbox.hideAll();
            if (textStatus == "abort") {
                bootbox.alert('Statement cancelled!');
            }
            else {
                bootbox.alert('Failed to generate the statement: ' + textStatus + '!');
            }
        });

        // Always do this.
        request.always(function () {
            console.log('Request for the statement is complete!');
        });

        return false;
    }
});

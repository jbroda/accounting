
// Uncollapse the report panel given by the link.
function selectReport(link) {
    var url = String(link);
    var hash = url.substring(url.indexOf("#"));
    var panel = hash + "_panel";
    console.log("selectForm(): showing " + panel);
    $(panel).collapse('show');
}

// Delete report given by action in the form.
function onDeleteReport(form) {
    console.log("Deleting report ...");

    try {
        var deleteUrl = form.attr("action");
        var redirectUrl = $("input[name=redirect_url]", form.context).val();

        console.log("Deleting: " + deleteUrl + ", redirect: " + redirectUrl);

        // Disable the delete button and report link.
        $('#report_delete_btn', form.context).prop("disabled", true);
        $('#report_link', form.context).first().removeAttr('href');

        var deleteRq = $.ajax({
            type: "POST",
            url: deleteUrl,
            data: {
                redirect_url: redirectUrl
            },
        });

        deleteRq.done(function (r) {
            console.log("deleteRq done ");
            form.parent().hide();
        });

        deleteRq.fail(function (jqXhr, status) {
            console.log("deleteRq fail " + status);
        });

        deleteRq.always(function () {
            console.log("deleteRq always");
        });
    }
    catch (err) {
        console.log(err.message);
    }

    return false;
}

///////////////////////////////////////////////////////////////////////////////
function getReportLink(report_type, report_url, report_path, report_name)
{
    var strReportLink = "";
    strReportLink += "<form style=\"display: inline;\"";
    strReportLink += "      name=\"report_delete_form\"";
    strReportLink += "      id=\"report_delete_form\"";
    strReportLink += "      action=\"\/delete" + report_path + "\"";
    strReportLink += "      onsubmit=\"return onDeleteReport($(this));\"";
    strReportLink += "      method=\"post\">";
    //strReportLink += "     {% csrf_token %}";
    strReportLink += "";
    strReportLink += "    <a id=\"report_link\" target=\"_blank\" href=\"" + report_url + "\">" + report_name + "<\/a>";
    strReportLink += "";
    strReportLink += "    <input type=\"hidden\" ";
    strReportLink += "           name=\"redirect_url\" ";
    strReportLink += "           id=\"redirect_url\"";
    strReportLink += "           value=\"\/accounting\/reports\/#" + report_type + "\"\/>";
    strReportLink += "";
    strReportLink += "    <button name=\"report_delete_btn\"";
    strReportLink += "            id=\"report_delete_btn\" ";
    strReportLink += "            type=\"submit\" ";
    strReportLink += "            class=\"btn btn-danger btn-xs\" ";
    strReportLink += "            title=\"Delete '" + report_name + "'\">";
    strReportLink += "        <span class=\"glyphicon glyphicon-remove\"><\/span>";
    strReportLink += "    <\/button>";
    strReportLink += "<\/form>";
    strReportLink += "";

    return strReportLink;
}

///////////////////////////////////////////////////////////////////////////////
function get_report_list(report_type) {
    console.log("get_report_list(" + report_type + ")");

    try {
        var listReportsRq = $.ajax({
            type: "GET",
            dataType: "json",
            cache: false,
            url: '/accounting/reports/list/' + report_type + '/',
            report_type : report_type
        });

        listReportsRq.done(function (data) {
            console.log("listReportsRq done: " + data);

            var report_type = this.report_type;
            var reports = data[report_type];

            var links = "";
            for (i = 0; i < reports.length; i++)
            {
                var name = reports[i].name;
                var path = reports[i].path;
                var url  = reports[i].url;
                console.log(report_type + " name: " + name + ", path: " + path + ", url: " + url);

                var link = getReportLink(report_type, url, path, name);
                links += "<li>" + link + "</li>";
            }
            
            if (0 == reports.length) {
                links = "<li>No " + report_type + " reports found!</li>"
            }

            $("#" + report_type + "_report_list").html(links)
        });

        listReportsRq.fail(function (jqXhr, status) {
            console.log("listReportsRq fail " + status);
        });

        listReportsRq.always(function () {
            console.log("listReportsRq always");
        });
    }
    catch (err) {
        console.log(err.message);
    }
}

// Execute when finished loading the page.
$(document).ready(function () {

    // Report types array.
    var report_types = [
        'transaction',
        'statement',
        'delinquency',
        'income',
        'account_trail',
        'account_audit',
        'lease',
        'expired_lease',
        'vos_lease',
        'fha_lease',
        'export'
    ];

    // Perform configuration for each report type.
    for (var obj in report_types)
    {
        var report_type = report_types[obj];

        // Configure the collapsible report panel.
        var collapsible = "#" + report_type + "_panel";

        if ($(collapsible).length)
        {
            $(collapsible).collapse({ toggle: false });
            $(collapsible).on('shown.bs.collapse', (function (report_type) {
                return function () {
                    // Set the url to the hash when the collapsible element is shown.
                    $(location).attr('hash', report_type);
                };
            })(report_type));
        }

        // Configure the report history.
        var report_history = "#" + report_type + "_history";

        if ($(report_history).length)
        {
            $(report_history).on('show.bs.collapse', (function (report_type) {
                return function () {
                    console.log("show " + report_type + " history ...");
                    $("#" + report_type + "_report_list").html("<li>Please wait ...</li>");
                };
            })(report_type));

            $(report_history).on('shown.bs.collapse', (function (report_type) {
                return function () {
                    console.log("shown " + report_type + " history ...");
                    get_report_list(report_type);
                };
            })(report_type));
        }
    }

    // Show the collapsible report panel corresponding to the hash in the url.
    var hash = $(location).attr('hash');
    if (hash != "") {
        var panel = hash + "_panel";
        console.log("ready(): showing " + panel);
        $(panel).collapse('show');
    }

    // Initialize the widgets.
    $("#dtpicker").datetimepicker({
        pickTime: false
    });

    $("#dtpicker_trans_start").datetimepicker({
       pickTime: false
    });

    $("#dtpicker_trans_end").datetimepicker({
       pickTime: false
    });

    $("#dtpicker_statement").datetimepicker({
       pickTime: false
    });

    $("#dtpicker_income_start").datetimepicker({
        pickTime: false
    });

    $("#dtpicker_income_end").datetimepicker({
        pickTime: false
    });

    $("#dtpicker_account_trail").datetimepicker({
       pickTime: false
    });

    $("#dtpicker_account_audit_start").datetimepicker({
       pickTime: false
    });

    $("#dtpicker_account_audit_end").datetimepicker({
       pickTime: false
    });

    $("#dtpicker_lease").datetimepicker({
       pickTime: false
    });

    $('.btn-group button').click(function()
    {
        $(this).parent().children().removeClass('active');
        $(this).addClass('active');
    });

    //////////////////////////////////////////////////////////////////////////
    function pad (str, max) {
        str = str.toString();
        return str.length < max ? pad("0" + str, max) : str;
    }

    //////////////////////////////////////////////////////////////////////////
    function capitalize(str) {
        return str.charAt(0).toUpperCase() + str.substring(1);
    }

    //////////////////////////////////////////////////////////////////////////
    function baseName(url) {
        var fileName = url.substring(url.lastIndexOf('/') + 1);
        return fileName
    }

    //////////////////////////////////////////////////////////////////////////
    function generate_report(button, type, subtype, date1, date2)
    {
        if (date1 && date2)
            console.log("Requesting PDF for the " + type + " report for " + date1 + " through " + date2 + "..." )
        else if (date1)
            console.log("Requesting PDF for the " + type + " report as of " + date1 + " ...");
        else
            console.log("Requesting PDF for the " + type + " report ...");

        // Disable the request button to prevent concurrent requests.
        button.prop("disabled", true);

        // Show the progress div for the given report type.
        var progress = '.' + type + '-progress ';
        $(progress).show();

        // Show the progress bar within the progress div.
        $(progress + '#progress').show();

        // Update the progress status.
        $(progress + "#status").text("Generating the " + type + " report. Please wait ...");

        // Get a random unique request id.
        var reqId = getUUID();

        // Send an AJAX GET request to generate the given report.
        var request = $.ajax({
            type: "GET",
            dataType: "json",
            url:
                "/accounting/report/"
                + type + "/"
                + reqId + "/"
                + (subtype ? (subtype + "/") : "")
                + (date1 ? (date1 + "/") : "")
                + (date2 ? (date2 + "/") : ""),
        });

        // Install the cancel handler.
        $(progress + '#cancel_report').off("click"); // Remove the old handler first.
        $(progress + '#cancel_report').on("click", function () {
            console.log('Cancel for "' + type + '" report request "' + reqId + '" pressed!');

            // Send an AJAX request to cancel on the server side.
            var cancelRq = $.ajax({
                type: "POST",
                url:
                    "/accounting/report/cancel/"
                    + type + "/"
                    + reqId + "/",
            });

            cancelRq.done(function(r) {
                console.log("cancelRq done " + r);
            });

            cancelRq.fail(function(jqXhr, status) {
                console.log("cancelRq fail " + status);
            });

            cancelRq.always(function() {
                console.log("cancelRq always");
            });

            // Cancel the request on the client side.
            request.abort();
        });

        // Handle success.
        request.done(function (pdf) {
            url = pdf.url;
            path = pdf.path;
            console.log("Received " + type + " report PDF URL: " + url + ", PATH: " + path);

            $(progress + "#report").show();
            $(progress + "#report_heading").show();
            $(progress + "#report_link").attr("href", url);
            $(progress + "#report_link").text("Your " + capitalize(type) + " Report");
            $(progress + "#report_delete_form").attr("action","/delete" + path)
            $(progress + "#redirect_url").val("/accounting/reports/#" + type)
            $(progress + "#report_delete_btn").attr("title", "Delete '" + baseName(url) + "'")
            var win = window.open(url,"_blank");
            popupBlockerChecker.check(win);
        });

        // Handle failure.
        request.fail(function (jqXhr, textStatus) {
            console.log("failure: " + textStatus);

            // Hide the progress div.
            $(progress).hide();

            if (textStatus == "abort") {
                alert('"' + type + '" report canceled.');
            } else {
                alert('Failed to generate the "' + type + '" report: ' + 
                 textStatus + '!');
            }
        });

        // Always do this.
        request.always(function () {
            console.log('Request for "' + type + '" report complete!');

            // Hide the progress bar.
            $(progress + '#progress').hide();

            // Re-enable the request button.
            button.prop("disabled", false);
        });
    }

    //////////////////////////////////////////////////////////////////////////
    function onFormSubmitDelinq()
    {
        var d = new Date($("#delinq_date").val()); 

        var dateStr = "" + d.getFullYear() + "-" + 
            pad(d.getMonth() + 1, 2) + "-" + pad(d.getDate(), 2);

        console.log("requesting delinquency report for " + dateStr + " ...");

        generate_report($("#get_d_report"), "delinquency", dateStr);
    }

    //////////////////////////////////////////////////////////////////////////
    function onFormSubmitTransaction()
    {
        var d = new Date($('#transaction_bdate').val()); 
        var dateFrom = "" + d.getFullYear() + "-" + 
            pad(d.getMonth() + 1, 2) + "-" + pad(d.getDate(), 2);

        d = new Date($('#transaction_edate').val());

        var dateTo = "" + d.getFullYear() + "-" + 
            pad(d.getMonth() + 1, 2) + "-" + pad(d.getDate(), 2);

        var tType = "0";
        if ($("#charges").hasClass('active'))
            tType = "1";
        else if ($("#alltransactions").hasClass('active'))
            tType = "2";

        generate_report($("#get_t_report"), "transaction", tType, dateFrom, dateTo);
    }

    //////////////////////////////////////////////////////////////////////////
    function onFormSubmitStatement()
    {
        var d = new Date($("#statement_date").val()); 
        var dateStr = "" + d.getFullYear() + "-" + 
            pad(d.getMonth() + 1, 2) + "-" + pad(d.getDate(), 2);

        generate_report($("#get_s_report"), "statement", dateStr);
    }

    //////////////////////////////////////////////////////////////////////////
    function onFormSubmitIncome() {
        var d = new Date($('#income_bdate').val());
        var dateFrom = "" + d.getFullYear() + "-" +
            pad(d.getMonth() + 1, 2) + "-" + pad(d.getDate(), 2);

        d = new Date($('#income_edate').val());
        var dateTo = "" + d.getFullYear() + "-" +
            pad(d.getMonth() + 1, 2) + "-" + pad(d.getDate(), 2);

        var tType = "0";
        if ($("#accrual").hasClass('active'))
            tType = "1";

        generate_report($("#get_i_report"), "income", tType, dateFrom, dateTo);
    }

    //////////////////////////////////////////////////////////////////////////
    function onFormSubmitTrail()
    {
        var d = new Date($("#account_trail_date").val()); 

        var dateStr = "" + d.getFullYear() + "-" + 
            pad(d.getMonth() + 1, 2) + "-" + pad(d.getDate(), 2);

        generate_report($("#get_at_report"), "account_trail", dateStr);
    }

    //////////////////////////////////////////////////////////////////////////
    function onFormSubmitAccountAudit()
    {
        var d = new Date($('#account_audit_bdate').val());
        var dateFrom = "" + d.getFullYear() + "-" +
            pad(d.getMonth() + 1, 2) + "-" + pad(d.getDate(), 2);

        d = new Date($('#account_audit_edate').val());
        var dateTo = "" + d.getFullYear() + "-" +
            pad(d.getMonth() + 1, 2) + "-" + pad(d.getDate(), 2);

	    // mkm here
        generate_report($("#get_account_audit_report"), "account_audit_report", dateFrom, dateTo);
    }

    //////////////////////////////////////////////////////////////////////////
    function onFormSubmitLease()
    {  
        var d = new Date($('#lease_date').val()); 
        var date = "" + d.getFullYear() + "-" + 
            pad(d.getMonth() + 1, 2) + "-" + pad(d.getDate(), 2);

        var tType = "expired";
        if ($("#fha").hasClass('active'))
            tType = "fha";
        else if ($("#vos").hasClass('active'))
            tType = "vos";

        generate_report($("#get_l_report"), "lease", tType, date);
    }

    //////////////////////////////////////////////////////////////////////////
    function onFormSubmitExport()
    {
        console.log("requesting export report ...");

        generate_report($("#get_exp_report"), "export", "");
    }

    //////////////////////////////////////////////////////////////////////////
    // Configure the validator plugin.
    $.validator.setDefaults({
        highlight: function (element) {
            $(element).closest('.form-group').addClass('has-error');
        },
        unhighlight: function (element) {
            $(element).closest('.form-group').removeClass('has-error');
        },
        errorElement: 'span',
        errorClass: 'help-block',
        errorPlacement: function (error, element) {
            if (element.parent('.input-group').length) {
                error.insertAfter(element.parent());
            } else {
                error.insertAfter(element);
            }
        }
    });

    // Validate the date.
    $.validator.addMethod("validDate", function (value, element) {
        var stamp = value;
        var validDateTime = !/Invalid|NaN/.test(new Date(stamp).toString());
        return this.optional(element) || (validDateTime);
    }, "Please enter a valid date.");
    
    // Validate the entry form.
    $("#delinq-report-form").validate({
        submitHandler: function () {
            onFormSubmitDelinq();
        },
        rules: {
            delinq_date: {
                validDate: true,
                required: true
            }
        }
    });

    $("#transaction-report-form").validate({
        submitHandler: function () {
            onFormSubmitTransaction();
        },
        rules: {
            transaction_bdate: {
                validDate: true,
                required: true
            },
            transaction_edate: {
                validDate: true,
                required: true
            }
        }
    });

    $("#statement-report-form").validate({
        submitHandler: function () {
            onFormSubmitStatement();
        },
        rules: {
            statement_date: {
                validDate: true,
                required: true
            }
        }
    });

    $("#income-report-form").validate({
        submitHandler: function () {
            onFormSubmitIncome();
        },
        rules: {
            income_bdate: {
                validDate: true,
                required: true
            },
            income_edate: {
                validDate: true,
                required: true
            }
        }
    });

    $("#account-trail-report-form").validate({
        submitHandler: function () {
            onFormSubmitTrail();
        },
        rules: {
            account_trail_date: {
                validDate: true,
                required: true
            }
        }
    });

    $("#account-audit-report-form").validate({
        submitHandler: function () {
            onFormSubmitAccountAudit();
        },
        rules: {
            account_audit_bdate: {
                validDate: true,
                required: true
            },
            account_audit_edate: {
                validDate: true,
                required: true
            }
        }
    });


    $("#lease-report-form").validate({
        submitHandler: function () {
            onFormSubmitLease();
        },
        rules: {
            lease_date: {
                validDate: true,
                required: true
            }
        }
    });

    $("#export-report-form").validate({
        submitHandler: function () {
            onFormSubmitExport();
        }
    });
});

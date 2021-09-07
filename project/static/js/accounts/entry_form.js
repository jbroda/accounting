$(document).ready(function () {

    // Initialize the datetime picker.
    $("#dtpicker").datetimepicker({
            pickTime: false
    });

    // Category changed handler
    $("#category").change(function() {
        var category = $("#category").val();

        $("#amount").val("");
        $("#memo").val("");

        $.each( CATEGORIES, function( key, value ) {
            if (key == category) {
                console.log(category + ": '" + value + "'");
                if (isCharge(category)) {
                    $("#memo").val(key + "\r\n");
                }
                if (value != "") {
                    try {
                        $("#amount").val(Number(value).toFixed(2));
                    }
                    catch(err) {
                        console.log(err);
                        $("#amount").val("Invalid!");
                    }
                }
                $("#amount").hide();
                $("#amount").slideDown("slow");
                $("#amount").focus();
                return false; // Stop iterating.
            }
        });
    });

    // Form handler function.
    function onFormSubmit()
    {
        var oTable = $('#accounts-table').dataTable();
        var accounts = [];

        $("input[name='accounts']:checked", oTable.fnGetNodes()).each(function() {
            accounts.push(this.value);
        });
        
        if (accounts.length == 0) {
            bootbox.dialog({
                message: "Please select at least one account!",
                title: "Warning!",
                buttons: {
                    warning: {
                        label: "OK",
                        className: "btn-danger"
                    }
                }
            });
        } else {
            console.log("amount: " + $("#amount").val());

            var msg1 = "Apply '" + $("#memo").val() + "' for "
                + $("#amount").val() + " dollars on " + $("#date").val() + " to each"
                + " of the following account(s)?";
            
            var msg2 = "<ul class='two_columns'>";
            for (var i = 0; i < accounts.length; i++) {
                msg2 += "<li class='two_columns'>" + accounts[i] + "</li>";
            }
            msg2 += "</ul>";
            
            bootbox.confirm(msg1 + msg2, function (result)
            {
                if (result) {
                    console.log("Applying amount " + $("#amount").val() + "...");

                    bootbox.dialog({
                        message: "Updating ...",
                        closeButton: false
                    });
                    
                    var request = $.ajax({
                        type: "POST",
                        url: "enter/",
                        traditional: true,
                        data: {
                            amount: $("#amount").val(),
                            memo: $("#memo").val(),
                            category: $("#category").val(),
                            date: $("#date").val(),
                            accounts: accounts
                        },
                        dataType: "html"
                    });

                    request.done(function(msg) {
                        console.log("MSG: " + msg);
                        if (msg.toLowerCase().indexOf("invalid") >= 0) {
                            bootbox.hideAll();
                            msg = msg.replace("INVALID:", "");
                            bootbox.alert('Operation failed: ' + msg);
                            return;
                        }
                        
                        // 'msg' contains a list of accounts with updated balances:
                        // acctid1:bal2,acctId2:bal2,acctId3:bal3,
                        var newBalances = msg.split(',');
                        var acctsUpdated = 0;
                        for (var k = 0; k < (newBalances.length - 1); k++) {
                            var acctBalance = newBalances[k].split(':');
                            var acct = acctBalance[0];
                            var balance = acctBalance[1];
                            console.log(acct + ": " + balance);
                            // Update the account balance.
                            $("#" + acct, oTable.fnGetNodes()).text(balance);
                            // Uncheck the account.
                            $("#select_" + acct, oTable.fnGetNodes()).prop("checked", false);

                            ++acctsUpdated;
                        }

                        $("#select_all_head").prop("checked", false);
                        $("#select_all_foot").prop("checked", false);

                        if (0 == acctsUpdated) {
                            bootbox.hideAll();
                            bootbox.alert('No accounts were updated!');
                        } else {
                            // Refresh the page.
                            location.reload();
                        }
                    });

                    request.fail(function(jqXHR, textStatus) {
                        console.log("failure: " + textStatus);
                        bootbox.hideAll();
                        alert("Request failed: " + textStatus);
                    });
                } else {
                    console.log("Cancelled!");
                }
            });
        }
    }

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

    // Check the category for charge.
    function isCharge(category) {
        var bIsCharge = false;
        
        $.each(CHARGE_CATEGORIES, function (key, value) {
            if (key == category) {
                console.log("isCharge() - " + category + ": '" + value + "'");
                bIsCharge = true;
                return false; // Stop iterating.
            }
        });

        return bIsCharge;
    }

    // Error messages for the custom validation methods below.
    var ERROR_MSGS = { 
        POSITIVE: "Please enter a postive amount for a charge!",
        NEGATIVE: "Please enter a negative amount for a payment/credit!"
    };
    var errMsg = ERROR_MSGS.POSITIVE;

    var dispError = function() {
        return errMsg;
    };

    // Validate the sign of the amount.
    $.validator.addMethod("amount_sign", function(value, element, params) {
        var category = $("#category").val();
        if (category == "")
            return true;
        if (isCharge(category)) {
            if (value > 0)
                return true;
            else {
                errMsg = ERROR_MSGS.POSITIVE;
                return false;
            }
        } else {
            if (value >= 0) {
                errMsg = ERROR_MSGS.NEGATIVE;
                return false;
            } else
                return true;
        }
    }, dispError);

    // Validate the category.
    $.validator.addMethod("category_type", function(value, element, params) {
        var amount = $("#amount").val();
        if (amount == "")
            return true;
        if (isCharge(value)) {
            if (amount > 0)
                return true;
            else {
                errMsg = ERROR_MSGS.POSITIVE;
                return false;
            }
        } else {
            if (amount > 0) {
                errMsg = ERROR_MSGS.NEGATIVE;
                return false;
            } else {
                return true;
            }
        }
    }, dispError);

    // Validate the date.
    $.validator.addMethod("validDate", function (value, element) {
        var stamp = value;
        var validDateTime = !/Invalid|NaN/.test(new Date(stamp).toString());
        return this.optional(element) || (validDateTime);
    }, "Please enter a valid date.");
    
    // Validate the entry form.
    $("#entry-form").validate({
        submitHandler: function () {
            onFormSubmit();
        },
        rules: {
            amount: {
                number: true,
                required: true,
                amount_sign: true
            },
            category: {
                required: true,
                category_type: true
            },
            memo: {
                required: true
            },
            date: {
                validDate: true,
                required: true
            }
        }
    });
});

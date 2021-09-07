google.load('payments', '1.0', {
    'packages': ['sandbox_config']
});

/*
google.load('payments', '1.0', {
    'packages': ['production_config']
});
*/

// Success handler
var successHandler = function (status) {
    if (window.console != undefined) {
        console.log("Purchase completed successfully: ", status);
        //window.location.reload();
    }
}

// Failure handler
var failureHandler = function (status) {
    if (window.console != undefined) {
        console.log("Purchase failed ", status);
    }
}

// Function: purchase
function purchase(generated_jwt) {
    goog.payments.inapp.buy({
        'jwt': generated_jwt,
        'success': successHandler,
        'failure': failureHandler
    });
}

// Function: onMakePayment
function onMakePayment(form) {

    var amount = $("#id_amount", form.context).val();
    var scheduling = $("#id_scheduling", form.context).val();
    var description = $("#id_description").val();

    console.log("onMakePayment(amount: " + amount +
        ", scheduling: " + scheduling +
        ")");

    var jwtRq = $.ajax({
        type: "POST",
        url: "/payment/getjwt/",
        data: {
            amount: amount,
            scheduling: scheduling,
            description: description,
        },
    });

    jwtRq.done(function (token) {
        purchase(token);
    });

    jwtRq.fail(function (jqXhr, status) {
        console.log("jwtRq fail " + status);
    });

    jwtRq.always(function () {
        console.log("jwtRq always");
    });


    return false;
}
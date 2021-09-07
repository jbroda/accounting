///////////////////////////////////////////////////////////////////////////////
function capitalise(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

///////////////////////////////////////////////////////////////////////////////
function onChangeExisting(obj, objDom, idxForm) {
    var objId = objDom.val();

    var formSelector = "." + obj + idxForm + " ";

    if (objId == 0) {
        // Clear all fields in the form (except for account and lease).
        window["clear" + capitalise(obj) + "Form"](formSelector);

        // Enable input.
        window["make" + capitalise(obj) + "FormReadOnly"](formSelector, false);
    } else {
        // Request object's info.
        var request = $.ajax({
            type: "GET",
            url: "/accounting/" + obj + "/" + objId + "/",
            dataType: "json"
        });

        request.done(function (o) {
            // Set the retrieved info in the form.
            var data = $.parseJSON(o);
            $.each(data[0].fields, function (field, value) {
                if (field != "account" && field != "lease") {
                    $(formSelector + "[id$='" + field + "']" ).val(value);
                }
            });

            // Disable input.
            window["make" + capitalise(obj) + "FormReadOnly"](formSelector, true);
        });

        request.fail(function (jqXhr, textStatus) {
            console.log("failure: " + textStatus);
        });
    }
}

///////////////////////////////////////////////////////////////////////////////
function configureTab(obj) {

    var tabName = obj + "Tab";
    var tabSelector = "#" + tabName;
    var tabNameIndex = tabName + "Index";

    // Initialize the click handler.
    $(tabSelector + " a").click(function (e) {
        e.preventDefault();

        if ($(this).parent('li').hasClass('active'))
        {
            // Remove the 'active' class from the tab button.
            $(this).parent('li').removeClass('active');

            // Remove the 'active' class from the tab content.
            var contentTab = "#" + obj + "TabContent";
            var idx = $(this).parent().index();
            $(contentTab + " > div").eq(idx).removeClass('active');

            // Remove the tab index from the cookie.
            $.cookie(tabNameIndex, -1);
        }
        else
        {
            $(this).tab('show');

            // Update the tab index cookie.
            var tabIndex = $(this).parent().index();
            $.cookie(tabNameIndex, tabIndex);
        }
    });

    // Retrieve the tab index from the tab index cookie.
    var myTabIndex = $.cookie(tabNameIndex);
    if (myTabIndex == null) {
        // Inititalize the index cookie.
        myTabIndex = -1;
        $.cookie(tabNameIndex, myTabIndex);
    }

    // Show the tab with the given tab index.
    if (myTabIndex != -1) {
        $(tabSelector + " li:eq(" + myTabIndex + ") a").tab("show");
    }

    // Enable tooltips.
    $("#existing_" + obj + "_id").tooltip();
    $("#existing_" + obj + "_id_label").tooltip();

    $("#existing_" + obj + "_id").change(function () {
        onChangeExisting(obj, $(this), 0);
    });
}

///////////////////////////////////////////////////////////////////////////////
function OnTenantFormAdded(row) {
    var existingId = $(row[0]).find("[id$='existing_tenant_id']");

    var idxForm = $(".dynamic-form").index(row[0]);

    $(existingId[0]).change(function() {
        onChangeExisting("tenant", $(this), idxForm);
    });
}

///////////////////////////////////////////////////////////////////////////////
function OnTenantFormRemoved(row) {
}

///////////////////////////////////////////////////////////////////////////////
$(document).ready(function() {

    var hash = $(location).attr('hash');
    if (hash != "") {
        console.log("showing" + hash);
        $(hash).collapse('show');
    }

    var collapsibles = ['#owners', '#lease', '#vehicles'];
    for (var obj in collapsibles) {
        var collapsible = collapsibles[obj];
        $(collapsible).on('shown.bs.collapse', (function(c) {
            return function() {
                $(location).attr('hash', c);
            };}) (collapsible));
        }

    configureTab("owner");

    configureTab("tenant");

    configureTab("lease");

    configureTab("vehicle");
});
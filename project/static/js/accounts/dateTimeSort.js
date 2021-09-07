// Pattern for date and time, e.g: 01/01/2015, 12:34:10 p.m.
var dateTimePattern =
    /(\d{1,2})\/(\d{1,2})\/(\d{2,4}), (\d{1,2}):(\d{1,2}):(\d{1,2}) (a.m.|p.m.|am|pm|AM|PM|Am|Pm)/;

// Sort by US date and time.
function dateTimeSort(a) {
    if (a == null)
        return '';

    var b = a.match(dateTimePattern),
        month = b[1],
        day   = b[2],
        year  = b[3],
        hour  = b[4],
        min   = b[5],
        sec   = b[6],
        ampm  = b[7];

    if (ampm) {
        ampm = ampm.toLowerCase();

        // Remove '.' from 'a.m.' or 'p.m.'
        ampm = ampm.replace(/\./g, '');
    }

    if (hour == '12') {
        hour = '0';
    }

    if (ampm == 'pm') {
        hour = parseInt(hour, 10) + 12;
    }

    if (year.length == 2) {
        if (parseInt(year, 10) < 70) {
            year = '20' + year;
        }
        else {
            year = '19' + year;
        }
    }

    if (month.length == 1) {
        month = '0' + month;
    }

    if (day.length == 1) {
        day = '0' + day;
    }

    if (hour.length == 1) {
        hour = '0' + hour;
    }

    if (min.length == 1) {
        min = '0' + min;
    }

    if (sec.length == 1) {
        sec = '0' + sec;
    }

    var tt = (year + month + day + hour + min + sec);
    return tt;
}

// Function for detecting the type 'datetime' in a data table.
function dateTimeSortType(sData) {
   if (sData !== null && sData.match(dateTimePattern)) {
       return 'datetime-us';
   }
   return null;
}

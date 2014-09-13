var urls = [];
var tour_i = 0;
var iterate_tour = true;

function run_tour() {
    if (!urls) {
        // At the end, time to reset
    }

    if (tour_i >= urls.length) {
        get_urls();
        return;
    }
    if (!iterate_tour) {
        return;
    }
    
    set_page(urls[tour_i]);
    tour_i++;

    $('#tour').load(function() {
        setTimeout(run_tour, 4500);
    });
}

function get_urls() {
    $.getJSON("rtour_json", function(data) {
        urls = data['urls'];
        run_tour();
    });
}

function set_page(url) {
    $('#tour').attr('src', url);
}

$(document).ready(function() {
    $('#start').hide();
    $('#stop').click(function () {
        iterate_tour = false;
        $('#start').show();
        $('#stop').hide();
    });
    $('#start').click(function () {
        iterate_tour = true;
        $('#stop').show();
        $('#start').hide();
        run_tour();
    });
    run_tour();
});

var urls = [];
var tour_i = 0;
var iterate_tour = true;
var seed = null;
var z_index = 10;
var page = 0;

function run_tour(flip) {
    // First run
    if (urls.length == 0) {
        get_urls(flip);
        return;
    }
    // At the end, time to reset
    if (tour_i >= urls.length) {
        get_urls(flip);
        return;
    }
    if (!iterate_tour) {
        return;
    }
    
    set_page(urls, tour_i, flip);
    tour_i++;

    $('#tour' + flip).unbind('load');
    $('#tour' + flip).load(function() {
        flip = (flip + 1) % 2;
        setTimeout(function(){ run_tour(flip); }, 1800);
    });
}

function get_urls(flip) {
    var get_url = "/_explore/rtour_json/";
    if (typeof(region_slug) != 'undefined' && region_slug) {
        get_url = "/" + region_slug + get_url;
    }
    get_url += '?';
    if (seed) {
        get_url += ('&s=' + seed);
    }
    if (page) {
        get_url += ('&page=' + page);
    }
    $.getJSON(get_url, function(data) {
        urls = data['urls'];
        seed = data['random_seed'];
        tour_i = 0;
        page += 100;  // From explore.views items_per_page
        if (urls.length > 0) {
            run_tour(flip);
        }
    });
}

function set_page(urls, tour_i, flip) {
    var url = urls[tour_i];

    $('#tour' + flip).attr('src', url);
    // Hide behavior is different on the first run
    if (!(tour_i == 0 && page == 100)) {
        flip = (flip + 1) % 2;
        $('#tour' + flip).css('z-index', ++z_index);
    }
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
        run_tour(0);
    });
    run_tour(0);
});

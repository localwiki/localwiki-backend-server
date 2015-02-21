$(window).load(function() {
    window.loaded = true;
});

/* Show login/logout in #nav when screen is small. */
function add_login_info_actions() {
    $('#login_info .actions a').each(function() {
        var item = $('<li>');
        item.attr('class', 'remove');
        item.append($(this).clone());
        $('#nav ul').append(item);
    });
};

function hide_login_info_actions() {
    $("#nav ul li.remove").remove()
};

$(function() {
    enquire.register("screen and (max-width:500px)", {
        match: add_login_info_actions,
        unmatch: hide_login_info_actions,
    });
    enquire.listen(); 
});

/* hide-address-bar.js. inlined for speed */
/*! Normalized address bar hiding for iOS & Android (c) @scottjehl MIT License */
(function( win ){
	var doc = win.document;
	
	// If there's a hash, or addEventListener is undefined, stop here
	if( !location.hash && win.addEventListener ){
		
		//scroll to 1
		win.scrollTo( 0, 1 );
		var scrollTop = 1,
			getScrollTop = function(){
				return win.pageYOffset || doc.compatMode === "CSS1Compat" && doc.documentElement.scrollTop || doc.body.scrollTop || 0;
			},
		
			//reset to 0 on bodyready, if needed
			bodycheck = setInterval(function(){
				if( doc.body ){
					clearInterval( bodycheck );
					scrollTop = getScrollTop();
					win.scrollTo( 0, scrollTop === 1 ? 0 : 1 );
				}	
			}, 15 );
		
		win.addEventListener( "load", function(){
			setTimeout(function(){
				//at load, if user hasn't scrolled more than 20 or so...
				if( getScrollTop() < 20 ){
					//reset to hide addr bar at onload
					win.scrollTo( 0, scrollTop === 1 ? 0 : 1 );
				}
			}, 0);
		}, false );
	}
})( this );

/* For our little responsive menu toggler */
$(function() {  
    var pull = $('#pull');  
    menu = $('#nav ul');  
    menuHeight = menu.height();  
  
    $(pull).on('click', function(e) {  
        e.preventDefault();  
        menu.slideToggle(300);
    });  

    $(window).resize(function(){  
        var w = $(window).width();  
        if(w > 320 && menu.is(':hidden')) {  
            menu.removeAttr('style');  
        }  
    });
});

/* For twitter typeahead */
$(document).ready(function() {
    if (region_id) {
        var pages_remote_url = '/_api/pages/suggest?term=%QUERY&region_id=' + region_id;
    }
    else {
        var pages_remote_url = '/_api/pages/suggest?term=%QUERY';
    }
    var autoRegions = new Bloodhound({
        datumTokenizer: Bloodhound.tokenizers.whitespace('value'),
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        remote: '/_api/regions/suggest?term=%QUERY'
    });
    var autoPages = new Bloodhound({
        datumTokenizer: Bloodhound.tokenizers.whitespace('value'),
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        remote: pages_remote_url
    });
    autoRegions.initialize();
    autoPages.initialize();

    if (region_id) {
        $('#id_q').typeahead(null,
            {
              name: 'pages',
              source: autoPages.ttAdapter()
            },
            {
                // Footer: search within this region
                source: function(q, cb) {
                    if (window.location.host == home_hostname) {
                        var search_url = '/_rsearch/' + region_slug + '?q=' + q;
                    } else {
                        var search_url = '/_rsearch/' + '?q=' + q;
                    }
                    return cb([{'value': q, 'url': search_url }]);
                },
                templates: {
                    header: Handlebars.compile('<div class="autocomplete_divider"></div>'),
                    suggestion: Handlebars.compile("<p>" +
                        gettext('Search for "{{ value }}"') +
                        "</p>"
                    )
                }
            },
            {
                // Footer: search all of LocalWiki
                source: function(q, cb) {
                    return cb([{'value': q, 'url': '//' + home_hostname + '/_search/?q=' + q}]);
                },
                templates: {
                    header: Handlebars.compile('<div class="autocomplete_divider"></div>'),
                    suggestion: Handlebars.compile(
                        "<p>" +
                        gettext("Search all of LocalWiki") +
                        "</p>"
                    )
                }
            }
        )
        .on('typeahead:selected', function(e, datum) {
            document.location = datum.url;
        });
    }
    else {
        
        $('#id_q').typeahead(null,
            {
              name: 'regions',
              source: autoRegions.ttAdapter(),
              templates: {
                suggestion: Handlebars.compile("<p><strong>{{ value }}</strong> &mdash; {{ slug }}</p>")
              }
            },
            {
              name: 'pages',
              source: autoPages.ttAdapter(),
              templates: {
                header: Handlebars.compile('<div class="autocomplete_divider"></div>'),
                suggestion: Handlebars.compile("<p><strong>{{ value }}</strong> &mdash; {{ region }}</p>")
              }
            },
            {
                // Footer: Do search as usual
                source: function(q, cb) {
                    return cb([{'value': q, 'url': '/_search/?q=' + q}]);
                },
                templates: {
                    header: Handlebars.compile('<div class="autocomplete_divider"></div>'),
                    suggestion: Handlebars.compile(
                        "<p>" +
                        gettext("Search all of LocalWiki") +
                        "</p>"
                    )
                }
            }
        )
        .on('typeahead:selected', function(e, datum) {
            document.location = datum.url;
        });
    }

    /* Just-region pull-down / search selector */
    if ($('#id_region_q')) {
       $('#id_region_q').typeahead(null,
            {
              name: 'regions',
              source: autoRegions.ttAdapter(),
              templates: {
                suggestion: Handlebars.compile("<p><strong>{{ value }}</strong> &mdash; {{ slug }}</p>"),
              }
            },
            {
                // Footer: Do search as usual
                source: function(q, cb) {
                    return cb([{'value': q, 'url': '/_search/?q=' + q}]);
                },
                templates: {
                    header: Handlebars.compile('<div class="autocomplete_divider"></div>'),
                    suggestion: Handlebars.compile(
                        "<p>" +
                        gettext("Search all of LocalWiki") +
                        "</p>"
                    )
                }
            }
        )
        .on('typeahead:selected', function(e, datum) {
            document.location = datum.url;
        });
    }
    
});

var setup_lazy_csrf = function(selector) {
  $(selector).submit(function() {
    var form = $(this)[0];
    set_django_tokens(form, function() {
        $(selector)[0].submit();
    });
    return false;
  });
}

/* Lazy CSRF for page tag edit */
$(document).ready(function () {
    setup_lazy_csrf('#pagetagset_form');
    setup_lazy_csrf('#file_replace_upload');
    setup_lazy_csrf('.new_tagged_page form');
});

/* Add page button */
$(document).ready(function() {
    $('#new_page_button').click(function() {
       $(this).hide()
       $('#new_page_form').show();
       $('#new_page_form #pagename').focus();
    });
});

/* Add new tagged-page button */
$(document).ready(function() {
    var pages_remote_url = '/_api/pages/suggest?term=%QUERY&region_id=' + region_id;
    var autoPages = new Bloodhound({
        datumTokenizer: Bloodhound.tokenizers.whitespace('value'),
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        remote: pages_remote_url
    });
    autoPages.initialize();

    $('.new_tagged_page .start').click(function() {
       $(this).parent().find('.page_name').typeahead(null,
           {
             name: 'new_tagged_pages',
             source: autoPages.ttAdapter()
           }
       )
       .on('typeahead:selected', function(e, datum) {
          var pagename = datum.value;
          $(this).parent().find('form .page_name').val(pagename);
          var form = $(this).parent().parent().parent().find('form');
          form.submit();
       });

       $(this).parent().find('.start').hide();
       $(this).parent().find('form').show();
       $(this).parent().find('form .page_name').focus();

    });
});

/* Follow button */
$(document).ready(function () {
  if ($('.follow_item form')) {
        $('.follow_item').each(function() {
            var follow_item = $(this);
            var form = $(this).find('form')[0];
            var follow_url = $(form).attr('action');
            var followData = $(form).serializeArray();
            var unfollow = function() {
                $.post(
                    follow_url,
                    followData
            
                ).done(function() {
                    var item = $(follow_item.find('.unfollow')[0]);
                    item.addClass('follow'); 
                    item.removeClass('unfollow'); 
                    item.unbind();
                    item.click(follow);
                })
            };
            var follow = function() {
                $.post(
                    follow_url,
                    followData
                ).done(function() {
                    var item = $(follow_item.find('.follow')[0]);
                    item.addClass('unfollow'); 
                    item.removeClass('follow'); 
                    item.unbind();
                    item.click(unfollow);
                });
            };

            $($(this).find('.unfollow')[0]).click(function () {
                $(this).unbind();
                unfollow();
            });
            $($(this).find('.follow')[0]).click(function () {
                $(this).unbind();
                follow();
            });

        });
    }
});


function getCookie(key) {
    var result;
    // adapted from the jQuery Cookie plugin
    return (result = new RegExp('(?:^|; )' + encodeURIComponent(key) + '=([^;]*)').exec(document.cookie)) ? decodeURIComponent(result[1]) : null;
}

function set_django_tokens(form, cb) {
    // Patch the form -- add the CSRF token and honeypot fields

    if (!cb) {
        var cb = function() {};
    }
    
    var _setup_tokens = function(csrf_cookie) {
        csrf = form.ownerDocument.createElement('input');
        csrf.setAttribute('name', 'csrfmiddlewaretoken');
        csrf.setAttribute('type', 'hidden');
        csrf.setAttribute('value', csrf_cookie);
        form.appendChild(csrf);
        
        /* TODO: make this automatic, this is hardcoded to the django-honeypot settings */
        honeypot = form.ownerDocument.createElement('input');
        honeypot.setAttribute('name', 'main_content');
        honeypot.setAttribute('type', 'hidden');
        form.appendChild(honeypot);
        honeypot_js = form.ownerDocument.createElement('input');
        honeypot_js.setAttribute('name', 'main_content_js');
        honeypot_js.setAttribute('type', 'hidden');
        form.appendChild(honeypot_js);
    }

    var csrf_cookie = getCookie('csrftoken');
    if (!csrf_cookie) {
        $.get('/_api/_get/csrf_cookie', function() {
            var csrf_cookie = getCookie('csrftoken');
            _setup_tokens(csrf_cookie);
            cb();
        });
    }
    else {
        _setup_tokens(csrf_cookie);
        cb();
    }
}

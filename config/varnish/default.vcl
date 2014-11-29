# This is a basic VCL configuration file for varnish.  See the vcl(7)
# man page for details on VCL syntax and semantics.
# 
# Default backend definition.  Set this to point to your content
# server.

backend localwiki { 
    .host = "127.0.0.1";
    .port = "8084";

    .connect_timeout = 600s;
    .first_byte_timeout = 600s;
    .between_bytes_timeout = 600s;
}


backend splash { 
    .host = "71.19.144.195";
    .port = "80";

    .connect_timeout = 600s;
    .first_byte_timeout = 600s;
    .between_bytes_timeout = 600s;
}

sub vcl_recv {
    # unless sessionid/csrftoken/messages is in the request, don't pass ANY cookies (referral_source, utm, etc)
    if (req.request == "GET" && (req.url ~ "^/static" || req.url ~ "^/media" || (req.http.cookie !~ "sessionid" && req.http.cookie !~ "csrftoken" && req.http.cookie !~ "messages"))) {
        remove req.http.Cookie;
    }
    # Some Django URLs to always, always cache.
    if (req.request == "GET" && (req.url ~ "^/jsi18n/")) {
        remove req.http.Cookie;
    }

    # Allow the backend to serve up stale content if it is responding slowly.
    set req.grace = 6h;

    # XXX TODO TEMPORARY UNTIL SPLASH SITE IS FULLY INTEGRATED
    # REMOVE THIS CONDITIONAL AFTER
    if (req.url ~ "^/blog" || req.url ~ "^/about" || req.url ~ "^/donate" || req.url ~ "^/signup" || req.url ~ "^/_start_new" || req.url ~ "^/static_old" || req.url ~ "^/media_old") {

        # In these cases, always serve from the old splash site backend
        set req.backend = splash;
    }
    else {
        # XXX TODO TEMPORARY UNTIL SPLASH SITE IS FULLY INTEGRATED
        # REMOVE THIS CONDITIONAL AFTER
        if (req.http.cookie !~ "sessionid" && req.url ~ "^/$") {
            # Serve main page from splash backend if not logged in
            set req.backend = splash;
        }
        else {
            # XXX TODO extract this bit back up after splash
            # is integrated:
            if (req.http.x-forwarded-host == "www.localwiki.org" || req.http.x-forwarded-host == "localwiki.org") {
               set req.http.host = "localwiki.org";
               set req.backend = localwiki;
            } else {
               set req.http.host = req.http.x-forwarded-host;
               set req.backend = localwiki;
            }
        }
    }

    if (req.http.x-forwarded-for) {
       set req.http.X-Forwarded-For =
           req.http.X-Forwarded-For + ", " + client.ip;
    } else {
       set req.http.X-Forwarded-For = client.ip;
    }

    if (req.http.X-Forwarded-Proto == "https" ) {
        set req.http.X-Forwarded-Port = "443";
    } else {
        set req.http.X-Forwarded-Port = "80";
        set req.http.X-Forwarded-Proto = "http";
    }

    if (req.request != "GET" &&
      req.request != "HEAD" &&
      req.request != "PUT" &&
      req.request != "POST" &&
      req.request != "TRACE" &&
      req.request != "OPTIONS" &&
      req.request != "DELETE") {
        /* Non-RFC2616 or CONNECT which is weird. */
        return (pipe);
    }
    if (req.request != "GET" && req.request != "HEAD") {
        /* We only deal with GET and HEAD by default */
        return (pass);
    }
    return (lookup);
}

sub vcl_hash {
  if (req.http.X-Forwarded-Proto) {
     hash_data(req.http.X-Forwarded-Proto);
  }
}

sub vcl_fetch {
    /* Set URL and Host on object for ban-reaper purposes */
    set beresp.http.x-url = req.url;
    set beresp.http.x-host = req.http.host;

    if (beresp.ttl > 0s && beresp.http.X-KEEPME) {
        /* Remove Expires from backend, it's not long enough */
        unset beresp.http.expires;

        /* Set the clients TTL on this object */
        set beresp.http.cache-control = "max-age=900";

        /* Set how long Varnish will keep it */
        set beresp.ttl = 52w;

        /* marker for vcl_deliver to reset Age: */
        set beresp.http.magicmarker = "1";
    }

    # XXX TODO TEMPORARY UNTIL SPLASH SITE IS FULLY INTEGRATED
    # REMOVE THIS CONDITIONAL AFTER
    if (req.url ~ "^/blog" || req.url ~ "^/about" || req.url ~ "^/donate" || req.url ~ "^/signup" || req.url ~ "^/_start_new" || req.url ~ "^/static_old" || req.url ~ "^/media_old" || (req.http.cookie !~ "sessionid" && req.url ~ "^/$")) {
       unset beresp.http.set-cookie;
       /* Remove Expires from backend, it's not long enough */
        unset beresp.http.expires;

        /* Set the clients TTL on this object */
        set beresp.http.cache-control = "max-age=900";

        /* Set how long Varnish will keep it */
        set beresp.ttl = 2h;

        set beresp.http.magicmarker = "1";
        return (deliver);
    }

    # static files always cached
    if (req.url ~ "^/static" || req.url ~ "^/media") {
       unset beresp.http.set-cookie;
       return (deliver);
    }

    # Hardcoded Django URLs to always cache.
    if (req.url ~ "^/jsi18n/") {
       unset beresp.http.set-cookie;
       return (deliver);
    }

    # pass through for anything with a session/csrftoken/messages set
    if (beresp.http.set-cookie ~ "sessionid" || beresp.http.set-cookie ~ "csrftoken" || beresp.http.set-cookie ~ "messages") {
       return (hit_for_pass);
    } else {
       return (deliver);
    }
}

sub vcl_deliver {
    if (resp.http.x-url) {
       unset resp.http.x-url;
    }
    if (resp.http.x-host) {
       unset resp.http.x-host;
    }
    if (resp.http.X-KEEPME) {
       unset resp.http.X-KEEPME;
    }
     if (resp.http.magicmarker) {
        /* Remove the magic marker */
        unset resp.http.magicmarker;

	/* By definition we have a fresh object */
        set resp.http.age = "0";
    }
    return (deliver);
}

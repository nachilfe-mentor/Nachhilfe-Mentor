(function () {
  var POSTHOG_KEY = "phc_lGrnsri0QNMf2aR5OQh8bZ4lEUCDbxucJJIG90mgV8e";
  var POSTHOG_HOST = "https://eu.i.posthog.com";
  var SCROLL_MARKS = [25, 50, 75, 90];
  var trackedScrollMarks = {};
  var articleCompleteTracked = false;

  if (window.__nachhilfeMentorPostHogLoaded) return;
  window.__nachhilfeMentorPostHogLoaded = true;

  !function (t, e) {
    var o, n, p, r;
    e.__SV || (window.posthog = e, e._i = [], e.init = function (i, s, a) {
      function g(t, e) {
        var o = e.split(".");
        if (o.length === 2) {
          t = t[o[0]];
          e = o[1];
        }
        t[e] = function () {
          t.push([e].concat(Array.prototype.slice.call(arguments, 0)));
        };
      }
      p = t.createElement("script");
      p.type = "text/javascript";
      p.crossOrigin = "anonymous";
      p.async = true;
      p.src = s.api_host.replace(".i.posthog.com", "-assets.i.posthog.com") + "/static/array.js";
      r = t.getElementsByTagName("script")[0];
      r.parentNode.insertBefore(p, r);
      var u = e;
      if (a !== undefined) {
        u = e[a] = [];
      } else {
        a = "posthog";
      }
      u.people = u.people || [];
      u.toString = function (t) {
        var e = "posthog";
        if (a !== "posthog") e += "." + a;
        if (!t) e += " (stub)";
        return e;
      };
      u.people.toString = function () {
        return u.toString(1) + ".people (stub)";
      };
      o = "init capture register register_once register_for_session unregister unregister_for_session getFeatureFlag getFeatureFlagPayload isFeatureEnabled reloadFeatureFlags updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures on onFeatureFlags onSessionId getSurveys getActiveMatchingSurveys renderSurvey canRenderSurvey getNextSurveyStep identify setPersonProperties group resetGroups setPersonPropertiesForFlags resetPersonPropertiesForFlags setGroupPropertiesForFlags reset resetGroups get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException loadToolbar get_property getSessionProperty createPersonProfile opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing clear_opt_in_out_capturing debug".split(" ");
      for (n = 0; n < o.length; n++) g(u, o[n]);
      e._i.push([i, s, a]);
    }, e.__SV = 1);
  }(document, window.posthog || []);

  posthog.init(POSTHOG_KEY, {
    api_host: POSTHOG_HOST,
    defaults: "2026-01-30",
    autocapture: true,
    capture_pageview: true,
    capture_pageleave: true,
    cookieless_mode: "always",
    person_profiles: "identified_only",
    session_recording: {
      maskAllInputs: true
    },
    before_send: function (event) {
      if (!event || !event.properties) return event;
      delete event.properties.$initial_person_info;
      delete event.properties.$person_processing_info;
      return event;
    }
  });

  function capture(name, props) {
    if (!window.posthog || typeof window.posthog.capture !== "function") return;
    window.posthog.capture(name, Object.assign(pageProps(), props || {}));
  }

  function pageProps() {
    return {
      site: "nachhilfe-mentor.de",
      page_path: window.location.pathname,
      page_title: document.title,
      page_type: pageType(),
      canonical_url: getCanonicalUrl()
    };
  }

  function pageType() {
    var originalPath = window.location.pathname;
    var path = originalPath.toLowerCase();
    if (path === "/" || path.endsWith("/index.html")) return "landing";
    if (path === "/blog/" || path === "/blog/index.html") return "blog_index";
    if (path.indexOf("/blog/posts/") === 0) return "blog_post";
    if (originalPath.indexOf("/Blog/") === 0) return "blog_legacy";
    if (path.indexOf("/blog/") === 0) return "blog_other";
    if (path.indexOf("/datenschutz") === 0 || path.indexOf("/datenschutzerklaerung") === 0 || path.indexOf("/impressum") === 0 || path.indexOf("/nutzungsbedingungen") === 0) return "legal";
    return "static_page";
  }

  function getCanonicalUrl() {
    var canonical = document.querySelector('link[rel="canonical"]');
    return canonical ? canonical.href : window.location.href.split("#")[0];
  }

  function labelFor(el) {
    return (el.getAttribute("data-ph-label") || el.getAttribute("aria-label") || el.textContent || "").replace(/\s+/g, " ").trim().slice(0, 120);
  }

  function storeForHref(href) {
    if (href.indexOf("play.google.com") !== -1) return "google_play";
    if (href.indexOf("apps.apple.com") !== -1) return "app_store";
    return "";
  }

  function sectionFor(el) {
    var section = el.closest("section[id], nav, footer, header, article, main");
    if (!section) return "";
    return section.id || section.tagName.toLowerCase();
  }

  function onClick(e) {
    var link = e.target.closest && e.target.closest("a[href]");
    if (!link) return;

    var href = link.href;
    var rawHref = link.getAttribute("href") || "";
    var store = storeForHref(href);
    var props = {
      href: href,
      raw_href: rawHref,
      label: labelFor(link),
      css_class: link.className || "",
      section: sectionFor(link)
    };

    if (store) {
      capture("app_download_click", Object.assign({ store: store }, props));
      return;
    }

    if (link.classList.contains("blog-card") || link.classList.contains("blog-card-link") || link.classList.contains("blog-card-img-link")) {
      capture("blog_card_click", props);
      return;
    }

    if (link.classList.contains("nav-link") || link.closest("nav")) {
      capture("nav_click", props);
      return;
    }

    if (href.indexOf("mailto:") === 0) {
      capture("contact_click", props);
      return;
    }

    if (link.hostname && link.hostname !== window.location.hostname) {
      capture("outbound_link_click", props);
      return;
    }

    if (rawHref.charAt(0) === "#") {
      capture("anchor_click", props);
    }
  }

  function scrollPercent() {
    var doc = document.documentElement;
    var body = document.body;
    var scrollTop = window.scrollY || doc.scrollTop || body.scrollTop || 0;
    var height = Math.max(body.scrollHeight, doc.scrollHeight, body.offsetHeight, doc.offsetHeight) - window.innerHeight;
    if (height <= 0) return 100;
    return Math.min(100, Math.round((scrollTop / height) * 100));
  }

  function onScroll() {
    var percent = scrollPercent();
    SCROLL_MARKS.forEach(function (mark) {
      if (percent >= mark && !trackedScrollMarks[mark]) {
        trackedScrollMarks[mark] = true;
        capture("scroll_depth", { percent: mark });
      }
    });

    if (!articleCompleteTracked && pageType() === "blog_post" && percent >= 90) {
      articleCompleteTracked = true;
      capture("blog_read_complete", articleProps());
    }
  }

  function articleProps() {
    var title = document.querySelector("h1");
    var tag = document.querySelector(".blog-tag");
    var readTime = Array.prototype.find.call(document.querySelectorAll(".blog-post-meta span"), function (el) {
      return /Lesezeit/.test(el.textContent || "");
    });
    return {
      article_title: title ? title.textContent.trim() : document.title,
      article_tag: tag ? tag.textContent.trim() : "",
      read_time_label: readTime ? readTime.textContent.trim() : ""
    };
  }

  function trackVisibleImages() {
    if (!("IntersectionObserver" in window)) return;
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var img = entry.target;
        observer.unobserve(img);
        capture("image_view", {
          image_src: img.currentSrc || img.src,
          image_alt: img.alt || "",
          section: sectionFor(img)
        });
      });
    }, { threshold: 0.5 });

    document.querySelectorAll("img").forEach(function (img) {
      observer.observe(img);
    });
  }

  function trackBlogPostView() {
    if (pageType() !== "blog_post") return;
    capture("blog_post_view", articleProps());
  }

  function trackLandingView() {
    if (pageType() !== "landing") return;
    capture("landing_page_view", {
      has_download_section: !!document.getElementById("download")
    });
  }

  function initTracking() {
    capture("website_page_ready");
    trackBlogPostView();
    trackLandingView();
    trackVisibleImages();
    document.addEventListener("click", onClick, true);
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("beforeunload", function () {
      capture("page_engagement_summary", {
        max_scroll_percent: scrollPercent()
      });
    });
    onScroll();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initTracking);
  } else {
    initTracking();
  }
})();

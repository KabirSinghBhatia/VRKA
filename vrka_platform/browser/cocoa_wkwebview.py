"""macOS Cocoa WKWebView browser verification driver.

Encapsulates PyObjC WKWebView behavior including immediate direct URL loading,
Cocoa delegate popup firewall suppression, cross-frame media stream observation
(injecting into nested and cross-origin iframes via WKUserScript), and comprehensive
cookie store extraction across all domains.
"""

from __future__ import annotations

import json
from pathlib import Path
from threading import Semaphore
from typing import Any, Callable

from vrka_platform.browser.base import BrowserVerificationDriver


CROSS_FRAME_MEDIA_OBSERVER_JS = """
(function() {
    if (window.__vrkaHooked) return;
    window.__vrkaHooked = true;

    function report(item) {
        try {
            if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.vrkaMediaBridge) {
                window.webkit.messageHandlers.vrkaMediaBridge.postMessage(item);
            }
        } catch (_) {}
    }

    // Intercept fetch API across all browsing contexts (main frame & iframes)
    if (window.fetch) {
        const origFetch = window.fetch;
        window.fetch = function(...args) {
            const req = args[0];
            let url = typeof req === 'string' ? req : (req && req.url ? req.url : '');
            let method = (args[1] && args[1].method) || (req && req.method) || 'GET';
            if (url) {
                try { url = new URL(url, location.href).href; } catch(_) {}
                report({
                    kind: 'request',
                    source: 'fetch',
                    url: url,
                    method: method,
                    headers: { 'referer': location.href, 'origin': location.origin }
                });
            }
            return origFetch.apply(this, args).then(response => {
                try {
                    if (url && response) {
                        const ctype = response.headers.get('content-type') || '';
                        const clen = response.headers.get('content-length') || '';
                        report({
                            kind: 'response',
                            source: 'fetch',
                            url: response.url || url,
                            status: response.status,
                            content_type: ctype,
                            content_length: clen,
                            headers: { 'referer': location.href, 'origin': location.origin }
                        });
                    }
                } catch (_) {}
                return response;
            });
        };
    }

    // Intercept XMLHttpRequest across all browsing contexts
    if (window.XMLHttpRequest) {
        const origOpen = XMLHttpRequest.prototype.open;
        const origSend = XMLHttpRequest.prototype.send;
        XMLHttpRequest.prototype.open = function(method, url, ...rest) {
            try {
                this.__vrkaUrl = new URL(String(url), location.href).href;
            } catch(_) {
                this.__vrkaUrl = String(url);
            }
            this.__vrkaMethod = method;
            try {
                report({
                    kind: 'request',
                    source: 'xhr',
                    url: this.__vrkaUrl,
                    method: method,
                    headers: { 'referer': location.href, 'origin': location.origin }
                });
            } catch (_) {}
            return origOpen.call(this, method, url, ...rest);
        };
        XMLHttpRequest.prototype.send = function(...args) {
            this.addEventListener('load', function() {
                try {
                    if (this.__vrkaUrl) {
                        const ctype = this.getResponseHeader('content-type') || '';
                        const clen = this.getResponseHeader('content-length') || '';
                        report({
                            kind: 'response',
                            source: 'xhr',
                            url: this.responseURL || this.__vrkaUrl,
                            status: this.status,
                            content_type: ctype,
                            content_length: clen,
                            headers: { 'referer': location.href, 'origin': location.origin }
                        });
                    }
                } catch (_) {}
            });
            return origSend.apply(this, args);
        };
    }

    // Scan for embedded player globals (JWPlayer, Video.js, custom stream objects)
    function scanGlobals() {
        try {
            if (window.masterPlaylist && window.masterPlaylist.url) {
                report({
                    kind: 'response',
                    source: 'dom_stream',
                    url: new URL(window.masterPlaylist.url, location.href).href,
                    content_type: 'application/vnd.apple.mpegurl',
                    status: 200,
                    headers: { 'referer': location.href, 'origin': location.origin }
                });
            }
            if (window.streams && Array.isArray(window.streams)) {
                window.streams.forEach(s => {
                    if (s && s.url) {
                        report({
                            kind: 'response',
                            source: 'dom_stream',
                            url: new URL(s.url, location.href).href,
                            content_type: 'application/vnd.apple.mpegurl',
                            status: 200,
                            headers: { 'referer': location.href, 'origin': location.origin }
                        });
                    }
                });
            }
        } catch (_) {}
    }

    // Watch video and audio DOM elements inside this frame
    function watchMediaElements() {
        try {
            scanGlobals();
            document.querySelectorAll('video, audio, source').forEach(node => {
                const src = node.currentSrc || node.src;
                if (src && !src.startsWith('blob:')) {
                    try {
                        const absUrl = new URL(src, location.href).href;
                        report({
                            kind: 'request',
                            source: 'dom',
                            url: absUrl,
                            headers: { 'referer': location.href, 'origin': location.origin }
                        });
                    } catch (_) {}
                }
                if (node.tagName && (node.tagName.toLowerCase() === 'video' || node.tagName.toLowerCase() === 'audio')) {
                    ['canplay', 'playing', 'loadeddata'].forEach(ev => {
                        const flag = '__vrka_' + ev;
                        if (!node[flag]) {
                            node[flag] = true;
                            node.addEventListener(ev, () => {
                                report({ kind: 'playable', source: ev, url: node.currentSrc || node.src || location.href });
                            });
                        }
                    });
                    if (node.readyState >= 3 || (!node.paused && node.currentTime > 0)) {
                        report({ kind: 'playable', source: 'state', url: node.currentSrc || node.src || location.href });
                    }
                }
            });
        } catch (_) {}
    }

    setInterval(watchMediaElements, 500);
    watchMediaElements();
})();
"""


class CocoaWKWebViewDriver(BrowserVerificationDriver):
    """Browser verification driver using Apple WebKit (WKWebView) on macOS."""

    def prepare_environment(self) -> None:
        """macOS WebKit requires no special external runtime paths or extensions."""
        pass

    def get_initial_url(self, start_url: str) -> str:
        """macOS Cocoa WKWebView loads the start URL directly without blank-screen delay."""
        return start_url

    def install_security_guards(self, window: Any, popup_stats: dict[str, Any]) -> None:
        """Install Cocoa delegate hook to intercept and suppress popup windows."""
        try:
            import webview.platforms.cocoa as cocoa

            def _block_cocoa_popup(self_delegate, webview_inst, config, action, features):
                req_url = ""
                try:
                    req_url = str(action.request().URL().absoluteString() or "")
                except Exception:
                    pass
                if req_url:
                    popup_stats.setdefault("blocked_urls", []).append(req_url)
                    popup_stats["blocked"] = popup_stats.get("blocked", 0) + 1
                return None

            # Suppress disruptive modal JavaScript alert, confirm, and prompt dialogs
            def _suppress_alert(self_delegate, webview, message, frame, handler):
                try:
                    handler()
                except Exception:
                    pass

            def _suppress_confirm(self_delegate, webview, message, frame, handler):
                try:
                    handler(True)
                except Exception:
                    pass

            def _suppress_prompt(self_delegate, webview, prompt, default_text, frame, handler):
                try:
                    handler("")
                except Exception:
                    pass

            cocoa.BrowserView.BrowserDelegate.webView_createWebViewWithConfiguration_forNavigationAction_windowFeatures_ = (
                _block_cocoa_popup
            )
            cocoa.BrowserView.BrowserDelegate.webView_runJavaScriptAlertPanelWithMessage_initiatedByFrame_completionHandler_ = (
                _suppress_alert
            )
            cocoa.BrowserView.BrowserDelegate.webView_runJavaScriptConfirmPanelWithMessage_initiatedByFrame_completionHandler_ = (
                _suppress_confirm
            )
            cocoa.BrowserView.BrowserDelegate.webView_runJavaScriptTextInputPanelWithPrompt_defaultText_initiatedByFrame_completionHandler_ = (
                _suppress_prompt
            )
            popup_stats["native_guard_installed"] = True
            popup_stats["guard_error"] = ""
        except Exception as exc:
            popup_stats["guard_error"] = f"Cocoa popup guard: {exc}"

    def install_media_observer(
        self,
        window: Any,
        observation_callback: Callable[[dict[str, Any]], None],
        playable_callback: Callable[[str], None] | None = None,
    ) -> bool:
        """Install WebKit cross-frame user script and script message handler to observe media in all frames."""
        try:
            import threading
            import time
            import objc
            import Foundation
            import AppKit
            import WebKit
            import webview.platforms.cocoa as cocoa

            # Thread-safe and deadlock-free evaluate_js wrapper for pywebview Cocoa
            eval_lock = threading.Lock()

            def _threadsafe_evaluate_js(bview_self, script, parse_json=True):
                # If invoked directly on the AppKit main thread, do not block with a semaphore
                # which causes a permanent deadlock with AppHelper.callAfter
                if AppKit.NSThread.isMainThread():
                    res_box = [None]
                    done_box = [False]

                    def _sync_handler(res, err):
                        if parse_json and res:
                            try:
                                res_box[0] = json.loads(res)
                            except Exception:
                                res_box[0] = res
                        else:
                            res_box[0] = res
                        done_box[0] = True

                    try:
                        bview_self.webview.evaluateJavaScript_completionHandler_(script, _sync_handler)
                    except Exception:
                        return None

                    limit = time.time() + 5.0
                    while not done_box[0] and time.time() < limit:
                        AppKit.NSRunLoop.currentRunLoop().runMode_beforeDate_(
                            AppKit.NSDefaultRunLoopMode,
                            Foundation.NSDate.dateWithTimeIntervalSinceNow_(0.05),
                        )
                    return res_box[0]

                # Background thread: per-call Semaphore with bounded timeout
                sem = Semaphore(0)
                res_box = [None]

                def _handler(res, err):
                    try:
                        if parse_json and res:
                            try:
                                res_box[0] = json.loads(res)
                            except Exception:
                                res_box[0] = res
                        else:
                            res_box[0] = res
                    finally:
                        sem.release()

                def _eval():
                    try:
                        bview_self.webview.evaluateJavaScript_completionHandler_(script, _handler)
                    except Exception:
                        sem.release()

                with eval_lock:
                    cocoa.AppHelper.callAfter(_eval)
                    if sem.acquire(timeout=10.0):
                        return res_box[0]
                    return None

            cocoa.BrowserView.evaluate_js = _threadsafe_evaluate_js

            # Define PyObjC script message handler class
            class CocoaMediaScriptMessageHandler(Foundation.NSObject):
                def initWithCallback_andPlayable_(self, cb, pcb):
                    self = objc.super(CocoaMediaScriptMessageHandler, self).init()
                    if self is None:
                        return None
                    self._callback = cb
                    self._playable_cb = pcb
                    return self

                def userContentController_didReceiveScriptMessage_(self, controller, message):
                    try:
                        raw_body = message.body()
                        if hasattr(raw_body, "items"):
                            body = dict(raw_body)
                        elif isinstance(raw_body, dict):
                            body = raw_body
                        else:
                            body = {}
                        kind = body.get("kind")
                        if kind in ("request", "response") and self._callback:
                            self._callback(body)
                        elif kind == "playable" and self._playable_cb:
                            # CRITICAL: WebKit dispatches this method on the AppKit main thread.
                            # Calling capture_session() synchronously on the main thread would deadlock
                            # evaluate_js. Offload to a daemon thread immediately.
                            play_url = str(body.get("url") or "")
                            threading.Thread(
                                target=self._playable_cb,
                                args=(play_url,),
                                name="vrka-cocoa-playable-capture",
                                daemon=True,
                            ).start()
                    except Exception:
                        pass

            handler = CocoaMediaScriptMessageHandler.alloc().initWithCallback_andPlayable_(
                observation_callback, playable_callback
            )

            orig_init = cocoa.BrowserView.__init__

            def _patched_browser_view_init(bview_self, win):
                orig_init(bview_self, win)
                try:
                    config = bview_self.webview.configuration()
                    ucc = config.userContentController()
                    ucc.addScriptMessageHandler_name_(handler, "vrkaMediaBridge")

                    user_script = WebKit.WKUserScript.alloc().initWithSource_injectionTime_forMainFrameOnly_(
                        CROSS_FRAME_MEDIA_OBSERVER_JS,
                        WebKit.WKUserScriptInjectionTimeAtDocumentStart,
                        False,  # forMainFrameOnly: False injects into ALL frames, including cross-origin iframes
                    )
                    ucc.addUserScript_(user_script)
                except Exception:
                    pass

            cocoa.BrowserView.__init__ = _patched_browser_view_init
            return True
        except Exception:
            return False

    def get_all_cookies(self, window: Any) -> list[dict[str, Any]] | None:
        """Extract all cookies across all domains directly from the WKWebsiteDataStore HTTP cookie store."""
        try:
            import webview.platforms.cocoa as cocoa

            instance = cocoa.BrowserView.instances.get(window.uid)
            if not instance or not hasattr(instance, "datastore"):
                return None

            cookies_result: list[dict[str, Any]] = []
            sem = Semaphore(0)

            def _cookie_handler(ns_cookies):
                try:
                    for c in ns_cookies:
                        cookies_result.append({
                            "name": str(c.name() or ""),
                            "value": str(c.value() or ""),
                            "domain": str(c.domain() or ""),
                            "path": str(c.path() or ""),
                            "secure": bool(c.isSecure()),
                            "httponly": bool(c.isHTTPOnly()),
                        })
                finally:
                    sem.release()

            cocoa.AppHelper.callAfter(
                instance.datastore.httpCookieStore().getAllCookies_, _cookie_handler
            )
            # Synchronous wait bounded by 3.0s
            if sem.acquire(timeout=3.0):
                return cookies_result
            return None
        except Exception:
            return None

    def navigate_to_target(self, window: Any, target_url: str) -> None:
        """Navigate to target URL directly."""
        try:
            window.load_url(target_url)
        except Exception:
            pass

    def start_media_capture(self, window: Any, result_path: Path, holder: dict[str, Any]) -> bool:
        """MediaBodyCapture is not currently supported on macOS Cocoa WKWebView."""
        holder["error"] = "Media capture not supported on Cocoa WKWebView"
        return False

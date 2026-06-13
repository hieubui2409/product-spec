#!/usr/bin/env python3
"""Hover-tooltip support for product-spec HTML views.

Builds an inert JSON data island (id=ps-tip-data) mapping every artifact ID to
its {title, metadata} and a client-side scanner that tags Mermaid SVG labels and
bare IDs in HTML-native text so hovering any artifact ID surfaces its context.

Tooltip content is built with textContent (never innerHTML) so a PO title can
never inject markup.

Public API:
  tooltip_index(graph) → Dict[str, Dict[str, str]]
  tooltip_island(graph) → str (inert <script type=application/json> island)
  _TOOLTIP_JS             — client scanner <script> block

Not a CLI entry point; imported by render_html.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from render_html_escape import _tip_scalar


def tooltip_index(graph: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """Map every node id → {t: title, d: one-line metadata} for the hover tooltip.
    Pure node data (title + closed-enum metadata + owner/date) — NO body text, so
    nothing here needs HTML sanitization beyond the JSON island's `<`-escape."""
    out: Dict[str, Dict[str, str]] = {}
    for n in graph.get("nodes", []):
        nid = n.get("id")
        if not nid:
            continue
        meta = [p for p in (
            _tip_scalar(n.get("type")), _tip_scalar(n.get("status")),
            _tip_scalar(n.get("horizon")), _tip_scalar(n.get("moscow")),
            _tip_scalar(n.get("scope")),
        ) if p]
        td = _tip_scalar(n.get("target_date"))
        if td:
            meta.append("⏱ " + td)
        owner = _tip_scalar(n.get("owner"))
        if owner:
            meta.append("@ " + owner)
        out[str(nid)] = {"t": _tip_scalar(n.get("title")), "d": " · ".join(meta)}
    return out


def tooltip_island(graph: Dict[str, Any]) -> str:
    """The tooltip data as an inert JSON island (id=ps-tip-data), `<`-escaped via
    the same script-data-hazard neutralizer as embed_spec_data."""
    blob = json.dumps(tooltip_index(graph), ensure_ascii=False, sort_keys=True).replace("<", "\\u003c")
    return f'<script type="application/json" id="ps-tip-data">{blob}</script>'


# Client tooltip: read the inert id→{title,meta} island, then (a) tag SVG text
# labels (Mermaid gantt/flowchart — can't wrap a span inside <text>) and (b) wrap
# bare IDs in non-SVG text (HTML-native matrices, the ascii <pre> text-summary) so
# hovering any artifact ID surfaces its title + metadata. Mermaid renders async, so
# the scan re-runs a couple of times after load. Tooltip content is built with
# textContent (never innerHTML) so a PO title can never inject markup.
_TOOLTIP_JS = """
<script>
(function(){
  var island=document.getElementById("ps-tip-data"); if(!island) return;
  var TIP; try{ TIP=JSON.parse(island.textContent); }catch(e){ return; }
  var ids=Object.keys(TIP).filter(Boolean); if(!ids.length) return;
  ids.sort(function(a,b){return b.length-a.length;});          // longest-first: PRD-X-E1 before PRD-X
  function esc(s){return s.replace(/[.*+?^${}()|[\\]\\\\]/g,"\\\\$&");}
  var alt="(?<![A-Za-z0-9-])("+ids.map(esc).join("|")+")(?![A-Za-z0-9-])";
  // SVG label variant WITHOUT the trailing boundary: a Mermaid flowchart node
  // label concatenates "ID" + title into one textContent ("BRD-G1Onboard…"), so
  // the trailing boundary would reject every multi-line node. longest-first
  // ordering still makes PRD-X-E1 win over PRD-X at the same position.
  var altSvg="(?<![A-Za-z0-9-])("+ids.map(esc).join("|")+")";
  var reTest=new RegExp(alt);
  var box=document.createElement("div"); box.id="ps-tip"; box.setAttribute("role","tooltip");
  document.body.appendChild(box);
  function show(id,x,y){
    var d=TIP[id]; if(!d){box.style.display="none";return;}
    box.textContent="";
    var h=document.createElement("div"); h.className="ps-tip-h";
    var s=document.createElement("strong"); s.textContent=id; h.appendChild(s);
    if(d.t){var t=document.createElement("span"); t.className="ps-tip-t"; t.textContent=" "+d.t; h.appendChild(t);}
    box.appendChild(h);
    if(d.d){var m=document.createElement("div"); m.className="ps-tip-m"; m.textContent=d.d; box.appendChild(m);}
    box.style.display="block";
    var px=Math.min(x+14, window.innerWidth-box.offsetWidth-8);
    var py=Math.min(y+16, window.innerHeight-box.offsetHeight-8);
    box.style.left=Math.max(8,px)+"px"; box.style.top=Math.max(8,py)+"px";
  }
  function hide(){box.style.display="none";}
  function tagSvg(){
    // SVG text labels (gantt/flowchart): tag the whole <text> AFTER Mermaid has
    // rendered (skip already-tagged so re-scans are idempotent and late renders
    // still get picked up). A span can't live inside SVG <text>, so wrapText must
    // NOT touch this subtree (see acceptNode) — it is handled here exclusively.
    document.querySelectorAll("svg text, svg .nodeLabel").forEach(function(t){
      if(t.getAttribute("data-psid")) return;
      var m=(t.textContent||"").match(new RegExp(altSvg));
      if(m){ t.setAttribute("data-psid",m[1]); t.classList.add("ps-tipword"); }
    });
  }
  function wrapText(){
    var walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT,{acceptNode:function(node){
      if(!node.nodeValue||!reTest.test(node.nodeValue)) return NodeFilter.FILTER_REJECT;
      var p=node.parentNode;
      while(p&&p!==document.body){
        var tag=(p.tagName||"").toLowerCase();
        // Reject the ENTIRE Mermaid container: wrapping a span into its raw source
        // text (a race with Mermaid's async render) corrupts the diagram — the
        // span markup renders as literal text or breaks parsing. Mermaid labels go
        // through tagSvg instead.
        if(tag==="script"||tag==="style"||tag==="svg"||p.id==="ps-tip"||(p.classList&&(p.classList.contains("ps-tipword")||p.classList.contains("mermaid")))) return NodeFilter.FILTER_REJECT;
        p=p.parentNode;
      }
      return NodeFilter.FILTER_ACCEPT;
    }});
    var nodes=[],n; while((n=walker.nextNode())) nodes.push(n);
    nodes.forEach(function(node){
      var txt=node.nodeValue, frag=document.createDocumentFragment(), last=0, mm, r=new RegExp(alt,"g");
      while((mm=r.exec(txt))){
        if(mm.index>last) frag.appendChild(document.createTextNode(txt.slice(last,mm.index)));
        var sp=document.createElement("span"); sp.className="ps-tipword"; sp.setAttribute("data-psid",mm[1]); sp.textContent=mm[0];
        frag.appendChild(sp); last=mm.index+mm[0].length;
      }
      if(last<txt.length) frag.appendChild(document.createTextNode(txt.slice(last)));
      node.parentNode.replaceChild(frag,node);
    });
  }
  function scan(){ try{tagSvg();wrapText();}catch(e){} }
  // Exposed so the shell can re-tag SVG labels after it re-renders Mermaid on a
  // theme toggle (the old SVG + its data-psid tags are replaced wholesale).
  window.psRescanTooltips=scan;
  function idOf(t){ if(!t) return null; if(t.getAttribute){var d=t.getAttribute("data-psid"); if(d) return d;} if(t.closest){var c=t.closest("[data-psid]"); if(c) return c.getAttribute("data-psid");} return null; }
  document.addEventListener("mouseover",function(e){ var id=idOf(e.target); if(id) show(id,e.clientX,e.clientY); });
  document.addEventListener("mouseout",function(e){ if(idOf(e.target)) hide(); });
  scan(); setTimeout(scan,400); setTimeout(scan,1200);
})();
</script>
"""

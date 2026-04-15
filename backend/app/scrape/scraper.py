"""
DOM Scraper Module
Uses Playwright to extract important text nodes with visual hierarchy data.
"""
import os
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def scrape_landing_page(url: str) -> dict:
    """
    Scrape the landing page using Playwright to get visual hierarchy.
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
                                      
            await page.set_viewport_size({"width": 1280, "height": 800})
            
                                                       
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
                                            
            html = await page.content()
            
                                    
            nodes = await page.evaluate(_JS_EXTRACT_NODES)
            
            await browser.close()
            
                                                       
            soup = BeautifulSoup(html, "lxml")
            meta = _extract_meta(soup)
            
                                    
            scored_nodes = _score_and_filter_nodes(nodes)
            
            return {
                "success": True,
                "original_html": html,
                "nodes": scored_nodes,
                "meta": meta,
                "error": None
            }
            
    except Exception as e:
        return {
            "success": False,
            "original_html": "",
            "nodes": [],
            "meta": {"title": "", "description": ""},
            "error": f"Scraping failed: {str(e)}"
        }

def _extract_meta(soup: BeautifulSoup) -> dict:
    title = ""
    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        title = title_tag.string.strip()
    
    description = ""
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        description = meta_desc["content"].strip()
    
    return {"title": title, "description": description}

def _score_and_filter_nodes(nodes: list) -> list:
    """Score nodes by prominence and return top candidates."""
    for node in nodes:
        score = 0
                          
        score += node["fontSize"] * 2
        
                                                
        if node["top"] < 800:
            score += (800 - node["top"]) / 10
            
                    
        tag_weights = {"h1": 50, "h2": 30, "h3": 20, "button": 40, "a": 20}
        score += tag_weights.get(node["tagName"], 0)
        
        node["score"] = score
        
                              
    nodes.sort(key=lambda n: n["score"], reverse=True)
    
                                
    return nodes[:40]

_JS_EXTRACT_NODES = r"""
() => {
    const results = [];
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
    let node;
    
    function getSelector(el) {
        if (el.id) return '#' + el.id;
        let path = [];
        while (el.nodeType === Node.ELEMENT_NODE) {
            let selector = el.nodeName.toLowerCase();
            if (el.className) {
                selector += '.' + el.className.trim().replace(/\s+/g, '.');
            }
            path.unshift(selector);
            el = el.parentNode;
        }
        return path.join(' > ');
    }

    while(node = walker.nextNode()) {
        const text = node.textContent.trim();
        if (text.length < 5) continue; // skip short noise
        
        const parent = node.parentElement;
        if (!parent) continue;
        
        const style = window.getComputedStyle(parent);
        if (style.display === 'none' || style.visibility === 'hidden') continue;
        if (['SCRIPT', 'STYLE', 'NOSCRIPT', 'IFRAME'].includes(parent.tagName)) continue;
        
        const rect = parent.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) continue;
        
        results.push({
            text: text,
            tagName: parent.tagName.toLowerCase(),
            fontSize: parseFloat(style.fontSize),
            top: rect.top,
            left: rect.left,
            selector: getSelector(parent)
        });
    }
    return results;
}
"""

"""
Merger Module
Applies text replacements and inserts personalized components back into the original HTML.
"""
from bs4 import BeautifulSoup
import re
import copy


def merge_copy_into_html(
    original_html: str,
    replacements: list[dict],
    color_overrides: dict = None,
    custom_section: dict = None,
    base_url: str = None
) -> dict:
    """
    Apply text replacements and insert personalized components into the original HTML.
    
    Args:
        original_html: The original landing page HTML
        replacements: List of {selector, original, replacement, reason} dicts
        color_overrides: Dict with {primary_bg, primary_text, accent_bg, accent_text} or None
        custom_section: Dict with {type, title, content, cta} or None
    
    Returns:
        {
            "success": bool,
            "modified_html": str,
            "changes_applied": int,
            "changes_failed": int,
            "diff": list[dict],
            "error": str or None
        }
    """
    if not original_html:
        return {
            "success": False,
            "modified_html": "",
            "changes_applied": 0,
            "changes_failed": len(replacements),
            "diff": [],
            "error": "Original HTML is empty."
        }
        
    try:
        soup = BeautifulSoup(original_html, "lxml")
        print(f"[Merger] Starting merge. Replacements: {len(replacements)}")
        if color_overrides:
            print(f"[Merger] Color overrides present: {list(color_overrides.keys())}")
        if custom_section:
            print(f"[Merger] Custom section present: {custom_section.get('title')}")
            
        changes_applied = 0
        changes_failed = 0
        diff = []
        
                                    
        for repl in replacements:
            selector = repl.get("selector", "")
            original_text = repl.get("original", "")
            new_text = repl.get("replacement", "")
            reason = repl.get("reason", "")
            
            if not original_text or not new_text:
                changes_failed += 1
                continue
            
                                                  
            replaced = _apply_replacement(soup, selector, original_text, new_text)
            
            if replaced:
                changes_applied += 1
                diff.append({
                    "selector": selector,
                    "original": original_text,
                    "replacement": new_text,
                    "reason": reason,
                    "status": "applied"
                })
            else:
                changes_failed += 1
                diff.append({
                    "selector": selector,
                    "original": original_text,
                    "replacement": new_text,
                    "reason": reason,
                    "status": "failed"
                })
        
                                             
        if custom_section:
            _insert_custom_section(soup, custom_section)
            changes_applied += 1
            diff.append({
                "selector": "body > .troopod-custom-section",
                "original": "",
                "replacement": custom_section.get("title", ""),
                "reason": "Inserted custom personalized section",
                "status": "applied"
            })
            
                                              
        if color_overrides:
            _inject_styles(soup, color_overrides)
            changes_applied += 1
            diff.append({
                "selector": "head > style",
                "original": "",
                "replacement": "Custom CSS overrides",
                "reason": "Applied personalized color palette",
                "status": "applied"
            })
            
                                       
        if base_url:
            head = soup.find('head')
            if not head:
                head = soup.new_tag("head")
                soup.insert(0, head)
            
                                              
            for base in head.find_all('base'):
                base.decompose()
                
            base_tag = soup.new_tag("base", href=base_url)
            head.insert(0, base_tag)
            print(f"[Merger] Injected <base href=\"{base_url}\">")
            
                                                    
        modified_html = str(soup)
        try:
            BeautifulSoup(modified_html, "lxml")
        except Exception:
            return {
                "success": False,
                "modified_html": original_html,
                "changes_applied": 0,
                "changes_failed": len(replacements),
                "diff": [],
                "error": "Modified HTML failed validation. Returning original."
            }
        
        return {
            "success": True,
            "modified_html": modified_html,
            "changes_applied": changes_applied,
            "changes_failed": changes_failed,
            "diff": diff,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "modified_html": original_html,
            "changes_applied": 0,
            "changes_failed": len(replacements),
            "diff": [],
            "error": f"Merge failed: {str(e)}"
        }


def _inject_styles(soup: BeautifulSoup, color_overrides: dict):
    """Inject a style tag with color overrides."""
    head = soup.find('head')
    if not head:
        head = soup.new_tag("head")
        soup.insert(0, head)
        
    style_tag = soup.new_tag("style")
    
    primary_bg = color_overrides.get("primary_bg", "")
    primary_text = color_overrides.get("primary_text", "")
    accent_bg = color_overrides.get("accent_bg", "")
    accent_text = color_overrides.get("accent_text", "")
    
    css = ""
    if primary_bg:
        css += f"body, section, .container, .wrapper {{ background-color: {primary_bg} !important; }}\n"
    if primary_text:
        css += f"body, p, span, li {{ color: {primary_text} !important; }}\n"
        css += f"h1, h2, h3, h4, h5, h6 {{ color: {primary_text} !important; }}\n"
    if accent_bg:
        css += f"button, .cta, a.btn, .primary-btn {{ background-color: {accent_bg} !important; }}\n"
    if accent_text:
        css += f"button, .cta, a.btn, .primary-btn {{ color: {accent_text} !important; }}\n"
        
    css += f"""
    .troopod-custom-section {{
        background-color: {accent_bg if accent_bg else '#f8f9fa'};
        color: {accent_text if accent_text else '#212529'};
        padding: 40px 20px;
        margin: 20px 0;
        border-radius: 8px;
        text-align: center;
        font-family: system-ui, -apple-system, sans-serif;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    .troopod-custom-section h2 {{
        font-size: 2rem;
        margin-bottom: 15px;
    }}
    .troopod-custom-section p, .troopod-custom-section li {{
        font-size: 1.1rem;
        margin-bottom: 10px;
    }}
    """
        
    style_tag.string = css
    head.append(style_tag)


def _insert_custom_section(soup: BeautifulSoup, section: dict):
    """Insert a new custom section into the page."""
    body = soup.find('body')
    if not body:
        return
        
                              
    section_div = soup.new_tag("div", **{"class": f"troopod-custom-section troopod-{section.get('type', 'default')}"})
    
                    
    title = soup.new_tag("h2")
    title.string = section.get("title", "")
    
    content = section.get("content", "")
    content_elem = None
    if isinstance(content, list):
        content_elem = soup.new_tag("ul")
        for item in content:
            li = soup.new_tag("li")
            li.string = item
            content_elem.append(li)
    else:
        content_elem = soup.new_tag("p")
        content_elem.string = content
        
    section_div.append(title)
    section_div.append(content_elem)
    
    if section.get("cta"):
        cta = soup.new_tag("button", **{"class": "cta"})
        cta.string = section.get("cta")
        section_div.append(cta)
        
                               
    body.insert(0, section_div)


                                    
_SKIP_TAGS = {'title', 'meta', 'link', 'script', 'style', 'noscript', 'head',
              'nav', 'header', 'footer', 'iframe', 'svg', 'path', 'form', 'input',
              'select', 'option', 'textarea', 'label', 'code', 'pre', 'body', 'html'}


def _is_safe_to_replace(elem) -> bool:
    """Check if an element is safe to replace (inside body, not in nav/header/footer)."""
    if elem.name in _SKIP_TAGS:
        return False
    for parent in elem.parents:
        if parent.name in _SKIP_TAGS:
            return False
    return True


def _apply_replacement(
    soup: BeautifulSoup,
    selector: str,
    original_text: str,
    new_text: str
) -> bool:
    """
    Find and replace text in the DOM using multiple strategies.
    Only targets safe elements within <body>, skipping nav/header/footer.
    Returns True if replacement was successful.
    """
    body = soup.find('body') or soup
    
                                            
    if selector.startswith("#") and "[" not in selector:
        elem_id = selector[1:]
        elem = body.find(id=elem_id)
        if elem and _is_safe_to_replace(elem) and _text_matches(elem.get_text(strip=True), original_text):
            _replace_text_content(elem, original_text, new_text)
            return True
    
                                                                          
    try:
        index_match = re.search(r'\[(\d+)\]$', selector)
        target_index = int(index_match.group(1)) if index_match else 0
        
        clean_selector = re.sub(r'\[\d+\]$', '', selector)
        
        elements = body.select(clean_selector)
        
        elements = [e for e in elements if _is_safe_to_replace(e)]
        
        if elements and target_index < len(elements):
            elem = elements[target_index]
            if _text_matches(elem.get_text(strip=True), original_text):
                _replace_text_content(elem, original_text, new_text)
                return True
    except Exception:
        pass
        
                                                                         
    for elem in body.find_all(True):
        if not _is_safe_to_replace(elem):
            continue
        if _text_matches(elem.get_text(strip=True), original_text):
            children_with_text = [
                c for c in elem.children
                if hasattr(c, 'get_text') and _text_matches(c.get_text(strip=True), original_text)
            ]
            if not children_with_text:
                _replace_text_content(elem, original_text, new_text)
                return True
    
    return False


def _text_matches(actual: str, expected: str) -> bool:
    """Fuzzy text match — normalize whitespace and compare."""
    a = re.sub(r'\s+', ' ', actual.strip().lower())
    b = re.sub(r'\s+', ' ', expected.strip().lower())
    return a == b or a.startswith(b) or b.startswith(a)


def _replace_text_content(elem, original_text: str, new_text: str):
    """
    Replace text content in an element while preserving child tags.
    """
    children = list(elem.children)
    
    if len(children) == 1 and isinstance(children[0], str):
        children[0].replace_with(new_text)
    elif len(children) == 0:
        elem.string = new_text
    else:
        from bs4 import NavigableString
        text_nodes = [c for c in children if isinstance(c, NavigableString) and c.strip()]
        if text_nodes:
            longest = max(text_nodes, key=lambda t: len(t.strip()))
            longest.replace_with(new_text)
        else:
            elem.clear()
            elem.string = new_text

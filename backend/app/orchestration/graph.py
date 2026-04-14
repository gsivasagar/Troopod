"""
LangGraph Orchestrator
Follows industry standards with class-based nodes and clean state management.
"""
from typing import List, Optional
from langgraph.graph import StateGraph, END
from app.scrape.scraper import scrape_landing_page
from app.agents.vision_agent import VisionAgent
from app.agents.copywriter_agent import CopywriterAgent
from app.agents.merger_agent import merge_copy_into_html
from app.agents.designer_agent import DesignerAgent
from app.core.state import GraphState
from app.core.config import config
import time
import re
import json
from playwright.async_api import async_playwright

class PersonalizationPipeline:
    """
    Orchestrates the Ad-to-LP Personalization pipeline using LangGraph.
    Encapsulates nodes and graph construction for scalability.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.max_iterations = config.MAX_ITERATIONS
        
        # Instantiate agents
        self.vision_agent = VisionAgent(api_key=self.api_key)
        self.copywriter_agent = CopywriterAgent(api_key=self.api_key)
        self.designer_agent = DesignerAgent(api_key=self.api_key)
        
        self.workflow = StateGraph(GraphState)
        self._build_graph()
        self.app = self.workflow.compile()
        
    def _build_graph(self):
        """Wire the graph nodes and edges."""
        self.workflow.add_node("scrape_and_analyze", self.scrape_and_analyze)
        self.workflow.add_node("generate_copy", self.generate_copy)
        self.workflow.add_node("merge_and_render", self.merge_and_render)
        self.workflow.add_node("critique", self.critique)
        self.workflow.add_node("refine", self.refine)
        
        self.workflow.set_entry_point("scrape_and_analyze")
        self.workflow.add_edge("scrape_and_analyze", "generate_copy")
        self.workflow.add_edge("generate_copy", "merge_and_render")
        self.workflow.add_edge("merge_and_render", "critique")
        
        self.workflow.add_conditional_edges(
            "critique",
            self.should_continue,
            {
                "refine": "refine",
                "end": END
            }
        )
        
        self.workflow.add_edge("refine", "merge_and_render")

    async def scrape_and_analyze(self, state: GraphState) -> dict:
        """Node: Scrape landing page and analyze ad creative."""
        scrape_result = await scrape_landing_page(state["url"])
        if not scrape_result["success"]:
            return {"success": False, "error": f"Scraping failed: {scrape_result['error']}"}
            
        vision_result = self.vision_agent.analyze_ad_creative(state["image_bytes"])
        if not vision_result["success"]:
            return {"success": False, "error": f"Vision failed: {vision_result['error']}"}
            
        return {
            "original_html": scrape_result["original_html"],
            "dom_nodes": scrape_result["nodes"],
            "ad_context": vision_result["context"],
            "meta": scrape_result["meta"],
            "success": True,
            "iteration": 0
        }

    async def generate_copy(self, state: GraphState) -> dict:
        """Node: Generate copy and banner content."""
        if not state.get("success", True): return {}
        
        print("[Graph] Entering generate_copy node")
        time.sleep(5) # Rate limit buffer
        copy_result = self.copywriter_agent.generate_personalized_copy(state["ad_context"], state["dom_nodes"])
        if not copy_result["success"]:
            return {"success": False, "error": f"Copy failed: {copy_result['error']}"}
            
        return {
            "color_overrides": copy_result.get("color_overrides"),
            "replacements": copy_result.get("replacements", []),
            "custom_section": copy_result.get("custom_section"),
            "summary": copy_result.get("summary", ""),
            "success": True
        }

    async def merge_and_render(self, state: GraphState) -> dict:
        """Node: Merge changes and take a screenshot for verification."""
        if not state.get("success", True): return {}
        
        print("[Graph] Entering merge_and_render node")
        merge_result = merge_copy_into_html(
            state["original_html"], 
            state["replacements"], 
            state["color_overrides"],
            state.get("custom_section")
        )
        if not merge_result["success"]:
            print(f"[Graph] Merge failed: {merge_result['error']}")
            return {"success": False, "error": f"Merge failed: {merge_result['error']}"}
            
        modified_html = merge_result["modified_html"]
        
        screenshot = None
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.set_viewport_size({"width": 1280, "height": 800})
                await page.set_content(modified_html)
                await page.wait_for_timeout(1000)
                screenshot = await page.screenshot(type="jpeg", quality=80)
                await browser.close()
        except Exception as e:
            print(f"Screenshot failed: {e}")
            
        return {
            "modified_html": modified_html,
            "screenshot": screenshot,
            "success": True
        }

    async def critique(self, state: GraphState) -> dict:
        """Node: Critique the design using Vision."""
        if not state.get("success", True) or not state.get("screenshot"):
            return {"critique": "SKIP"}
            
        critique = self.designer_agent.critique_design(
            screenshot_bytes=state["screenshot"],
            ad_image_bytes=state["image_bytes"]
        )
        
        return {
            "critique": critique,
            "iteration": state["iteration"] + 1
        }

    def should_continue(self, state: GraphState) -> str:
        """Conditional edge: Decide to continue or end."""
        critique = state.get("critique", "")
        iteration = state.get("iteration", 0)
        
        if critique == "GOOD" or iteration >= self.max_iterations:
            return "end"
        if critique.startswith("{") or '"banner_bg"' in critique:
            return "refine"
        return "end"

    async def refine(self, state: GraphState) -> dict:
        """Node: Parse critique and update color overrides."""
        critique = state["critique"]
        try:
            text = re.sub(r'^```(?:json)?\s*', '', critique)
            text = re.sub(r'\s*```$', '', text).strip()
            
            parsed = json.loads(text)
            
            current_overrides = state.get("color_overrides", {}) or {}
            new_overrides = {**current_overrides, **parsed}
            
            if "reason" in new_overrides:
                del new_overrides["reason"]
                
            return {
                "color_overrides": new_overrides,
                "success": True
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to parse critique: {str(e)}"}

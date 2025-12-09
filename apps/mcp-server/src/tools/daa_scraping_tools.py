"""
MCP tools for scraping DAA portal (grades, schedule).
"""
from fastmcp import FastMCP

from ..scraper.daa_scraper import DaaScraper
from ..scraper.models.grades import Grades
from ..scraper.models.schedule import Schedule


def register_daa_tools(mcp: FastMCP):
    """Register DAA scraping tools to FastMCP instance."""

    @mcp.tool()
    async def get_grades(cookie: str) -> Grades:
        """
        Retrieve student grades from the DAA portal using cookie authentication.

        Returns structured grade data including:
        - Student information (name, MSSV, class, faculty, etc.)
        - Semester-by-semester breakdown with courses and GPA
        - Overall GPA summary (both 10-scale and 4-scale)

        This tool automatically calculates GPA for each semester and cumulative GPA.

        Args:
            cookie: DAA authentication cookie (format: "name1=value1; name2=value2").
                    This cookie is automatically provided by the agent system.

        Returns:
            Grades: Pydantic model with complete grade information and GPA calculations.
                FastMCP will automatically generate JSON schema from this model.
        """
        if not cookie:
            raise ValueError("Cookie is required. Please sync DAA cookies via the extension first.")

        async with DaaScraper(cookie=cookie, headless=True) as scraper:
            grades = await scraper.get_grades()
            return grades

    @mcp.tool()
    async def get_schedule(cookie: str) -> Schedule:
        """
        Retrieve student schedule from the DAA portal using cookie authentication.

        Returns structured schedule data including:
        - Current semester information
        - List of all classes with details (time, room, subject, class size, etc.)
        - Day of week, period, date range for each class

        Args:
            cookie: DAA authentication cookie (format: "name1=value1; name2=value2").
                    This cookie is automatically provided by the agent system.

        Returns:
            Schedule: Pydantic model with complete schedule information.
                FastMCP will automatically generate JSON schema from this model.
        """
        if not cookie:
            raise ValueError("Cookie is required. Please sync DAA cookies via the extension first.")

        async with DaaScraper(cookie=cookie, headless=True) as scraper:
            schedule = await scraper.get_schedule()
            return schedule

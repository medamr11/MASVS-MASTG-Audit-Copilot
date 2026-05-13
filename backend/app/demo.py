"""
Demo mode — runs the full pipeline on bundled sample data.
Usage: python -m app.demo
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.schemas import AppMetadata
from app.pipeline import AnalysisPipeline
from app.core.logging import setup_logging, get_logger


async def run_demo():
    """Run the demo pipeline on sample data."""
    setup_logging()
    logger = get_logger("demo")

    logger.info("demo_starting", msg="Running MASVS Audit Copilot demo...")

    sample_path = Path(__file__).parent.parent / "data" / "samples" / "sample_mobsf_report.json"
    if not sample_path.exists():
        logger.error("sample_not_found", path=str(sample_path))
        print(f"❌ Sample file not found: {sample_path}")
        return

    app_metadata = AppMetadata(
        name="InsecureBankv2",
        package_name="com.android.insecurebankv2",
        version="1.0",
        platform="android",
        auditor="MASVS Audit Copilot (Demo)",
    )

    # Run without LLM for demo
    pipeline = AnalysisPipeline(use_llm=False)

    print("\n🛡️  MASVS Audit Copilot — Demo Mode")
    print("=" * 50)

    async for event in pipeline.run([sample_path], app_metadata, "demo"):
        icon = "✅" if event.event_type == "complete" else "⚡" if event.event_type == "stage_update" else "❌"
        progress_bar = "█" * int(event.progress * 20) + "░" * (20 - int(event.progress * 20))
        print(f"  {icon} [{progress_bar}] {event.progress:.0%} — {event.message}")

        if event.finding_count:
            print(f"     📋 Findings: {event.finding_count}")

    # Check outputs
    reports_dir = Path("./data/reports/demo")
    if reports_dir.exists():
        print(f"\n📁 Reports generated in: {reports_dir}")
        for f in reports_dir.iterdir():
            size = f.stat().st_size
            print(f"   📄 {f.name} ({size:,} bytes)")

    print("\n✅ Demo complete!")


def main():
    asyncio.run(run_demo())


if __name__ == "__main__":
    main()

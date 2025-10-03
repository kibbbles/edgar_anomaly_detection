"""
SEC EDGAR 10-K Scraper

Downloads 10-K filings from SEC EDGAR for specified companies and fiscal years.
Uses sec-edgar-downloader library which handles rate limiting and filing lookup.

Usage:
    scraper = Edgar10KScraper()
    scraper.download_all_companies()
"""

import os
import json
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
from sec_edgar_downloader import Downloader

# Load environment variables
load_dotenv()


class Edgar10KScraper:
    """Scraper for downloading 10-K filings from SEC EDGAR using sec-edgar-downloader library."""

    def __init__(self, data_dir: str = "data/raw"):
        """
        Initialize the scraper.

        Args:
            data_dir: Directory to store downloaded filings
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Get user agent from environment variable
        self.user_agent = os.getenv("SEC_USER_AGENT")
        if not self.user_agent:
            raise ValueError(
                "SEC_USER_AGENT not set. Create a .env file with: "
                "SEC_USER_AGENT='YourName your.email@company.com'"
            )

        # Initialize downloader with user agent and output directory
        self.downloader = Downloader(
            company_name="EDGAR_Analytics",
            email_address=self.user_agent.split()[-1],  # Extract email from user agent
            download_folder=str(self.data_dir)
        )

    def download_company_filings(self, ticker: str, cik: str, years: List[int]) -> int:
        """
        Download 10-K filings for a company across multiple years.

        Args:
            ticker: Company ticker symbol (e.g., "AAPL")
            cik: 10-digit CIK
            years: List of fiscal years (e.g., [2020, 2021, 2022, 2023, 2024])

        Returns:
            Number of filings downloaded
        """
        print(f"Fetching 10-K filings for {ticker} (CIK: {cik})...")

        # Calculate date range for filings
        # 10-Ks are typically filed within 60-90 days after fiscal year end
        # So for FY 2020-2024, we look for filings from 2020 to early 2025
        after_date = f"{min(years)}-01-01"
        before_date = f"{max(years)+1}-12-31"

        try:
            # Download 10-K filings for this company
            # The library will download all 10-Ks in the date range
            num_downloaded = self.downloader.get(
                "10-K",
                cik,
                after=after_date,
                before=before_date,
                download_details=True
            )

            print(f"  Downloaded {num_downloaded} filings for {ticker}")
            return num_downloaded

        except Exception as e:
            print(f"  Error downloading {ticker}: {e}")
            return 0

    def download_all_companies(
        self,
        companies_json_path: str = "config/companies.json",
        years: List[int] = [2020, 2021, 2022, 2023, 2024]
    ) -> Dict[str, int]:
        """
        Download 10-K filings for all companies in config file.

        Args:
            companies_json_path: Path to companies.json config file
            years: List of fiscal years to download

        Returns:
            Dictionary mapping ticker to number of filings downloaded
        """
        with open(companies_json_path, "r") as f:
            config = json.load(f)

        companies = config["companies"]
        download_counts = {}

        print(f"Starting download for {len(companies)} companies")
        print(f"Target fiscal years: {years}")
        print("-" * 60)

        for company in companies:
            cik = company["cik"]
            ticker = company["ticker"]
            name = company["name"]

            print(f"\n[{ticker}] {name}")
            count = self.download_company_filings(ticker, cik, years)
            download_counts[ticker] = count

        print("\n" + "=" * 60)
        print(f"Download complete. Total filings: {sum(download_counts.values())}")
        print("\nFilings by company:")
        for ticker, count in download_counts.items():
            print(f"  {ticker}: {count} filings")

        # Save summary
        summary = {
            "companies": len(companies),
            "target_years": years,
            "total_filings": sum(download_counts.values()),
            "by_company": download_counts
        }

        summary_path = self.data_dir / "download_summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"\nDownload summary saved to: {summary_path}")

        return download_counts


def main():
    """Example usage: Download all filings for configured companies."""
    scraper = Edgar10KScraper()

    # Download all companies for 5 years (2020-2024)
    scraper.download_all_companies(
        companies_json_path="config/companies.json",
        years=[2020, 2021, 2022, 2023, 2024]
    )


if __name__ == "__main__":
    main()

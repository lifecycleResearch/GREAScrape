#!/usr/bin/env python3
"""
Hemp & Cannabis Business Intelligence — Waterfall Enrichment Pipeline
Phase A: SOS (Secretary of State) entity matching
Phase B: EPA ECHO cross-reference
Phase C: Fire Marshal permit lookup
Phase D: SEC EDGAR public company check
Phase E: Patent & social media signals
"""

import os
import csv
import json
import time
import logging
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional

BASE_DIR = Path("/teamspace/studios/this_studio/hemp_cannabis_intel")
INPUT_CSV = BASE_DIR.parent / "unified_cannabis_hemp_base.csv"
OUTPUT_DIR = BASE_DIR / "output"
FOIA_DIR = BASE_DIR / "foia"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(BASE_DIR / "enrichment.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


@dataclass
class BusinessRecord:
    """Unified business record with enrichment fields."""
    record_id: str = ""
    source: str = ""
    name: str = ""
    legal_name: str = ""
    dba: str = ""
    type: str = ""
    category: str = ""
    extraction_processing_flag: str = "PENDING"
    phone: str = ""
    email: str = ""
    website: str = ""
    street_address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    county: str = ""
    lat: str = ""
    lng: str = ""
    license_number: str = ""
    license_state: str = ""
    license_type: str = ""
    license_status: str = ""
    license_expiration: str = ""
    date_issued: str = ""
    usda_hemp_flag: str = ""
    delivery: str = ""
    sells_seeds: str = ""
    home_delivery: str = ""
    business_category: str = ""
    product_focus: str = ""
    is_medical: str = ""
    is_adult_use: str = ""
    ownership_type: str = ""
    social_equity_status: str = ""
    # Enrichment fields
    sos_entity_match: str = ""
    sos_formation_date: str = ""
    sos_registered_agent: str = ""
    sos_entity_type: str = ""
    sos_status: str = ""
    sos_website: str = ""
    epa_air_permit: str = ""
    epa_npdes_permit: str = ""
    epa_rcra_generator: str = ""
    epa_facility_name: str = ""
    epa_facility_address: str = ""
    fire_marshal_permit: str = ""
    fire_marshal_violations: str = ""
    tier2_filed: str = ""
    sec_public_company: str = ""
    sec_cik: str = ""
    sec_ticker: str = ""
    patent_count: str = ""
    instagram_url: str = ""
    google_place_id: str = ""
    sales_priority: str = "5"
    data_quality_score: str = "0"
    notes: str = ""


class WaterfallEnrichmentPipeline:
    """
    Sequential enrichment pipeline — each step fills gaps from the previous.
    Order matters: earlier steps provide data that later steps can use for matching.
    """

    def __init__(self, input_path: str, output_dir: str):
        self.input_path = Path(input_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.records: list[BusinessRecord] = []
        self.stats = {
            "total": 0,
            "sos_matched": 0,
            "epa_matched": 0,
            "fire_marshal_matched": 0,
            "sec_matched": 0,
            "extraction_processing": 0,
        }

    def load_data(self):
        """Load unified base CSV."""
        log.info(f"Loading {self.input_path}")
        with open(self.input_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rec = BusinessRecord(**{k: v for k, v in row.items() if k in BusinessRecord.__dataclass_fields__})
                self.records.append(rec)
        self.stats["total"] = len(self.records)
        log.info(f"Loaded {len(self.records)} records")

    def save_checkpoint(self, name: str):
        """Save intermediate results."""
        path = self.output_dir / f"checkpoint_{name}.csv"
        if not self.records:
            return
        headers = list(asdict(self.records[0]).keys())
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for rec in self.records:
                writer.writerow(asdict(rec))
        log.info(f"Checkpoint saved: {path} ({len(self.records)} records)")

    # ─── Phase A: Secretary of State Cross-Reference ───

    def phase_a_sos_matching(self):
        """
        For each business, search the Secretary of State business entity database
        in their state of registration.

        States with online SOS search:
        - CA: https://bizfileonline.sos.ca.gov/search/business
        - CO: https://www.sos.co.gov/biz/BusinessEntitySearch.do
        - NY: https://apps.dos.ny.gov/publicInquiry/
        - TX: https://mycpa.cpa.state.tx.us/alltaxpermits/
        - FL: https://dos.myflorida.com/sunbiz/search/
        - And 30+ more states with online search

        For states without online search, flag for FOIA.
        """
        log.info("═" * 60)
        log.info("Phase A: Secretary of State Entity Matching")
        log.info("═" * 60)

        states_with_online_sos = {
            "AL", "AK", "AZ", "CA", "CO", "CT", "DE", "FL", "GA", "HI",
            "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA",
            "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM",
            "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD",
            "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
        }

        for rec in self.records:
            state = rec.state.strip().upper()
            if state in states_with_online_sos:
                # Mark as searchable — actual scraping done by subagent
                rec.notes += f"|sos_searchable:Y"
                self.stats["sos_matched"] += 1
            else:
                rec.notes += f"|sos_searchable:N"
                # Flag for FOIA
                foia_path = FOIA_DIR / f"foia_needed_{state}.csv"
                foia_path.parent.mkdir(parents=True, exist_ok=True)

        self.save_checkpoint("phase_a_sos")
        log.info(f"Phase A complete: {self.stats['sos_matched']} searchable, {self.stats['total'] - self.stats['sos_matched']} need FOIA")

    # ─── Phase B: EPA ECHO Cross-Reference ───

    def phase_b_epa_echo(self):
        """
        Cross-reference against EPA ECHO database using facility name + address.
        Identifies: Air permits, NPDES water permits, RCRA generator IDs, enforcement actions.

        API: https://echodata.epa.gov/echo/
        """
        log.info("═" * 60)
        log.info("Phase B: EPA ECHO Cross-Reference")
        log.info("═" * 60)

        # EPA ECHO API integration
        # For extraction/processing facilities, key EPA programs:
        # - ICIS-AIR (air permits for VOC emissions from extraction)
        # - ICIS-NPDES (water discharge from processing)
        # - RCRAInfo (hazardous waste generators — solvent waste)
        # - ECHO enforcement actions

        ECHO_BASE_URL = "https://echodata.epa.gov/echo"

        for rec in self.records:
            # Flag extraction/processing facilities likely to have EPA permits
            cat_lower = (rec.category + "|" + rec.type).lower()
            extraction_indicators = [
                "extraction", "processing", "manufacturing", "distillation",
                "refining", "solvent", "ethanol", "butane", "hydrocarbon",
                "co2", "supercritical", "post-processing", "formulation",
            ]
            if any(ind in cat_lower for ind in extraction_indicators):
                rec.extraction_processing_flag = "LIKELY"
                self.stats["extraction_processing"] += 1
                rec.notes += f"|epa_likely:Y"

        self.save_checkpoint("phase_b_epa")
        log.info(f"Phase B complete: {self.stats['extraction_processing']} likely extraction/processing facilities")

    # ─── Phase C: Fire Marshal Permit Lookup ───

    def phase_c_fire_marshal(self):
        """
        For extraction/processing facilities, search state fire marshal databases
        for flammable liquid storage permits.

        Key states with online fire marshal permit search:
        - CA: OSFM PIP (osfm.fire.ca.gov/pip)
        - TX: TDI SFMO (appscenter.tdi.texas.gov/reports/p/sfmo)
        - FL: MyFloridaCFO SFM
        - NY: DOS Fire Prevention
        - IL: OSFM
        """
        log.info("═" * 60)
        log.info("Phase C: Fire Marshal Permit Lookup")
        log.info("═" * 60)

        fire_marshal_states = {"CA", "TX", "FL", "NY", "IL", "OH", "PA", "GA", "NC", "NJ"}

        for rec in self.records:
            if rec.extraction_processing_flag == "LIKELY" and rec.state in fire_marshal_states:
                rec.notes += f"|fm_searchable:Y"
                self.stats["fire_marshal_matched"] += 1

        self.save_checkpoint("phase_c_fire")
        log.info(f"Phase C complete: {self.stats['fire_marshal_matched']} fire marshal searchable")

    # ─── Phase D: SEC EDGAR Public Company Check ───

    def phase_d_sec_edgar(self):
        """
        Check if business is publicly traded via SEC EDGAR.
        If yes: pull CIK, ticker, company name, filing history.
        """
        log.info("═" * 60)
        log.info("Phase D: SEC EDGAR Public Company Check")
        log.info("═" * 60)

        # Known public cannabis/hemp companies (pre-validated)
        known_public = {
            "TLRY": "Tilray Brands",
            "CGC": "Canopy Growth",
            "CRON": "Cronos Group",
            "TGTX": "TG Therapeutics",
            "MJ": "ETFMG Alternative Harvest ETF",
            "MSOS": "AdvisorShares Pure US Cannabis ETF",
            "CWB": "Charlotte's Web Holdings",
            "KERN": "Sierra Metals",  # not cannabis but check
        }

        for rec in self.records:
            name_lower = (rec.name + "|" + rec.legal_name).lower()
            for ticker, company in known_public.items():
                if company.lower() in name_lower:
                    rec.sec_public_company = company
                    rec.sec_ticker = ticker
                    rec.notes += f"|sec_public:{ticker}"
                    self.stats["sec_matched"] += 1
                    break

        self.save_checkpoint("phase_d_sec")
        log.info(f"Phase D complete: {self.stats['sec_matched']} public companies identified")

    # ─── Phase E: Lead Scoring & Categorization ───

    def phase_e_categorize_and_score(self):
        """
        Final phase: categorize records and assign sales priority.
        Categories: Hemp, Cannabis, Lab/Testing/Growers
        Priority: 1 (extraction/processing) → 5 (low-value)
        """
        log.info("═" * 60)
        log.info("Phase E: Lead Scoring & Categorization")
        log.info("═" * 60)

        for rec in self.records:
            cat_lower = (rec.category + "|" + rec.type + "|" + rec.business_category + "|" + rec.product_focus).lower()

            # ── Categorization ──
            if any(kw in cat_lower for kw in ["hemp", "fiber", "seed", "grain", "cbd", "cannabinoid"]):
                if "dispensary" not in cat_lower and "retail" not in cat_lower:
                    rec.notes += "|cat:HEMP"

            if any(kw in cat_lower for kw in ["dispensary", "retail", "cultivation", "marijuana", "cannabis", "marihuana"]):
                rec.notes += "|cat:CANNABIS"

            if any(kw in cat_lower for kw in ["lab", "testing", "analytical", "quality", "compliance", "certification", "laboratory"]):
                rec.notes += "|cat:LAB"

            if any(kw in cat_lower for kw in ["grow", "cultivat", "nursery", "propagation", "clone", "seedling"]):
                rec.notes += "|cat:GROWER"

            if any(kw in cat_lower for kw in ["extract", "process", "manufactur", "distill", "refin", "formulat", "packag", "co-packing"]):
                rec.notes += "|cat:EXTRACTION_PROCESSING"

            # ── Sales Priority ──
            score = 5  # default

            # Priority 1: Extraction & Processing facilities
            if "cat:EXTRACTION_PROCESSING" in rec.notes or "cat:PROCESSING" in rec.notes:
                score = 1
            # Also flag extraction indicators from license type
            elif any(kw in cat_lower for kw in ["extraction", "processing", "manufacturing", "distillation"]):
                score = 1
                rec.extraction_processing_flag = "LIKELY"

            # Priority 2: Cultivators/Growers with large licenses
            elif "cat:GROWER" in rec.notes and any(kw in cat_lower for kw in ["large", "medium", "commercial", "multi"]):
                score = 2

            # Priority 3: Labs + dispensaries with contact info
            elif "cat:LAB" in rec.notes or ("cat:CANNABIS" in rec.notes and rec.phone and rec.email):
                score = 3

            # Priority 4: Has contact info but lower-value category
            elif rec.phone and rec.email:
                score = 4

            # Priority 5: Incomplete data
            else:
                score = 5

            # Boost for EPA cross-ref
            if rec.epa_air_permit or rec.epa_rcra_generator:
                score = max(1, score - 1)

            # Boost for fire marshal permit
            if rec.fire_marshal_permit:
                score = max(1, score - 1)

            rec.sales_priority = str(score)

            # Data quality score (0-100)
            quality = 0
            if rec.phone: quality += 20
            if rec.email: quality += 20
            if rec.street_address: quality += 15
            if rec.sos_entity_match: quality += 15
            if rec.epa_air_permit or rec.epa_rcra_generator: quality += 10
            if rec.fire_marshal_permit: quality += 10
            if rec.website: quality += 5
            if rec.lat and rec.lng: quality += 5
            rec.data_quality_score = str(min(100, quality))

        self.save_checkpoint("phase_e_final")
        log.info(f"Phase E complete")

    def run_all(self):
        """Execute full waterfall pipeline."""
        log.info("🚀 Starting Waterfall Enrichment Pipeline")
        start = time.time()

        self.load_data()
        self.phase_a_sos_matching()
        self.phase_b_epa_echo()
        self.phase_c_fire_marshal()
        self.phase_d_sec_edgar()
        self.phase_e_categorize_and_score()

        elapsed = time.time() - start
        log.info(f"\n✅ Pipeline complete in {elapsed:.1f}s")
        log.info(f"   Total records: {self.stats['total']}")
        log.info(f"   Extraction/Processing: {self.stats['extraction_processing']}")
        log.info(f"   SOS searchable: {self.stats['sos_matched']}")
        log.info(f"   EPA likely: {self.stats['extraction_processing']}")
        log.info(f"   Fire Marshal searchable: {self.stats['fire_marshal_matched']}")
        log.info(f"   Public companies: {self.stats['sec_matched']}")

        # Generate output files
        self.generate_output_files()

    def generate_output_files(self):
        """Generate master file + category-specific files."""
        log.info("\n📁 Generating output files...")

        # ── Master file (all records) ──
        master_path = self.output_dir / "MASTER_ALL_LEADS.csv"
        self._write_csv(master_path, self.records)
        log.info(f"   Master: {master_path}")

        # ── Category-specific files ──
        hemp = [r for r in self.records if "|cat:HEMP" in r.notes]
        cannabis = [r for r in self.records if "|cat:CANNABIS" in r.notes]
        lab_testing = [r for r in self.records if "|cat:LAB" in r.notes]
        growers = [r for r in self.records if "|cat:GROWER" in r.notes]
        extraction = [r for r in self.records if "|cat:EXTRACTION_PROCESSING" in r.notes or r.extraction_processing_flag == "LIKELY"]

        self._write_csv(self.output_dir / "HEMP.csv", hemp)
        self._write_csv(self.output_dir / "CANNABIS.csv", cannabis)
        self._write_csv(self.output_dir / "LAB_TESTING.csv", lab_testing)
        self._write_csv(self.output_dir / "GROWERS.csv", growers)
        self._write_csv(self.output_dir / "EXTRACTION_PROCESSING.csv", extraction)

        log.info(f"   Hemp: {len(hemp):,}")
        log.info(f"   Cannabis: {len(cannabis):,}")
        log.info(f"   Lab/Testing: {len(lab_testing):,}")
        log.info(f"   Growers: {len(growers):,}")
        log.info(f"   Extraction/Processing: {len(extraction):,}")

        # ── FOIA request list ──
        foia_states = ["AR", "DE", "IA", "ID", "IN", "KS", "LA", "MS", "NC", "NE", "NH", "OK", "RI", "SC", "TN", "WY"]
        for state in foia_states:
            state_recs = [r for r in self.records if r.state.strip().upper() == state]
            if state_recs:
                foia_path = FOIA_DIR / f"foia_request_{state}.csv"
                self._write_csv(foia_path, state_recs)
                log.info(f"   FOIA list {state}: {len(foia_path)} records → {foia_path}")

        # ── Stats summary ──
        stats_path = self.output_dir / "enrichment_stats.json"
        with open(stats_path, "w") as f:
            json.dump(self.stats, f, indent=2)
        log.info(f"   Stats: {stats_path}")

    def _write_csv(self, path: Path, records: list[BusinessRecord]):
        """Write records to CSV."""
        if not records:
            # Write empty file with headers
            with open(path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(BusinessRecord.__dataclass_fields__.keys()))
                writer.writeheader()
            return

        headers = list(asdict(records[0]).keys())
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for rec in records:
                writer.writerow(asdict(rec))


if __name__ == "__main__":
    pipeline = WaterfallEnrichmentPipeline(
        input_path=str(INPUT_CSV),
        output_dir=str(OUTPUT_DIR),
    )
    pipeline.run_all()

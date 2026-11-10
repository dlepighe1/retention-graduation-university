"""Finalize an extracted Tableau package without changing the source data.

Usage: python scripts/prepare_tableau.py dashboard/gies_dashboard_extracted.twbx
Create the input in Tableau Desktop with all three sources set to Extract,
then File > Export Packaged Workbook. Open the output in Tableau Public to QA.
"""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def prepare(source: Path, target: Path):
    ET.register_namespace("user", "http://www.tableausoftware.com/xml/user")
    with zipfile.ZipFile(source) as package:
        workbook = next(n for n in package.namelist() if n.endswith(".twb"))
        root = ET.fromstring(package.read(workbook))
        sources = root.findall("./datasources/datasource[extract]")
        if len(sources) != 3:
            raise ValueError("Expected extracts for all three data sources")
        assets = {}
        names = {"federated.rates": "dair_rates", "federated.enroll": "dair_enrollment",
                 "federated.peers": "ipeds_peers"}
        for source_node in sources:
            name = names[source_node.get("name")]
            extract = source_node.find("./extract/connection")
            old_path = extract.get("dbname")
            new_path = f"Data/Extracts/{name}.hyper"
            assets[new_path] = package.read(old_path)
            extract.set("dbname", new_path)
            extract.attrib.pop("updated-database", None)
            for connection in source_node.findall("./connection/named-connections/named-connection/connection"):
                if connection.get("class") == "textscan":
                    connection.set("directory", "Data/Gies")
                    assets[f"Data/Gies/{name}.csv"] = (ROOT / f"data/clean/{name}.csv").read_bytes()

        # Keep parameter definitions and their worksheet copies synchronized.
        for column in root.iter("column"):
            value = {"[IPEDS year]": '"2023"', "[Peer group]": '"All public research peers"'}.get(column.get("name"))
            if value is not None and column.get("param-domain-type"):
                column.set("value", value)
                column.find("calculation").set("formula", value)

        trend = root.find("./worksheets/worksheet[@name='Retention and graduation']")
        for axis in trend.findall(".//encoding[@attr='space']"):
            for attr in ("min", "max", "range-type"):
                axis.attrib.pop(attr, None)
        # Do not persist local-machine identifiers in the repository artifact.
        for attr in list(root.attrib):
            if "WorkbookFingerprinting" in attr:
                del root.attrib[attr]

        ET.indent(root, space="  ")
        xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        target.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as output:
            output.writestr("gies_dashboard.twb", xml)
            for name, data in assets.items():
                output.writestr(name, data)
        print(f"Created {target}: three extracts, automatic outcome axes, 2023/all-peer defaults")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "dashboard/gies_dashboard.twbx")
    args = parser.parse_args()
    prepare(args.source, args.output)

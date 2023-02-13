#!/usr/bin/python3
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
#

"""Script to process Trivy vulnerability scans reports and send those to Jira automation"""

import argparse
import json
import os
from pathlib import Path

import requests


def parse_json(filename):
    """Parse JSON file"""
    record_list = []
    with open(filename, "r") as json_file:
        data = json.load(json_file)

    artifact = data["ArtifactName"]

    if "Results" not in data:
        # no scan results found, skip this report
        print(f"No results in report {filename}")
        return []

    for result in data["Results"]:
        if "Vulnerabilities" not in result or len(result["Vulnerabilities"]) == 0:
            # no vulnerabilities found, skip this report
            continue

        vuln_list = result["Vulnerabilities"]
        for vuln in vuln_list:
            artifact = artifact.replace(":", "-")
            artifact = artifact.replace("/", "-")
            record_name = f"{vuln['VulnerabilityID']}-{artifact}-{vuln['PkgName']}"
            record_list.append(
                {
                    "name": record_name,
                    "artifact": artifact,
                    "severity": vuln["Severity"],
                    "cve_id": vuln["VulnerabilityID"],
                    "package_name": vuln["PkgName"],
                    "installed_version": vuln["InstalledVersion"],
                    "fixed_version": vuln["FixedVersion"],
                    "title": vuln["Title"],
                    "description": vuln["Description"],
                    "references": "\n".join(vuln["References"]),
                    "primary_url": vuln["PrimaryURL"],
                }
            )

    return record_list


def parse_sarif(filename):
    """Parse SARIF file"""
    record_list = []
    with open(filename, "r") as json_file:
        data = json.load(json_file)
    if "runs" not in data and "tool" not in data["runs"][0]:
        # no scan results found, skip this report
        print(f"No results in report {filename}")
        return []

    rules = data["runs"][0]["tool"]["driver"]["rules"]
    results = data["runs"][0]["results"]

    for result in results:
        record_result = result
        record_rule = rules[result["ruleIndex"]]

        record_message = record_result["message"]["text"].split("\n")
        pkg_name = record_message[0].replace("Package: ", "")
        artifact = os.path.basename(filename).replace(".sarif", "")
<<<<<<< HEAD
        record_name = str(result["ruleId"] + "-" + artifact + "-" + pkg_name)
=======
        record_name = str(
            result["ruleId"] + "-" + artifact + "-" + pkg_name
        )
>>>>>>> fba520afbead71fbc7653d973b629efaed9a651d
        record_list.append(
            {
                "name": record_name,
                "artifact": artifact,
                "severity": record_message[3].replace("Severity: ", ""),
                "cve_id": result["ruleId"],
                "package_name": pkg_name,
                "installed_version": record_message[1].replace("Installed Version: ", ""),
                "fixed_version": record_message[4].replace("Fixed Version: ", ""),
                "title": record_rule["shortDescription"]["text"],
                "description": record_rule["help"]["text"],
                "references": "N/A",
                "primary_url": record_rule["helpUri"],
            }
        )

    return record_list


def main(report_path, jira_url):
    input_path = Path(report_path)

    file_list = []
    if input_path.is_dir():
        # directory is supplied, retrieve list of files
        file_list = list(input_path.iterdir())
    elif input_path.is_file():
        file_list.append(input_path)

    for file in file_list:
        print(f"Processing report in: {file}")
        if file.suffix == ".json":
            records = parse_json(file)
        elif file.suffix == ".sarif":
            records = parse_sarif(file)
        else:
            print(f"Unsupported file type: {file}. Skip it.")
            continue

        # send records
        for record in records:
            requests.post(jira_url, json=record)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-path")
    parser.add_argument("--jira-url")
    args = parser.parse_args()
    main(args.report_path, args.jira_url)

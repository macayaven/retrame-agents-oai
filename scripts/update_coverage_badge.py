#!/usr/bin/env python3
"""Update coverage badge based on test results."""

import json
import subprocess
import sys


def get_coverage_percentage():
    """Run tests with coverage and extract the percentage."""
    try:
        # Run pytest with coverage
        result = subprocess.run(
            ["uv", "run", "pytest", "--cov=app", "--cov-report=json", "-q"],
            capture_output=True,
            text=True
        )
        
        # Read the coverage report
        with open("coverage.json", "r") as f:
            coverage_data = json.load(f)
        
        # Get total coverage percentage
        percent = coverage_data["totals"]["percent_covered"]
        return round(percent)
    
    except Exception as e:
        print(f"Error getting coverage: {e}")
        return None


def get_badge_color(percentage):
    """Determine badge color based on coverage percentage."""
    if percentage >= 80:
        return "brightgreen"
    elif percentage >= 70:
        return "green"
    elif percentage >= 60:
        return "yellow"
    elif percentage >= 50:
        return "orange"
    else:
        return "red"


def main():
    """Update coverage badge."""
    coverage = get_coverage_percentage()
    
    if coverage is None:
        print("Failed to get coverage percentage")
        sys.exit(1)
    
    color = get_badge_color(coverage)
    
    print(f"Coverage: {coverage}%")
    print(f"Badge color: {color}")
    print(f"Badge URL: https://img.shields.io/badge/coverage-{coverage}%25-{color}")
    
    # TODO: Update README.md with the badge URL
    # For now, just output the results
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
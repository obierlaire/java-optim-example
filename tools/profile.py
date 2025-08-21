#!/usr/bin/env python3
"""
Minimal JFR hotspot analyzer for txtmark package
Usage: python jfr_analyzer.py profile.jfr output.json
"""

import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from parse import parse


def parse_jfr_samples(jfr_file, package_filter="com.github.rjeschke.txtmark"):
    """Parse JFR ExecutionSample events and extract hotspots"""

    # Run jfr print command
    result = subprocess.run(
        ['jfr', 'print', '--events', 'jdk.ExecutionSample', jfr_file],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"Error running jfr: {result.stderr}")
        return []

    # Parse samples
    samples = []
    lines = result.stdout.split('\n')
    current_sample = None
    in_stack = False

    for line in lines:
        line = line.strip()

        if line.startswith('jdk.ExecutionSample'):
            current_sample = []
            in_stack = False
        elif 'stackTrace = [' in line:
            in_stack = True
        elif in_stack and line and not line.startswith('}'):
            # Parse stack frame: "com.package.Class.method(args) line: 123"
            if package_filter in line and 'line:' in line:
                current_sample.append(line)
        elif line == '}' and current_sample:
            if current_sample:  # Only add if we found relevant frames
                samples.append(current_sample[0])  # Take top frame only
            current_sample = None
            in_stack = False

    return samples


def extract_hotspots(samples):
    """Extract hotspots from samples"""

    # Count occurrences of each line
    line_counts = defaultdict(int)
    line_info = {}

    for sample in samples:
        # Parse: "com.github.rjeschke.txtmark.Emitter.getToken(String, int) line: 841"
        result = parse("{}.{class_name}.{method_name}({}) line: {line_num:d}", sample)
        if result:
            class_name = result['class_name']
            method_name = result['method_name'] 
            line_num = result['line_num']

            key = f"{class_name}:{line_num}"
            line_counts[key] += 1
            line_info[key] = {
                'filename': f"{class_name}.java",
                'method': method_name,
                'line': line_num
            }

    # Convert to percentages and sort
    total_samples = len(samples)
    hotspots = []

    for key, count in line_counts.items():
        info = line_info[key]
        cpu_percent = (count / total_samples) * 100

        # Read source code line
        code_line = read_source_line(info['filename'], info['line'])

        hotspots.append({
            'cpu_percent': round(cpu_percent, 2),
            'filename': info['filename'],
            'line': info['line'],
            'method': info['method'],
            'code': code_line
        })

    # Sort by CPU percentage
    hotspots.sort(key=lambda x: x['cpu_percent'], reverse=True)
    return hotspots, total_samples


def read_source_line(filename, line_num):
    """Read specific line from source file"""
    
    import glob
    
    # Search for the file in target/src and workspace/target/src
    search_patterns = [
        f"target/src/**/{filename}",
        f"/workspace/target/src/**/{filename}",
        f"src/**/{filename}",
        filename
    ]
    
    for pattern in search_patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            path = matches[0]  # Take first match
            try:
                with open(path, 'r') as f:
                    lines = f.readlines()
                    if 1 <= line_num <= len(lines):
                        return lines[line_num - 1].strip()
            except:
                continue

    return f"<source not found: {filename}:{line_num}>"


def main():
    if len(sys.argv) != 3:
        print("Usage: python jfr_analyzer.py <jfr_file> <output_json>")
        sys.exit(1)

    jfr_file = sys.argv[1]
    output_file = sys.argv[2]

    if not os.path.exists(jfr_file):
        print(f"JFR file not found: {jfr_file}")
        sys.exit(1)

    # Parse samples
    print("Parsing JFR samples...")
    samples = parse_jfr_samples(jfr_file)
    print(f"Found {len(samples)} relevant samples")

    if not samples:
        print("No samples found for txtmark package")
        sys.exit(1)

    # Extract hotspots
    print("Analyzing hotspots...")
    hotspots, total_samples = extract_hotspots(samples)

    # Generate output
    output = {
        "hotspots": hotspots,
        "total_samples": total_samples,
        "analysis_info": {
            "package_filter": "com.github.rjeschke.txtmark",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    }

    # Write JSON
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"Analysis complete! Results written to {output_file}")
    print(f"Found {len(hotspots)} hotspots from {total_samples} samples")

    # Show top 5 hotspots
    print("\nTop 5 hotspots:")
    for i, hotspot in enumerate(hotspots[:5], 1):
        print(
            f"{i}. {hotspot['filename']}:{hotspot['line']} ({hotspot['cpu_percent']}%) - {hotspot['method']}")


if __name__ == "__main__":
    main()

import requests
import argparse
import os
import re


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate the nt2py README content for the documentation"
    )
    parser.add_argument(
        "--branch",
        default="master",
        type=str,
        help="Git branch to use for fetching the README.md file",
    )
    cwd = os.path.dirname(os.path.abspath(__file__))
    parser.add_argument(
        "--output",
        default=os.path.join(cwd, "..", "docs", "assets", "imported"),
        type=str,
        help="Directory to save the imported README",
    )
    args = parser.parse_args()
    nt2py_url = f"https://raw.githubusercontent.com/entity-toolkit/nt2py/refs/heads/{args.branch}"

    response = requests.get(f"{nt2py_url}/README.md")
    if response.status_code != 200:
        raise FileNotFoundError(f"File README.md not found in branch {args.branch}")

    with open(os.path.join(args.output, "nt2py-readme.md"), "w") as f:
        readme_content = response.text[
            response.text.index("## Usage") : response.text.index("## Features")
        ].strip()
        readme_content = re.sub("^### ", "#### ", readme_content)
        readme_content = readme_content.replace("## ", "### ")
        f.write(readme_content)

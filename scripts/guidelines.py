import requests
import argparse
import os
import re


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate coding guidelines from the CODEGUIDE.md file in the repository"
    )
    parser.add_argument(
        "--branch",
        default="master",
        type=str,
        help="Git branch to use for fetching the CODEGUIDE.md file",
    )
    cwd = os.path.dirname(os.path.abspath(__file__))
    parser.add_argument(
        "--output",
        default=os.path.join(cwd, "..", "docs", "assets", "imported"),
        type=str,
        help="Directory to save the imported guidelines",
    )
    args = parser.parse_args()
    entity_url = f"https://raw.githubusercontent.com/entity-toolkit/entity/refs/heads/{args.branch}"

    response = requests.get(f"{entity_url}/CODEGUIDE.md")
    if response.status_code != 200:
        raise FileNotFoundError(f"File CODEGUIDE.md not found in branch {args.branch}")

    with open(os.path.join(args.output, "code-guidelines.md"), "w") as f:
        readme_content = response.text[response.text.index("## Testing") :].strip()
        readme_content = re.sub("^### ", "#### ", readme_content)
        readme_content = readme_content.replace("## ", "### ")
        readme_content = readme_content.replace("    *", "      *")
        readme_content = readme_content.replace("  *", "    *")
        f.write(readme_content)

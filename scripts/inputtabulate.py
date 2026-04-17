import requests
import tomlparser as tp
import argparse
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch and parse TOML file from GitHub"
    )
    parser.add_argument(
        "--branch",
        type=str,
        default="master",
        help="Branch name to fetch the input file from",
    )
    cwd = os.path.dirname(os.path.abspath(__file__))

    parser.add_argument(
        "--output",
        type=str,
        default=os.path.join(cwd, "..", "docs", "assets", "meta"),
        help="Output HTML file path",
    )
    args = parser.parse_args()

    url = f"https://raw.githubusercontent.com/entity-toolkit/entity/refs/heads/{args.branch}/input.example.toml"
    response = requests.get(url)

    content = None
    if response.status_code == 200:
        content = response.content
        tree = tp.Tree()
        tree.from_text(content.decode("utf-8"))
        tree.export_html(os.path.join(args.output, "input-table.html"))
    else:
        raise Exception(
            f"Failed to fetch the input file from {url}. Status code: {response.status_code}"
        )

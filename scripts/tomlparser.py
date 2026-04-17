import textwrap
import re


def convert_value(value: str) -> str:
    def is_float(element: str) -> bool:
        try:
            _ = float(element)
            return True
        except ValueError:
            return False

    def is_bool(element: str) -> bool:
        return element.lower() in ["true", "false"]

    def is_string(element: str) -> bool:
        return (
            element.startswith('"')
            and element.endswith('"')
            or element.startswith("'")
            and element.endswith("'")
        )

    if is_float(value):
        if "e" in value:
            d1, d2 = value.split("e", 1)
            if d1 == "1":
                value = rf"10^{{{d2}}}"
            else:
                value = rf"{d1}\cdot 10^{{{d2}}}"
        value = f"${value}$"
    elif is_string(value):
        value = f"<pre>{value}</pre>"
    elif is_bool(value):
        value = f"<pre>{value}</pre>"

    return value


class Node:
    def __init__(self, name: str, attrs: dict[str, str | bool] | None):
        self._id: int = id(self)
        self._name: str = name
        self._attrs: dict[str, str | bool] | None = attrs
        self._children: list[Node] = []
        self._parent: Node | None = None

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def attrs(self) -> dict[str, str | bool] | None:
        return self._attrs

    @property
    def children(self):
        return self._children

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent: "Node"):
        self._parent = parent

    @property
    def is_final(self) -> bool:
        return len(self._children) == 0 and self.name != "setup"

    @property
    def is_root(self) -> bool:
        return self._parent is None

    def add_child(self, path: str, attrs: dict[str, str | bool] | None = None):
        path_parts = path.split(".")
        child = self.find_child(path_parts[0])
        if child is None:
            child = Node(path_parts[0], None if len(path_parts) > 1 else attrs)
            child.parent = self
            self._children.append(child)
        if len(path_parts) > 1:
            child.add_child(".".join(path_parts[1:]), attrs)

    def find_child(self, path: str) -> "Node | None":
        path_parts = path.split(".")
        for child in self._children:
            if child.name == path_parts[0]:
                if len(path_parts) > 1:
                    return child.find_child(".".join(path_parts[1:]))
                return child
        return None

    def print(self, indent: int = 0) -> str:
        repr = " " * indent + self.name
        if self.attrs is not None and self.attrs.get("required", False):
            repr += " [*]"
        if self.attrs is not None and self.attrs.get("inferred", False):
            repr += " [->]"
        repr += "\n"
        for child in self._children:
            repr += child.print(indent + 2)
        return repr

    def html(self, depth: int, indent: int | None = 0) -> str:
        def ind(extra: int) -> str:
            if indent is None:
                return ""
            return " " * (indent + extra)

        required = False
        inferred = False
        typ = ""
        desc = ""
        dflt = ""
        if self.attrs is not None:
            # Whether the node is required or inferred
            if self.attrs.get("required", False):
                required = True
            elif self.attrs.get("inferred", False):
                inferred = True

            # Type
            if self.attrs.get("type", None) is not None:
                assert isinstance(self.attrs["type"], str), "Type should be a string"
                tt = self.attrs["type"]
                tt = tt.replace("<", "&lt;").replace(">", "&gt;")
                tt = " or ".join(
                    [f'<pre class="type">{el}</pre>' for el in tt.split("|")]
                )
                # Type limitations as tooltip
                comm = re.search(r"\[([^\]]+)\]", tt)
                if comm is not None:
                    tt = tt.replace(comm.group(0), "").strip()
                    comm = comm.group(1)
                else:
                    comm = ""
                comm = comm.replace("inf", "∞")
                if self.attrs.get("enum", None) is not None:
                    assert isinstance(
                        self.attrs["enum"], str
                    ), "Enum should be a list of strings"
                    tt = f'<div class="type-tooltip">{tt}<span class="tooltiptext">{self.attrs["enum"]}</span></div>'
                elif comm != "":
                    tt = f'<div class="type-tooltip">{tt}<span class="tooltiptext">{comm}</span></div>'
                typ = tt

            # Description
            if self.attrs.get("description", None) is not None:
                assert isinstance(
                    self.attrs["description"], str
                ), "Description should be a string"
                desc = self.attrs["description"]
            elif self.attrs.get("brief", None) is not None:
                assert isinstance(self.attrs["brief"], str), "Brief should be a string"
                desc = self.attrs["brief"]
            desc = re.sub(r"(^|\s+)`", r"\1<code>", desc)
            desc = re.sub(r"`", "</code>", desc)
            # Note as tooltip
            if self.attrs.get("note", None) is not None:
                assert isinstance(self.attrs["note"], str), "Note should be a string"
                note = self.attrs["note"].replace("<", "&lt;").replace(">", "&gt;")
                if len(note.split("\n")) > 1:
                    note = (
                        re.sub("^", "* ", note)
                        .replace(".\n", ".<br>* ")
                        .replace("\n", ".<br>* ")
                    )
                if not note.endswith("."):
                    note += "."
                note = re.sub(r"(^|\s+)`", r"\1<pre>", note)
                note = re.sub(r"`", "</pre>", note)
                desc = f'<div class="note-tooltip"><span class="description">{desc}</span><span class="tooltiptext">{note}</span></div>'

            # Default value
            if self.attrs.get("default", None) is not None:
                assert isinstance(
                    self.attrs["default"], str
                ), "Default value should be a string"
                dflt = self.attrs["default"]
                dflt = dflt.replace("<", "&lt;").replace(">", "&gt;")
                dflt = re.sub(r"(^|\s+)`", r"\1<code>", dflt)
                dflt = re.sub(r"`", "</code>", dflt)

                if dflt.startswith("[") and dflt.endswith("]"):
                    dflt = dflt[1:-1].strip().split(",")
                    dflt = ", ".join([convert_value(d.strip()) for d in dflt])
                    if "$" in dflt:
                        dflt = "$[" + dflt.replace("$", "") + "]$"
                    else:
                        dflt = f"[{dflt}]"
                else:
                    dflt = convert_value(dflt)

        classes: list[str] = []
        if not self.is_final:
            classes.append("category")
        if inferred:
            classes.append("inferred")
        elif required:
            classes.append("required")
        classes_str: str = ""
        if classes != []:
            classes_str = ' class="' + " ".join(classes) + '"'
        else:
            classes_str = ""
        return (
            textwrap.dedent(
                f"""
            {ind(0)}<tr data-depth="{depth}" data-id="{self.id}"{classes_str}>
            {ind(2)}<td><pre>{self.name}</pre></td>
            {ind(2)}<td>{typ}</td>
            {ind(2)}<td>{desc}</td>
            {ind(2)}<td>{dflt}</td>
            {ind(0)}</tr>
            """
            )
            + "\n".join(
                child.html(depth + 1, indent).strip() for child in self._children
            )
        ).strip()


class Tree:
    def __init__(self):
        self._roots: list[Node] = []

    @property
    def roots(self):
        return self._roots

    @property
    def root_names(self):
        return [root.name for root in self._roots]

    def from_text(self, text: str):
        active_section: str | None = None
        active_inferred: str | None = None
        active_attrs: dict[str, str | bool] = {}
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("["):
                line = line.replace("[", "").replace("]", "")
                active_section = line
                if active_section == "setup":
                    self.add_node("setup", active_attrs)
                    active_attrs = {}
            elif line.endswith('= ""'):
                line = line.split(" = ")[0].strip()
                assert (
                    active_section is not None
                ), "Active section should not be None when assigning attributes"
                self.add_node(".".join([active_section, line]), active_attrs)
                active_attrs = {}
            elif line == "":
                if active_inferred is not None:
                    assert (
                        active_section is not None
                    ), "Active section should not be None"
                    active_attrs["inferred"] = True
                    self.add_node(
                        ".".join([active_section, active_inferred]), active_attrs
                    )
                    active_inferred = None
                    active_attrs = {}
                else:
                    assert (
                        active_attrs == {}
                    ), f"Active attributes should be empty on empty line: {active_attrs}"
            elif line.startswith("# "):
                line = line[2:].strip()
                if line == "@inferred":
                    continue
                elif line.startswith("- "):
                    if active_inferred is not None:
                        assert (
                            active_section is not None
                        ), "Active section should not be None"
                        active_attrs["inferred"] = True
                        self.add_node(
                            ".".join([active_section, active_inferred]), active_attrs
                        )
                        active_attrs = {}
                    line = line[2:].strip()
                    active_inferred = line
                elif line.startswith("@required"):
                    active_attrs["required"] = True
                elif line.startswith("@"):
                    line = line[1:].strip()
                    attr = line.split(":", 1)[0]
                    val = line.split(":", 1)[1].strip()
                    if attr != "note" and attr != "example" and attr in active_attrs:
                        raise ValueError(
                            f"Attribute '{attr}' already exists in active attributes: {active_attrs}"
                        )
                    elif (attr == "note" or attr == "example") and attr in active_attrs:
                        assert isinstance(
                            val, str
                        ), f"Value for 'note' should be a string, but found: {val}"
                        active_attrs_attr = active_attrs[attr]
                        assert isinstance(
                            active_attrs_attr, str
                        ), f"Attribute '{attr}' should be a string, but found: {active_attrs[attr]}"
                        active_attrs_attr += f"\n{val}"
                        active_attrs[attr] = active_attrs_attr
                    else:
                        active_attrs[attr] = val
                elif line != "":
                    active_attrs["description"] = line

    def find_root(self, name: str) -> Node | None:
        for root in self._roots:
            if root.name == name:
                return root
        return None

    def find_node(self, path: str) -> Node | None:
        path_parts = path.split(".")
        root = self.find_root(path_parts[0])
        if root is None:
            return None
        elif len(path_parts) == 1:
            return root
        else:
            return root.find_child(".".join(path_parts[1:]))

    def add_node(self, path: str, attrs: dict[str, str | bool]):
        path_parts = path.split(".")
        root = self.find_root(path_parts[0])
        if root is None:
            root = Node(path_parts[0], None if len(path_parts) > 1 else attrs)
            self._roots.append(root)
        if len(path_parts) > 1:
            root.add_child(".".join(path_parts[1:]), attrs)

    def print(self) -> str:
        repr = ""
        for root in self._roots:
            repr += root.print()
        return repr

    def html(self, indent: int | None = 0) -> str:
        def ind(extra: int) -> str:
            if indent is None:
                return ""
            return " " * (indent + extra)

        return (
            textwrap.dedent(
                f"""
            {ind(0)}<table id="input-table">
            {ind(2)}<thead>
            {ind(4)}<tr>
            {ind(6)}<th>parameter</th>
            {ind(6)}<th>type</th>
            {ind(6)}<th>description</th>
            {ind(6)}<th>default</th>
            {ind(4)}</tr>
            {ind(2)}</thead>
            {ind(2)}<tbody>
            """
            )
            + "\n".join(
                textwrap.indent(root.html(0, indent), ind(4)) for root in self._roots
            )
            + textwrap.dedent(
                f"""
            {ind(2)}</tbody>
            {ind(0)}</table>
            """
            )
        ).strip()

    def export_html(self, filename: str):
        with open(filename, "w") as f:
            f.write(self.html())

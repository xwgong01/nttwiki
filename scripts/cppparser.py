import tree_sitter_cpp as tscpp
from tree_sitter import Language, Parser
from enum import Enum
from typing import override


class CPPAccessType(Enum):
    PRIVATE = "private"
    PROTECTED = "protected"
    PUBLIC = "public"

    def __str__(self):
        return self.value


def replace_type(type_str: str) -> str:
    if type_str.startswith("std::pair<") and type_str.endswith(">"):
        inner_types = type_str[10:-1].split(", ")
        return f"{replace_type(inner_types[0])},{replace_type(inner_types[1])}"
    return (
        type_str.replace("std::", "")
        .replace("<", "~")
        .replace(">", "~")
        .replace("Dim::_", "")
        .replace("::type", "")
        .replace("::", r"\:\:")
        .replace("unsigned ", "u")
    )


class CPPVariable:
    def __init__(
        self, name: str, type_: str, is_const: bool = False, is_static: bool = False
    ):
        assert name != "" or type_ != "", "Variable name and type cannot be empty"
        self._name: str = name
        self._type: str = type_
        self._is_static: bool = is_static
        self._is_const: bool = is_const

    @property
    def name(self) -> str:
        return self._name

    @property
    def type(self) -> str:
        return self._type

    @property
    def is_const(self) -> bool:
        return self._is_const

    @property
    def is_static(self) -> bool:
        return self._is_static

    @override
    def __repr__(self) -> str:
        prefix = ""
        if self.is_static:
            prefix += "static "
        if self.is_const:
            prefix += "const "
        return f"{prefix}{self.type} {self.name}".strip()

    def mermaid(self) -> str:
        return f"{'const ' if self.is_const else ''}{replace_type(self.type)} {self.name}{'$' if self.is_static else ''}"


class CPPFunction:
    def __init__(
        self,
        name: str,
        return_: CPPVariable | None = None,
        args: list[CPPVariable] | None = None,
        template_args: list[CPPVariable] | None = None,
        is_const: bool = False,
        is_virtual: bool = False,
        is_override: bool = False,
        is_final: bool = False,
    ):
        self._name = name
        self._return = return_
        self._args = args if args is not None else []
        self._template_args = template_args if template_args is not None else []
        self._is_const = is_const
        self._is_virtual = is_virtual
        self._is_override = is_override
        self._is_final = is_final

    @property
    def name(self) -> str:
        return self._name

    @property
    def template_args(self) -> list[CPPVariable]:
        return self._template_args

    @property
    def args(self) -> list[CPPVariable]:
        return self._args

    @property
    def return_type(self) -> CPPVariable | None:
        return self._return

    @property
    def is_template(self) -> bool:
        return self._template_args is not None and len(self._template_args) > 0

    @override
    def __repr__(self) -> str:
        tmpl = (
            f"template<{', '.join(map(str, self.template_args))}> "
            if self.is_template
            else ""
        )
        ret = str(self.return_type.type) if self.return_type else "void"
        args = ", ".join(map(str, self.args))
        return f"{tmpl}{ret} {self.name}({args})"

    def mermaid(self) -> str:
        ret = "const " if self._is_const else ""
        args = ", ".join(arg.mermaid() for arg in self.args)
        ret = f"{ret}{self.name}({args})"
        if self.return_type:
            ret += " " + replace_type(self.return_type.type)
        return ret


class CPPClass:
    def __init__(self, name: str, template_args: list[CPPVariable] | None = None):
        self._name = name
        self._template_args = template_args if template_args is not None else []
        self._methods: list[tuple[CPPFunction, CPPAccessType]] = []
        self._variables: list[tuple[CPPVariable, CPPAccessType]] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def template_args(self) -> list[CPPVariable]:
        return self._template_args

    @property
    def methods(self) -> list[tuple[CPPFunction, CPPAccessType]]:
        return self._methods

    @property
    def variables(self) -> list[tuple[CPPVariable, CPPAccessType]]:
        return self._variables

    def add_method(self, method: CPPFunction, access_type: CPPAccessType):
        self._methods.append((method, access_type))

    def add_variable(self, variable: CPPVariable, access_type: CPPAccessType):
        self._variables.append((variable, access_type))

    @property
    def is_template(self) -> bool:
        return self._template_args is not None and len(self._template_args) > 0

    @override
    def __repr__(self) -> str:
        tmpl = (
            f"template<{', '.join(map(str, self.template_args))}> "
            if self.is_template
            else ""
        )
        header = f"{tmpl}class {self.name}"

        vars_str = "\n  // Variables\n" + "\n".join(
            f"  [{access}] {var}" for var, access in self.variables
        )
        meth_str = "\n  // Methods\n" + "\n".join(
            f"  [{access}] {meth}" for meth, access in self.methods
        )
        return f"{header} {{\n{vars_str}\n{meth_str}\n}};"

    def mermaid(self, indent: int = 0) -> str:
        filtered_methods = [
            (meth, access)
            for meth, access in self.methods
            if (meth.return_type) and (meth.return_type.type != self.name)
        ]
        templates = (
            ", ".join(replace_type(t.type) for t in self.template_args)
            if self.is_template
            else ""
        )
        if templates != "":
            templates = f"~{templates}~"
        ret = f"class {self.name}{templates} {{\n"
        ret += "\n".join(
            f"  {'+' if access == CPPAccessType.PUBLIC else ('#' if access == CPPAccessType.PROTECTED else '-')}{var.mermaid()}"
            for var, access in self.variables
        )
        ret += "\n"
        ret += "\n".join(
            f"  {'+' if access == CPPAccessType.PUBLIC else ('#' if access == CPPAccessType.PROTECTED else '-')}{meth.mermaid()}"
            for meth, access in filtered_methods
        )
        ret += "\n}"
        if indent > 0:
            ret = " " * indent + ret.replace("\n", "\n" + " " * indent)
        return ret


class CPPParser:
    def __init__(self, source_code: str):
        self.source_code = source_code
        CPP_LANGUAGE = Language(tscpp.language())
        parser = Parser(CPP_LANGUAGE)
        tree = parser.parse(bytes(source_code, "utf8"))
        self.root_node = tree.root_node

    def _get_text(self, node) -> str:
        if node is None:
            return ""
        return self.source_code[node.start_byte : node.end_byte]

    def _get_function_return_type_text(self, func_node) -> str | None:
        leading_type_node = func_node.child_by_field_name("type")
        if not leading_type_node:
            return None
        leading_type_text = self._get_text(leading_type_node)
        if leading_type_text == "auto":
            fdec = [c for c in func_node.children if c.type == "function_declarator"]
            if len(fdec) == 0:
                return "auto"
            fdec = self._get_text(fdec[0])
            if "->" in fdec:
                trailing_return_type = fdec.split("->")[-1].strip()
                return trailing_return_type
            return "auto"
        else:
            return leading_type_text

    def _parse_function_from_components(
        self, func_node, declarator_node, template_args, class_name
    ):
        return_type_text = self._get_function_return_type_text(func_node)

        if return_type_text is None:
            return_var = CPPVariable(name="", type_=class_name)
            name_node = declarator_node
        else:
            return_var = CPPVariable(name="", type_=return_type_text)
            name_node = declarator_node.child_by_field_name("declarator")

        func_name = self._get_text(name_node)
        func_args = self._parse_function_parameters(declarator_node)

        is_const_method = (
            any(c.type == "const_qualifier" for c in declarator_node.children)
            if declarator_node
            else False
        )

        return CPPFunction(
            name=func_name,
            return_=return_var,
            args=func_args,
            template_args=template_args,
            is_const=is_const_method,
        )

    def _parse_template_parameters(self, template_node) -> list[CPPVariable]:
        params = []
        param_list_node = template_node.child_by_field_name("parameters")
        if not param_list_node:
            return params
        for child in param_list_node.named_children:
            if child.type in ("parameter_declaration", "type_parameter_declaration"):
                name = child.child_by_field_name("name")
                type_ = child.child_by_field_name("type")
                if name is None and type_ is None:
                    for child in child.children:
                        if child.type == "type_identifier":
                            name = child
                        elif child.type == "class":
                            type_ = child
                params.append(
                    CPPVariable(
                        name=self._get_text(name),
                        type_=self._get_text(type_),
                    )
                )
        return params

    def _parse_function_parameters(self, func_declarator_node) -> list[CPPVariable]:
        params = []
        if not func_declarator_node:
            return params
        params_node = func_declarator_node.child_by_field_name("parameters")
        if not params_node:
            return params
        for param_decl in params_node.named_children:
            if param_decl.type == "parameter_declaration":
                type_text = self._get_text(param_decl.child_by_field_name("type"))
                name_text = self._get_text(param_decl.child_by_field_name("declarator"))
                params.append(
                    CPPVariable(
                        name=name_text, type_=type_text, is_const="const" in type_text
                    )
                )
        return params

    def _parse_class(self, class_spec_node) -> CPPClass:
        template_args = []
        if (
            class_spec_node.parent
            and class_spec_node.parent.type == "template_declaration"
        ):
            template_args = self._parse_template_parameters(class_spec_node.parent)

        class_name = self._get_text(class_spec_node.child_by_field_name("name"))
        cpp_class = CPPClass(name=class_name, template_args=template_args)
        default_access = (
            "private" if class_spec_node.type == "class_specifier" else "public"
        )
        current_access = CPPAccessType(default_access)
        body = class_spec_node.child_by_field_name("body")
        if body is None:
            return cpp_class

        for member_node in body.named_children:
            node_type = member_node.type
            if node_type == "access_specifier":
                current_access = CPPAccessType(
                    self._get_text(member_node).rstrip(":").strip()
                )
            elif node_type == "function_definition":
                declarator_node = member_node.child_by_field_name("declarator")
                function = self._parse_function_from_components(
                    member_node, declarator_node, [], class_name
                )
                cpp_class.add_method(function, current_access)
            elif node_type == "template_declaration":
                func_node = member_node.child_by_field_name(
                    "definition"
                ) or member_node.child_by_field_name("declaration")
                if not func_node:
                    continue
                declarator_node = func_node.child_by_field_name("declarator")
                tmpl_args = self._parse_template_parameters(member_node)
                function = self._parse_function_from_components(
                    func_node, declarator_node, tmpl_args, class_name
                )
                cpp_class.add_method(function, current_access)
            elif node_type == "field_declaration":
                specifiers = [
                    self._get_text(c)
                    for c in member_node.children
                    if c.type in ("storage_class_specifier", "type_qualifier")
                ]
                for declarator_node in member_node.children_by_field_name("declarator"):
                    if declarator_node.type == "function_declarator":
                        function = self._parse_function_from_components(
                            member_node, declarator_node, [], class_name
                        )
                        cpp_class.add_method(function, current_access)
                    else:
                        shared_type_text = self._get_text(
                            member_node.child_by_field_name("type")
                        )
                        variable = CPPVariable(
                            name=self._get_text(declarator_node),
                            type_=shared_type_text,
                            is_const="const" in specifiers,
                            is_static="static" in specifiers,
                        )
                        cpp_class.add_variable(variable, current_access)
        return cpp_class

    def find_classes(self) -> list[CPPClass]:
        found_classes = []

        def traverse(node):
            if node.type in ("class_specifier", "struct_specifier"):
                class_obj = self._parse_class(node)
                found_classes.append(class_obj)
                return
            for child in node.children:
                traverse(child)

        traverse(self.root_node)
        return found_classes

from redup.core.classifier import classify_duplicate_group, classify_duplicate_groups
from redup.core.models import DuplicateFragment, DuplicateGroup, DuplicateType, DuplicationMap


def _group(*paths: str, duplicate_type: DuplicateType = DuplicateType.EXACT) -> DuplicateGroup:
    return DuplicateGroup(
        id="G1",
        duplicate_type=duplicate_type,
        fragments=[
            DuplicateFragment(file=path, line_start=1, line_end=10) for path in paths
        ],
    )


def test_classifies_source_to_published_file_as_generated():
    result = classify_duplicate_group(
        _group("js-client/src/client.js", "js-client/client.js")
    )

    assert result["provenance"] == "generated_copy"
    assert result["actionability"] == "generated"


def test_classifies_package_copied_into_web_runtime_as_generated():
    result = classify_duplicate_group(
        _group(
            "app/packages/ifuri-page/handlers.js",
            "app/src/ifuri_app/web/page/handlers.js",
        )
    )

    assert result["provenance"] == "vendored_copy"
    assert result["actionability"] == "generated"


def test_classifies_shared_behavior_in_standalone_public_assets_for_review():
    result = classify_duplicate_group(
        _group(
            "relcom/central-node/public/live-stream.js",
            "relcom/central-node/public/relcom.js",
        )
    )

    assert result["provenance"] == "standalone_assets"
    assert result["actionability"] == "review"


def test_classifies_nested_deployment_mirror_as_generated():
    result = classify_duplicate_group(
        _group("net-user/sites/shop/app.py", "pc1/net-user/sites/shop/app.py")
    )

    assert result["provenance"] == "deployment_mirror"
    assert result["actionability"] == "generated"


def test_classifies_parallel_relative_paths_for_review():
    result = classify_duplicate_group(
        _group("chrome-plugin/content.js", "firefox-plugin/content.js")
    )

    assert result["provenance"] == "platform_variant"
    assert result["actionability"] == "review"


def test_classifies_product_family_for_review():
    result = classify_duplicate_group(
        _group(
            "urirun-contract-filepair/ci/main.py",
            "urirun-contract-windowpair/ci/other.py",
        )
    )

    assert result["provenance"] == "product_family"
    assert result["actionability"] == "review"


def test_classifies_separate_examples_as_cross_component():
    result = classify_duplicate_group(
        _group(
            "examples/33-office/run.py",
            "examples/52-office-vm/run.py",
            duplicate_type=DuplicateType.FUZZY,
        )
    )

    assert result["provenance"] == "cross_component"
    assert result["actionability"] == "review"


def test_keeps_files_in_one_example_actionable():
    result = classify_duplicate_group(
        _group(
            "examples/33-office/run.py",
            "examples/33-office/helpers.py",
            duplicate_type=DuplicateType.FUZZY,
        )
    )

    assert result["provenance"] == "local_duplicate"
    assert result["actionability"] == "refactor"


def test_classifies_same_component_as_actionable():
    group = _group(
        "runtime/commands.py",
        "runtime/helpers.py",
        duplicate_type=DuplicateType.FUZZY,
    )
    group.metadata["model"] = "existing-evidence"

    classify_duplicate_groups([group])

    assert group.metadata["provenance"] == "local_duplicate"
    assert group.metadata["actionability"] == "refactor"
    assert group.metadata["model"] == "existing-evidence"


def test_classifies_distinct_thin_wrappers_for_review():
    group = DuplicateGroup(
        id="G1",
        duplicate_type=DuplicateType.STRUCTURAL,
        fragments=[
            DuplicateFragment(
                file="runtime/api.py",
                line_start=1,
                line_end=5,
                function_name="list_routes",
                text='def list_routes(registry):\n    return project(registry, result="routes")',
            ),
            DuplicateFragment(
                file="runtime/api.py",
                line_start=8,
                line_end=12,
                function_name="list_tools",
                text='def list_tools(registry):\n    return project(registry, result="tools")',
            ),
        ],
    )

    result = classify_duplicate_group(group)

    assert result["provenance"] == "delegating_wrappers"
    assert result["actionability"] == "review"


def test_classifies_lazy_facades_from_one_module_for_review():
    group = DuplicateGroup(
        id="G1",
        duplicate_type=DuplicateType.STRUCTURAL,
        fragments=[
            DuplicateFragment(
                file="runtime/api.py",
                line_start=1,
                line_end=5,
                function_name="command",
                text=(
                    "def command(uri):\n"
                    "    from runtime.routes import uri_command\n"
                    "    return uri_command(uri)"
                ),
            ),
            DuplicateFragment(
                file="runtime/api.py",
                line_start=8,
                line_end=12,
                function_name="handler",
                text=(
                    "def handler(uri):\n"
                    "    from runtime.routes import uri_handler\n"
                    "    return uri_handler(uri)"
                ),
            ),
        ],
    )

    result = classify_duplicate_group(group)

    assert result["provenance"] == "delegating_wrappers"
    assert result["actionability"] == "review"


def test_ignores_code_examples_in_wrapper_docstrings():
    group = DuplicateGroup(
        id="G1",
        duplicate_type=DuplicateType.STRUCTURAL,
        fragments=[
            DuplicateFragment(
                file="runtime/api.py",
                line_start=1,
                line_end=10,
                function_name="command",
                text=(
                    'def command(uri):\n    """Example::\n'
                    "        def sample():\n            return True\n"
                    '    """\n    from runtime.routes import uri_command\n'
                    "    return uri_command(uri)"
                ),
            ),
            DuplicateFragment(
                file="runtime/api.py",
                line_start=12,
                line_end=20,
                function_name="handler",
                text=(
                    'def handler(uri):\n    """Example::\n'
                    "        def sample():\n            return False\n"
                    '    """\n    from runtime.routes import uri_handler\n'
                    "    return uri_handler(uri)"
                ),
            ),
        ],
    )

    result = classify_duplicate_group(group)

    assert result["provenance"] == "delegating_wrappers"
    assert result["actionability"] == "review"


def test_keeps_small_functions_with_control_flow_actionable():
    group = DuplicateGroup(
        id="G1",
        duplicate_type=DuplicateType.STRUCTURAL,
        fragments=[
            DuplicateFragment(
                file="runtime/api.py",
                line_start=1,
                line_end=6,
                function_name="route_a",
                text=(
                    "def route_a(value):\n"
                    "    if value:\n"
                    "        return project(value)\n"
                    "    return {}"
                ),
            ),
            DuplicateFragment(
                file="runtime/api.py",
                line_start=8,
                line_end=13,
                function_name="route_b",
                text=(
                    "def route_b(value):\n"
                    "    if value:\n"
                    "        return project(value)\n"
                    "    return {}"
                ),
            ),
        ],
    )

    result = classify_duplicate_group(group)

    assert result["provenance"] == "same_file"
    assert result["actionability"] == "refactor"


def test_duplication_map_exposes_classification_counts():
    groups = [
        _group("pkg/a.py", "pkg/b.py"),
        _group("client/src/app.js", "client/app.js"),
        _group("chrome/a.js", "firefox/a.js"),
    ]
    classify_duplicate_groups(groups)
    result = DuplicationMap(groups=groups)

    assert result.actionable_groups == 1
    assert result.generated_groups == 1
    assert result.review_groups == 1
    assert result.saved_lines_for("refactor") == 10
    assert result.saved_lines_for("generated") == 10
    assert result.saved_lines_for("review") == 10

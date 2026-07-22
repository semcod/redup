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

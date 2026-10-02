"""Offline Codex/Claude definition checks, not native execution.

Native fields express client intent; these checks demonstrate neither runtime
acceptance, OS enforcement, independent agent behavior nor scientific validity.
"""
from dataclasses import dataclass
from pathlib import Path
import re
import tomllib
from urllib.parse import unquote, urlsplit

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
# Independent expectations from the three portable workflow role contracts.
EXPECTED_ROLES = {
    "develop-mesa-model": {
        "mesa_model_worker", "independent_model_qa", "mesa_model_reviewer",
        "mesa_model_verifier", "model_spec_analyst", "mesa_geo_specialist",
    },
    "document-abm-with-odd": {
        "odd_documenter", "odd_auditor", "model_spec_analyst", "mesa_geo_specialist",
    },
    "evaluate-mesa-model": {
        "experiment_designer", "evaluation_analyst", "model_spec_analyst",
        "mesa_geo_specialist",
    },
}
ALL_ROLES = set.union(*EXPECTED_ROLES.values())
AUTHORING_ROLES = {
    "mesa_model_worker", "independent_model_qa",
    "odd_documenter", "experiment_designer",
}
WRITABLE_ROLES = AUTHORING_ROLES | {"mesa_model_verifier"}
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


@dataclass(frozen=True)
class Client:
    name: str
    extension: str

    def role_file(self, role):
        native_name = role.replace("_", "-") if self.name == "claude-code" else role
        return native_name + self.extension

    def source_agent(self, product, role):
        return product / "integrations" / self.name / "agents" / self.role_file(role)

# Independent expectations from native client formats, not installer tables.
CLIENTS = (
    Client("codex", ".toml"),
    Client("claude-code", ".md"),
)


@pytest.fixture(params=CLIENTS, ids=lambda item: item.name)
def client(request):
    return request.param


def local_links(document, boundary):
    for raw in LINK.findall(document.read_text(encoding="utf-8")):
        url = urlsplit(raw.split()[0].strip("<>"))
        if url.scheme or url.netloc or not url.path:
            continue
        target = (document.parent / unquote(url.path)).resolve()
        assert target.is_relative_to(boundary.resolve()), (document, raw)
        assert not {"internal", ".git", "AGENTS.md"}.intersection(
            target.relative_to(boundary.resolve()).parts
        ), (document, raw)
        assert target.is_file(), (document, raw)


def test_role_inventory_matches_portable_contract(client):
    files = set((ROOT / "integrations" / client.name / "agents").iterdir())
    assert {path.name for path in files} == {client.role_file(role) for role in ALL_ROLES}
    assert len(files) == len(ALL_ROLES) == 10
    assert all(path.is_file() and not path.is_symlink() for path in files)
    for skill, roles in EXPECTED_ROLES.items():
        workflow = ROOT / "skills" / skill / "references" / "workflow.md"
        text = workflow.read_text(encoding="utf-8")
        assert roles <= set(re.findall(r"`([a-z]+(?:_[a-z]+)+)`", text))


@pytest.mark.parametrize("role", sorted(ALL_ROLES))
def test_definition_has_valid_native_fields_and_permission_intent(client, role):
    path = client.source_agent(ROOT, role)
    assert path.is_file() and not path.is_symlink()
    if client.name == "codex":
        with path.open("rb") as stream:
            config = tomllib.load(stream)
        assert set(config) == {"name", "description", "developer_instructions", "sandbox_mode"}
        assert config["name"] == role
        expected_sandbox = "workspace-write" if role in WRITABLE_ROLES else "read-only"
        assert config["sandbox_mode"] == expected_sandbox
        instructions = config["developer_instructions"]
    else:
        document = path.read_text(encoding="utf-8")
        assert document.startswith("---\n")
        frontmatter, instructions = document[4:].split("\n---\n", 1)
        config = yaml.safe_load(frontmatter)
        # This thin adapter deliberately omits model/provider, persistent memory,
        # hooks, plugins, MCP and recursive Agent/Skill tool configuration.
        assert set(config) == {"name", "description", "tools", "permissionMode"}
        assert re.fullmatch(r"[a-z]+(?:-[a-z]+)+", config["name"])
        assert config["name"] == role.replace("_", "-") == path.stem
        assert config["permissionMode"] == "default"
        tools = [tool.strip() for tool in config["tools"].split(",")]
        expected_tools = {"Read", "Grep", "Glob", "Bash"}
        if role in AUTHORING_ROLES:
            expected_tools |= {"Edit", "Write"}
        assert set(tools) == expected_tools
        assert len(tools) == len(expected_tools)
        assert "Shell access is not OS-enforced read-only access" in instructions
        assert "Do not invoke another agent, client, or skill through the shell" in instructions
        if role == "mesa_model_verifier":
            assert "declared temporary outputs or caches" in instructions
            assert "not source, test or fixture patches, formatters or auto-fixes" in instructions
    for field in ("name", "description"):
        assert isinstance(config[field], str) and config[field].strip(), (path, field)
    assert isinstance(instructions, str) and instructions.strip()
    # These are instruction-presence checks, not observations of role compliance.
    assert "absolute installed" in instructions and "supplied" in instructions
    assert "SKILL.md" in instructions and "workflow.md" in instructions
    assert "not recursively delegate or restart the whole workflow" in instructions
    if role in {"model_spec_analyst", "mesa_geo_specialist"}:
        assert "Do not assume sibling skills exist or load all three workflows" in instructions
    else:
        assigned_skill, = (name for name, roles in EXPECTED_ROLES.items() if role in roles)
        assert assigned_skill in instructions


def test_public_integration_document_links_remain_inside_product():
    documents = [ROOT / "README.md", ROOT / "integrations" / "codex" / "README.md"]
    documents.extend((ROOT / "integrations").rglob("*.md"))
    for document in set(documents):
        local_links(document, ROOT)

# Phase 10 Implementation Guide: Module Framework Foundation

**Status:** Ready for Implementation
**Priority:** Critical Path
**Estimated Duration:** 4-6 weeks

---

## Overview

This document provides detailed implementation guidance for **Phase 10: Module Framework Foundation**, the critical first step in transforming Aequitas into a full-stack framework.

---

## 10.1 Module Manifest Specification

### File: `governance/canon/module_manifest_spec.md`

```markdown
# Aequitas Module Manifest Specification

## Schema Definition

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Aequitas Module Manifest",
  "type": "object",
  "required": ["name", "version", "aequitas_version"],
  "properties": {
    "name": {
      "type": "string",
      "pattern": "^[a-z][a-z0-9_]*$",
      "description": "Machine-readable module name (snake_case)"
    },
    "display_name": {
      "type": "string",
      "description": "Human-readable module name"
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "description": "Semantic version (MAJOR.MINOR.PATCH)"
    },
    "aequitas_version": {
      "type": "string",
      "description": "Minimum compatible Aequitas version (e.g., '>=2025.2')"
    },
    "description": {
      "type": "string",
      "maxLength": 500
    },
    "author": {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "organization": {"type": "string"}
      }
    },
    "depends": {
      "type": "array",
      "items": {"type": "string"},
      "description": "List of module dependencies (must be installed first)"
    },
    "conflicts": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Modules that cannot be installed alongside this one"
    },
    "data": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Files to load during installation (models, views, data)"
    },
    "canon_extensions": {
      "type": "object",
      "description": "Canon documents this module extends or depends on",
      "additionalProperties": {
        "type": "array",
        "items": {"type": "string"}
      }
    },
    "permissions": {
      "type": "object",
      "properties": {
        "roles": {
          "type": "array",
          "items": {"type": "string"}
        },
        "access_rules": {
          "type": "array",
          "items": {"type": "object"}
        }
      }
    },
    "settings": {
      "type": "object",
      "description": "Module-specific configuration options",
      "additionalProperties": true
    },
    "license": {
      "type": "string",
      "enum": ["MIT", "Apache-2.0", "GPL-3.0", "Proprietary"]
    }
  }
}
```

## Example Manifest

```json
{
  "name": "contacts",
  "display_name": "Contacts & Partners",
  "version": "1.0.0",
  "aequitas_version": ">=2025.2",
  "description": "Unified contact management for customers, vendors, and partners",
  "author": {
    "name": "Aequitas Core Team",
    "email": "core@aequitas.io"
  },
  "depends": ["core_accounting"],
  "data": [
    "models/__init__.py",
    "models/partner.py",
    "api/v1/partners.py",
    "views/partner_list.tsx",
    "views/partner_form.tsx",
    "data/demo_partners.json"
  ],
  "canon_extensions": {
    "CANON_I": ["partner_types"]
  },
  "permissions": {
    "roles": ["contacts_user", "contacts_manager"],
    "access_rules": [
      {
        "role": "contacts_user",
        "model": "res_partner",
        "permissions": ["read", "write"]
      }
    ]
  },
  "license": "MIT"
}
```
```

---

## 10.2 Module Registry Implementation

### File: `backend/app/core/module_registry.py`

```python
"""
Module Registry - Dynamic module discovery and lifecycle management
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import networkx as nx

logger = logging.getLogger(__name__)


class ModuleStatus(Enum):
    DISCOVERED = "discovered"
    INSTALLING = "installing"
    INSTALLED = "installed"
    FAILED = "failed"
    UNINSTALLED = "uninstalled"


@dataclass
class ModuleManifest:
    """Represents a parsed module manifest"""
    name: str
    version: str
    aequitas_version: str
    path: Path
    display_name: Optional[str] = None
    description: Optional[str] = None
    author: Optional[Dict] = None
    depends: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    data: List[str] = field(default_factory=list)
    canon_extensions: Dict[str, List[str]] = field(default_factory=dict)
    permissions: Dict = field(default_factory=dict)
    settings: Dict = field(default_factory=dict)
    license: Optional[str] = None
    
    # Runtime state
    status: ModuleStatus = ModuleStatus.DISCOVERED
    error_message: Optional[str] = None


class ModuleRegistry:
    """
    Central registry for Aequitas modules.
    
    Responsibilities:
    - Discover modules in configured paths
    - Parse and validate manifests
    - Resolve dependencies
    - Manage module lifecycle (install/uninstall)
    - Track installed modules
    """
    
    MANIFEST_FILENAME = "aequitas_module.json"
    
    def __init__(self, module_paths: Optional[List[str]] = None):
        self.module_paths = module_paths or []
        self.modules: Dict[str, ModuleManifest] = {}
        self.installed_modules: Set[str] = set()
        self.dependency_graph = nx.DiGraph()
        
    def add_module_path(self, path: str):
        """Add a path to search for modules"""
        module_path = Path(path)
        if not module_path.exists():
            logger.warning(f"Module path does not exist: {path}")
            return
        
        if module_path not in self.module_paths:
            self.module_paths.append(module_path)
            logger.info(f"Added module path: {path}")
    
    def discover_modules(self) -> List[str]:
        """
        Scan all configured paths for modules.
        Returns list of discovered module names.
        """
        discovered = []
        
        for path in self.module_paths:
            path = Path(path)
            if not path.exists():
                continue
            
            # Check if path itself is a module
            manifest_path = path / self.MANIFEST_FILENAME
            if manifest_path.exists():
                try:
                    module = self._parse_manifest(manifest_path)
                    self.modules[module.name] = module
                    discovered.append(module.name)
                    logger.info(f"Discovered module: {module.name} v{module.version}")
                except Exception as e:
                    logger.error(f"Failed to parse manifest at {path}: {e}")
            
            # Scan subdirectories
            elif path.is_dir():
                for subdir in path.iterdir():
                    if subdir.is_dir():
                        manifest_path = subdir / self.MANIFEST_FILENAME
                        if manifest_path.exists():
                            try:
                                module = self._parse_manifest(manifest_path)
                                self.modules[module.name] = module
                                discovered.append(module.name)
                                logger.info(f"Discovered module: {module.name} v{module.version}")
                            except Exception as e:
                                logger.error(f"Failed to parse manifest at {subdir}: {e}")
        
        logger.info(f"Discovery complete: {len(discovered)} modules found")
        return discovered
    
    def _parse_manifest(self, manifest_path: Path) -> ModuleManifest:
        """Parse and validate a module manifest file"""
        with open(manifest_path, 'r') as f:
            data = json.load(f)
        
        # Validate required fields
        required = ['name', 'version', 'aequitas_version']
        for field in required:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        return ModuleManifest(
            name=data['name'],
            version=data['version'],
            aequitas_version=data['aequitas_version'],
            path=manifest_path.parent,
            display_name=data.get('display_name'),
            description=data.get('description'),
            author=data.get('author'),
            depends=data.get('depends', []),
            conflicts=data.get('conflicts', []),
            data=data.get('data', []),
            canon_extensions=data.get('canon_extensions', {}),
            permissions=data.get('permissions', {}),
            settings=data.get('settings', {}),
            license=data.get('license')
        )
    
    def resolve_dependencies(self, module_names: List[str]) -> List[str]:
        """
        Resolve module dependencies and return installation order.
        Uses topological sort to determine correct order.
        
        Raises:
            ValueError: If circular dependencies or missing dependencies detected
        """
        # Build dependency graph
        self.dependency_graph.clear()
        
        # Add all requested modules
        for name in module_names:
            if name not in self.modules:
                raise ValueError(f"Module not found: {name}")
            self.dependency_graph.add_node(name)
        
        # Add edges for dependencies
        for name in module_names:
            module = self.modules[name]
            for dep in module.depends:
                if dep not in self.modules:
                    raise ValueError(
                        f"Module '{name}' requires '{dep}' which is not available"
                    )
                self.dependency_graph.add_edge(dep, name)
        
        # Detect cycles
        try:
            cycle = nx.find_cycle(self.dependency_graph)
            cycle_str = " → ".join(cycle[0])
            raise ValueError(f"Circular dependency detected: {cycle_str}")
        except nx.NetworkXNoCycle:
            pass
        
        # Topological sort gives installation order
        install_order = list(nx.topological_sort(self.dependency_graph))
        logger.info(f"Resolved installation order: {install_order}")
        
        return install_order
    
    def check_conflicts(self, module_names: List[str]) -> List[str]:
        """Check for module conflicts. Returns list of conflict descriptions."""
        conflicts = []
        
        for name in module_names:
            module = self.modules[name]
            for conflict in module.conflicts:
                if conflict in self.installed_modules or conflict in module_names:
                    conflicts.append(
                        f"Module '{name}' conflicts with '{conflict}'"
                    )
        
        return conflicts
    
    def install_module(self, module_name: str, db_session=None) -> bool:
        """
        Install a single module and its dependencies.
        
        Steps:
        1. Validate module exists
        2. Check Canon compatibility
        3. Load models
        4. Execute initialization data
        5. Register API routes
        6. Apply permissions
        7. Mark as installed
        """
        if module_name not in self.modules:
            raise ValueError(f"Module not found: {module_name}")
        
        module = self.modules[module_name]
        module.status = ModuleStatus.INSTALLING
        
        try:
            logger.info(f"Installing module: {module_name} v{module.version}")
            
            # Step 1: Check Canon compatibility
            self._validate_canon_compatibility(module)
            
            # Step 2: Load models
            self._load_models(module)
            
            # Step 3: Execute initialization data
            if db_session:
                self._load_init_data(module, db_session)
            
            # Step 4: Register API routes (handled by FastAPI router inclusion)
            self._register_routes(module)
            
            # Step 5: Apply permissions
            self._apply_permissions(module)
            
            # Step 6: Mark as installed
            module.status = ModuleStatus.INSTALLED
            self.installed_modules.add(module_name)
            
            logger.info(f"Module installed successfully: {module_name}")
            return True
            
        except Exception as e:
            module.status = ModuleStatus.FAILED
            module.error_message = str(e)
            logger.error(f"Failed to install module {module_name}: {e}")
            raise
    
    def uninstall_module(self, module_name: str, db_session=None):
        """
        Uninstall a module.
        Checks for dependent modules first.
        """
        if module_name not in self.installed_modules:
            raise ValueError(f"Module not installed: {module_name}")
        
        # Check if other installed modules depend on this one
        dependents = []
        for name in self.installed_modules:
            if name == module_name:
                continue
            module = self.modules.get(name)
            if module and module_name in module.depends:
                dependents.append(name)
        
        if dependents:
            raise ValueError(
                f"Cannot uninstall '{module_name}': "
                f"the following modules depend on it: {', '.join(dependents)}"
            )
        
        # Execute uninstall hooks if present
        uninstall_script = module.path / "uninstall.py"
        if uninstall_script.exists() and db_session:
            self._execute_uninstall(module, db_session)
        
        # Remove from installed set
        self.installed_modules.remove(module_name)
        module.status = ModuleStatus.UNINSTALLED
        
        logger.info(f"Module uninstalled: {module_name}")
    
    def _validate_canon_compatibility(self, module: ModuleManifest):
        """Validate that module is compatible with current Canon version"""
        # TODO: Implement Canon version checking
        # For now, just log
        if module.canon_extensions:
            logger.info(
                f"Module {module.name} extends Canon: "
                f"{list(module.canon_extensions.keys())}"
            )
    
    def _load_models(self, module: ModuleManifest):
        """Load Python models from module"""
        models_init = module.path / "models" / "__init__.py"
        if models_init.exists():
            # Import models module
            import sys
            import importlib.util
            
            spec = importlib.util.spec_from_file_location(
                f"module_{module.name}_models",
                models_init
            )
            models_module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = models_module
            spec.loader.exec_module(models_module)
            
            logger.info(f"Loaded models for module: {module.name}")
    
    def _load_init_data(self, module: ModuleManifest, db_session):
        """Load initialization data (demo data, configurations)"""
        data_dir = module.path / "data"
        if not data_dir.exists():
            return
        
        for data_file in module.data:
            if data_file.startswith("data/"):
                file_path = module.path / data_file
                if file_path.exists():
                    self._load_data_file(file_path, db_session)
    
    def _load_data_file(self, file_path: Path, db_session):
        """Load a single data file (JSON format)"""
        import json
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Process data based on model type
        # This is a simplified example - real implementation needs more logic
        for record in data:
            model_name = record.get('_model')
            if not model_name:
                continue
            
            # Get model class and create record
            # TODO: Implement proper model instantiation
            logger.debug(f"Loading {model_name} record: {record.get('name', 'unnamed')}")
    
    def _register_routes(self, module: ModuleManifest):
        """Register API routes from module"""
        # Routes are typically registered via FastAPI include_router
        # This method can handle dynamic route registration if needed
        api_dir = module.path / "api"
        if api_dir.exists():
            logger.info(f"API routes available for module: {module.name}")
    
    def _apply_permissions(self, module: ModuleManifest):
        """Apply module permissions and roles"""
        if not module.permissions:
            return
        
        # TODO: Integrate with permission service
        logger.info(f"Applying permissions for module: {module.name}")
    
    def _execute_uninstall(self, module: ModuleManifest, db_session):
        """Execute module uninstall script"""
        import sys
        import importlib.util
        
        uninstall_path = module.path / "uninstall.py"
        spec = importlib.util.spec_from_file_location(
            f"module_{module.name}_uninstall",
            uninstall_path
        )
        uninstall_module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = uninstall_module
        spec.loader.exec_module(uninstall_module)
        
        # Call uninstall function if it exists
        if hasattr(uninstall_module, 'uninstall'):
            uninstall_module.uninstall(db_session)
    
    def get_installed_modules(self) -> List[str]:
        """Return list of installed module names"""
        return list(self.installed_modules)
    
    def get_module_info(self, module_name: str) -> Optional[ModuleManifest]:
        """Get information about a specific module"""
        return self.modules.get(module_name)
    
    def is_module_installed(self, module_name: str) -> bool:
        """Check if a module is installed"""
        return module_name in self.installed_modules


# Global registry instance
_registry: Optional[ModuleRegistry] = None


def get_module_registry() -> ModuleRegistry:
    """Get or create the global module registry"""
    global _registry
    if _registry is None:
        _registry = ModuleRegistry()
    return _registry


def initialize_module_registry(module_paths: List[str]):
    """Initialize the global module registry with paths"""
    global _registry
    _registry = ModuleRegistry(module_paths)
    _registry.discover_modules()
```

---

## 10.3 CLI Commands for Module Management

### File: `backend/cli/module_commands.py`

```python
"""
CLI commands for module management
"""

import click
import json
from pathlib import Path
from app.core.module_registry import get_module_registry, initialize_module_registry
from app.db.session import SessionLocal


@click.group()
def modules():
    """Module management commands"""
    pass


@modules.command()
@click.option('--path', '-p', multiple=True, help='Module search paths')
def discover(path):
    """Discover available modules"""
    registry = get_module_registry()
    
    for p in path:
        registry.add_module_path(p)
    
    discovered = registry.discover_modules()
    
    click.echo(f"\nDiscovered {len(discovered)} modules:\n")
    for name in discovered:
        module = registry.get_module_info(name)
        click.echo(f"  • {module.display_name or module.name} v{module.version}")
        if module.description:
            click.echo(f"    {module.description}")
        click.echo()


@modules.command()
@click.argument('module_name')
@click.option('--path', '-p', multiple=True, help='Module search paths')
def info(module_name, path):
    """Show detailed information about a module"""
    registry = get_module_registry()
    
    for p in path:
        registry.add_module_path(p)
    
    registry.discover_modules()
    
    module = registry.get_module_info(module_name)
    if not module:
        click.echo(f"Module not found: {module_name}", err=True)
        return
    
    click.echo(f"\nModule: {module.display_name or module.name}")
    click.echo(f"Version: {module.version}")
    click.echo(f"Path: {module.path}")
    
    if module.author:
        click.echo(f"Author: {module.author.get('name', 'Unknown')}")
    
    if module.description:
        click.echo(f"\nDescription:")
        click.echo(f"  {module.description}")
    
    if module.depends:
        click.echo(f"\nDependencies:")
        for dep in module.depends:
            click.echo(f"  • {dep}")
    
    if module.canon_extensions:
        click.echo(f"\nCanon Extensions:")
        for doc, sections in module.canon_extensions.items():
            click.echo(f"  • {doc}: {', '.join(sections)}")
    
    click.echo()


@modules.command()
@click.argument('module_name')
@click.option('--path', '-p', multiple=True, help='Module search paths')
def install(module_name, path):
    """Install a module"""
    registry = get_module_registry()
    
    for p in path:
        registry.add_module_path(p)
    
    registry.discover_modules()
    
    if module_name not in registry.modules:
        click.echo(f"Module not found: {module_name}", err=True)
        return
    
    try:
        # Resolve dependencies
        install_order = registry.resolve_dependencies([module_name])
        
        # Check conflicts
        conflicts = registry.check_conflicts(install_order)
        if conflicts:
            click.echo("Conflicts detected:", err=True)
            for conflict in conflicts:
                click.echo(f"  ✗ {conflict}", err=True)
            return
        
        click.echo(f"\nInstalling {len(install_order)} module(s):\n")
        
        db = SessionLocal()
        try:
            for name in install_order:
                if registry.is_module_installed(name):
                    click.echo(f"  ✓ {name} (already installed)")
                    continue
                
                click.echo(f"  Installing {name}... ", nl=False)
                registry.install_module(name, db)
                click.echo("✓ Done")
            
            db.commit()
            click.echo("\n✅ Installation complete!\n")
        except Exception as e:
            db.rollback()
            click.echo(f"\n❌ Installation failed: {e}\n", err=True)
            raise
        finally:
            db.close()
            
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)


@modules.command()
@click.argument('module_name')
def uninstall(module_name):
    """Uninstall a module"""
    registry = get_module_registry()
    registry.discover_modules()
    
    if not registry.is_module_installed(module_name):
        click.echo(f"Module not installed: {module_name}", err=True)
        return
    
    try:
        db = SessionLocal()
        try:
            click.echo(f"\nUninstalling {module_name}...")
            registry.uninstall_module(module_name, db)
            db.commit()
            click.echo("✅ Module uninstalled successfully\n")
        except Exception as e:
            db.rollback()
            click.echo(f"❌ Uninstall failed: {e}\n", err=True)
            raise
        finally:
            db.close()
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)


@modules.command()
def list():
    """List installed modules"""
    registry = get_module_registry()
    registry.discover_modules()
    
    installed = registry.get_installed_modules()
    
    if not installed:
        click.echo("\nNo modules installed.\n")
        return
    
    click.echo(f"\nInstalled modules ({len(installed)}):\n")
    for name in sorted(installed):
        module = registry.get_module_info(name)
        click.echo(f"  ✓ {module.display_name or module.name} v{module.version}")
    click.echo()


@modules.command()
@click.argument('module_name')
def test(module_name):
    """Run module tests"""
    registry = get_module_registry()
    registry.discover_modules()
    
    module = registry.get_module_info(module_name)
    if not module:
        click.echo(f"Module not found: {module_name}", err=True)
        return
    
    test_dir = module.path / "tests"
    if not test_dir.exists():
        click.echo(f"No tests found for module: {module_name}")
        return
    
    # Run pytest on module tests
    import subprocess
    result = subprocess.run(
        ["pytest", str(test_dir), "-v"],
        capture_output=True,
        text=True
    )
    
    click.echo(result.stdout)
    if result.stderr:
        click.echo(result.stderr, err=True)
    
    exit(result.returncode)


@modules.command()
@click.argument('name')
@click.option('--display-name', '-d', help='Display name')
@click.option('--description', help='Module description')
@click.option('--author', '-a', help='Author name')
@click.option('--path', '-p', default="./modules", help='Output directory')
def create(name, display_name, description, author, path):
    """Create a new module scaffold"""
    import shutil
    
    output_dir = Path(path) / name
    if output_dir.exists():
        click.echo(f"Directory already exists: {output_dir}", err=True)
        return
    
    # Create directory structure
    dirs = [
        output_dir,
        output_dir / "models",
        output_dir / "api" / "v1",
        output_dir / "views",
        output_dir / "reports",
        output_dir / "data",
        output_dir / "tests",
    ]
    
    for d in dirs:
        d.mkdir(parents=True)
        click.echo(f"Created: {d}")
    
    # Create manifest
    manifest = {
        "name": name,
        "display_name": display_name or name.replace("_", " ").title(),
        "version": "1.0.0",
        "aequitas_version": ">=2025.2",
        "description": description or f"Module {name}",
        "author": {"name": author or "Unknown"},
        "depends": ["core_accounting"],
        "data": [],
        "license": "MIT"
    }
    
    manifest_path = output_dir / "aequitas_module.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    click.echo(f"Created: {manifest_path}")
    
    # Create __init__.py files
    (output_dir / "models" / "__init__.py").touch()
    (output_dir / "tests" / "__init__.py").touch()
    click.echo("Created: __init__.py files")
    
    # Create example model
    model_template = f'''"""
Models for {name} module
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from app.db.base import Base


class ExampleModel(Base):
    __tablename__ = "{name}_example"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
'''
    model_path = output_dir / "models" / "example.py"
    with open(model_path, 'w') as f:
        f.write(model_template)
    click.echo(f"Created: {model_path}")
    
    click.echo(f"\n✅ Module scaffold created at: {output_dir}\n")
    click.echo("Next steps:")
    click.echo(f"  1. Edit {manifest_path}")
    click.echo(f"  2. Add your models to models/")
    click.echo(f"  3. Add API routes to api/v1/")
    click.echo(f"  4. Test with: aequitas modules test {name}\n")
```

---

## 10.4 Contacts Module (Proof of Concept)

### Directory Structure
```
modules/contacts/
├── aequitas_module.json
├── models/
│   ├── __init__.py
│   └── partner.py
├── api/
│   └── v1/
│       └── partners.py
├── views/
│   ├── partner_list.tsx
│   └── partner_form.tsx
├── data/
│   └── demo_partners.json
└── tests/
    └── test_partners.py
```

### Complete implementation files provided in separate attachments.

---

## Testing Strategy

### Unit Tests
- Module manifest parsing
- Dependency resolution
- Conflict detection
- Model loading

### Integration Tests
- Module installation/uninstallation
- Database migrations
- API route registration

### End-to-End Tests
- Full module lifecycle
- Multi-module dependencies
- Canon compliance validation

---

## Success Criteria

✅ Module registry discovers and loads modules
✅ Dependencies resolved correctly (topological sort)
✅ Conflicts detected before installation
✅ Models loaded without errors
✅ API routes accessible after installation
✅ Data loaded during installation
✅ Uninstallation removes module cleanly
✅ CLI commands functional

---

*Ready for implementation. Begin with Week 1-2 tasks.*

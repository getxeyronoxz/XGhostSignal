"""Plugin Registry for XGhostSignal"""
import os
import importlib
from typing import Dict, Any, List

class PluginRegistry:
    def __init__(self):
        self.plugins: Dict[str, Any] = {}

    def load_plugins(self, plugin_dir: str, package: str = None):
        """Dynamically load python files as plugins from the given directory.

        Args:
            plugin_dir: Directory containing plugin files
            package: Python package path (if None, auto-detects from plugin_dir)
        """
        if not os.path.exists(plugin_dir):
            return

            # Auto-detect package path if not provided
        if package is None:
            base_dir = os.path.basename(plugin_dir.rstrip(os.sep))
            package = f"plugins.{base_dir}"

        for filename in os.listdir(plugin_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = filename[:-3]
                try:
                    # Dynamically load the module
                    full_module_path = f"{package}.{module_name}"
                    module = importlib.import_module(full_module_path)
                    if hasattr(module, "PLUGIN_NAME") and hasattr(module, "run"):
                        self.plugins[module.PLUGIN_NAME] = module
                        print(f"[+] Loaded plugin: {module.PLUGIN_NAME}")
                except Exception as e:
                    print(f"[-] Failed to load plugin {module_name}: {e}")

    def get_active_plugins(self) -> List[str]:
        return list(self.plugins.keys())

    def run_plugin(self, name: str, **kwargs):
        if name in self.plugins:
            return self.plugins[name].run(**kwargs)
        raise ValueError(f"Plugin {name} not found.")

registry = PluginRegistry()

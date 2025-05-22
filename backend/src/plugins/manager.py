from typing import Dict, List, Type
import importlib
import inspect
from pathlib import Path
from .models import Plugin, PluginConfig, PluginEvent
from .hooks import PluginHook

class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, Plugin] = {}
        self.hooks: Dict[str, List[PluginHook]] = {}
        self.plugin_dir = Path("plugins")
        
    async def load_plugins(self) -> None:
        """Tüm pluginleri yükler."""
        for plugin_path in self.plugin_dir.glob("*.py"):
            try:
                # Import plugin module
                module = importlib.import_module(
                    f"plugins.{plugin_path.stem}"
                )
                
                # Find plugin class
                plugin_class = self._find_plugin_class(module)
                if not plugin_class:
                    continue
                    
                # Initialize plugin
                plugin = plugin_class()
                await self._register_plugin(plugin)
                
            except Exception as e:
                self.logger.error(
                    f"Failed to load plugin {plugin_path}: {str(e)}"
                )
                
    async def _register_plugin(self, plugin: Plugin) -> None:
        """Plugin'i kaydeder."""
        # Validate plugin
        if not self._validate_plugin(plugin):
            raise InvalidPluginError(
                f"Invalid plugin: {plugin.name}"
            )
            
        # Register hooks
        for hook in plugin.hooks:
            if hook.event not in self.hooks:
                self.hooks[hook.event] = []
            self.hooks[hook.event].append(hook)
            
        # Store plugin
        self.plugins[plugin.name] = plugin
        
        # Initialize plugin
        await plugin.initialize()
        
    async def trigger_event(self, event: PluginEvent,
                          context: Dict) -> None:
        """Event trigger eder."""
        if event.name not in self.hooks:
            return
            
        for hook in self.hooks[event.name]:
            try:
                await hook.execute(context)
            except Exception as e:
                self.logger.error(
                    f"Hook execution failed: {str(e)}"
                )
                
    def _validate_plugin(self, plugin: Plugin) -> bool:
        """Plugin validasyonu yapar."""
        required_attrs = ['name', 'version', 'hooks']
        return all(hasattr(plugin, attr) for attr in required_attrs)

class CustomQueryPlugin(Plugin):
    """Örnek custom query plugin."""
    
    def __init__(self):
        self.name = "custom_query_plugin"
        self.version = "1.0.0"
        self.hooks = [
            PluginHook(
                event="before_query_execute",
                callback=self.on_before_query
            ),
            PluginHook(
                event="after_query_execute",
                callback=self.on_after_query
            )
        ]
        
    async def initialize(self) -> None:
        """Plugin initialization."""
        # Custom initialization logic
        pass
        
    async def on_before_query(self, context: Dict) -> None:
        """Query execution öncesi hook."""
        query = context['query']
        # Custom query modification logic
        
    async def on_after_query(self, context: Dict) -> None:
        """Query execution sonrası hook."""
        result = context['result']
        # Custom result processing logic
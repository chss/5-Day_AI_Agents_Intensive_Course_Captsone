from toolbox_core import ToolboxSyncClient
import sys

try:
    toolbox = ToolboxSyncClient("http://127.0.0.1:5001")
    toolset = toolbox.load_toolset("my-toolset")
    print("Successfully loaded toolset 'my-toolset'")
    print(f"Tools: {toolset}")
except Exception as e:
    print(f"Failed to load toolset: {e}")
    sys.exit(1)

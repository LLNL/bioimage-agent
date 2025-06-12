from napari._app_model import get_app_model

app_model_cmds = get_app_model().commands           # CommandsRegistry

print(app_model_cmds)
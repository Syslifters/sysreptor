from sysreptor.plugins import PluginConfig


class ExcalidrawPluginConfig(PluginConfig):
    plugin_id = 'c50b19ff-db68-4a83-9508-80ff6b6d2498'


# TODO: Excalidraw collaborative editing:
# * [x] model
#   * [x] ProjectExcalidrawData: project, data
#   * [x] 1:1 relationship with project
# * [x] migrations
# * [x] collab backend
#   * [x] authentication
#   * [x] permissions
#   * [x] broadcast events
#   * [x] save to database
#   * [x] init: load elements from database
# * [x] collab frontend
#   * [x] sync elements
#   * [x] send data as JSON
#   * [x] insert elements
#   * [x] move elements
#   * [x] delete elements
#   * [x] text does not sync: no message sent => font error?
#   * [x] no assets/files
#   * [x] no awareness/presence/cursor
#   * [x] no user follow
# * [ ] frontend UI
#   * [x] plugin.js
#   * [x] per-project iframe
#   * [x] light-dark mode
#   * [x] disable assets/files in UI
#   * [x] loading animation
#   * [x] on disconnect: set readonly
#   * [x] disable external libraries
#   * [x] failed to load font
#   * [ ] error handling: show error message on initial load
#     * [x] log exceptions
#     * [x] connection error: show error message on initial load
#     * [x] connection loss: readonly
#     * [ ] connection loss: show error message: ErrorDialog + retry button
#   * [ ] reconnect on disconnect, max 3 times?
#       * [ ] show error message on reconnect failure
# * [x] libraries
#   * [x] save libraries in indexdb
#   * [x] support "Add to Excalidraw" button => link with hash
# * [ ] export/import
#   * [ ] export plugin data with project
# * [ ] tests
#   * [x] collab event broadcasting
#   * [x] collab init: load from DB
#   * [x] save to db
#   * [ ] import/export
# * [x] build
#   * [x] test frontend built in dockerfile
# * [ ] docs
#   * [ ] README
#   * [ ] plugin table
#   * [ ] changelog


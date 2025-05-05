from UviCornServer import UvicornServer
from server import app
from time import sleep
from webview import create_window
import webview

webview.settings["OPEN_DEVTOOLS_IN_DEBUG"] = False

server = UvicornServer(app)
server.start()

window = create_window("Google", "./index.html")
webview.start(debug=True)

server.stop()

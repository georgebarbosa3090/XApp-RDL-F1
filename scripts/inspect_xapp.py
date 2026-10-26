import ricxappframe.xapp_frame as x
import inspect

import ricxappframe.xapp_frame as x

x._BaseXapp.registerXapp = lambda self: None

app = x.RMRXapp(default_handler=lambda s, m, b: None, rmr_port=4560, rmr_wait_for_ready=False, use_fake_sdl=True)
print("Instantiated successfully without starting register thread!")
app.stop()




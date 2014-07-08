import sys
sys.path.insert(0, '..')


import pygame
from pygame.locals import *
from pgu import gui
from pgu import html


def handle_file_browser_closed(dlg):
    if dlg.value: input_file.value = dlg.value


#gui.theme.load('../data/themes/default')
app = gui.Desktop()
app.connect(gui.QUIT,app.quit,None)

main = gui.Container(width=710, height=400) #, background=(220, 220, 220) )


main.add(gui.Label("Console", cls="h1"), 10, 10)
main.add(gui.Label("Chat", cls="h1"), 380, 10)


console_output = """
<div style='width: 300px; height: 300px; padding: 8px; border: 1px; border-color: #000000; background: #eeffff;'></div>"""

console_input = """
<input type='text' style='width: 300px'/>"""

chat_output = """
<div style='width: 300px; height: 300px; padding: 8px; border: 1px; border-color: #000000; background: #eeffff;'></div>"""

chat_input = """
<input type='text' style='width: 300px'/>"""

cons_out = html.HTML(console_output)
cons_in = html.HTML(console_input)
chat_out = html.HTML(chat_output)
chat_in = html.HTML(chat_input)

td_style = {'padding_right': 10}
t = gui.Table()
t.tr()
input_file = gui.Input()


main.add(cons_out, 10, 40)
main.add(cons_in, 10, 370)
main.add(chat_out, 380, 40)
main.add(chat_in, 380, 370)

app.run(main)
#import profile
#profile.run('app.run(main)')

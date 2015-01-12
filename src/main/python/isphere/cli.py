from isphere.command import VSphereREPL


def main(*args):
    repl = VSphereREPL()
    repl.cmdloop()

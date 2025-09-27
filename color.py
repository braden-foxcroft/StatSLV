

class Color:
    doColor = True
    def setColor(this,yesNo):
        Color.doColor = yesNo
    
    def __init__(this,code):
        if not isinstance(code,int): raise Exception(f"Color(int) got \"{code}\" instead!")
        this.code = str(code)
    
    def __call__(this,toConv):
        if not Color.doColor: return str(toConv)
        return f"\033[{this.code}m" + str(toConv) + "\033[0m"


red = Color(31)
green = Color(32)
orange = Color(33)
blue = Color(34)
magenta = Color(35)
cyan = Color(36)
yellow = orange

lightgreen = Color(92)
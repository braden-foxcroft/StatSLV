

class Color:
    doColor = True
    def setColor(this,yesNo):
        Color.doColor = yesNo
    
    def __init__(this,code):
        if not isinstance(code,str): raise Exception(f"Color(str) got \"{code}\" instead!")
        this.code = str(code)
    
    def __call__(this,toConv):
        if not Color.doColor: return str(toConv)
        return f"\033[{this.code}m" + str(toConv) + "\033[0m"


red = Color("1;31")
green = Color("1;32")
orange = Color("1;33")
blue = Color("1;34")
magenta = Color("1;35")
cyan = Color("36")
yellow = orange

lightgreen = Color("1;92")
lightblue = Color("1;94")

col_keyword = cyan
col_comment = lightgreen
col_str = orange
col_int = blue

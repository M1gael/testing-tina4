# testing chapter 6 orm autocrud
from tina4_python.crud import AutoCrud

AutoCrud.discover("src/orm", prefix="/crud")

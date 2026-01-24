from typing import Annotated
from langchain_core.tools import StructuredTool
def add(a: int, b: int) -> int:
    return a + b

StructuredTool.from_function(func=add, )

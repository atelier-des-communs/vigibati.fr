
import sys
import traceback


for i in range(0, 4) :
    with NoFail(i) :
        raise Exception()

import sys

def read_file():
    print(sys.path)
    print("read file!")
    with open("read.txt","r") as f:
        print(f.read())


read_file()
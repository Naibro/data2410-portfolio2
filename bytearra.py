with open('picture.jpg', 'rb') as file:
    img = file.read()
# Turns the data into a list of elements with length 1460
img = "e"*422
def a(bytez):
    return (bytez[i:1460 + i] for i in range(0, len(bytez), 1460))

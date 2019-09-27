import IPython


class RGBFrameBuffer:
    def __init__(self, x=10, y=10, spec='', *args, **kwargs):
        self.x = x
        self.y = y

        self.clear()

    def clear(self):
        self.data = bytearray([0, 0, 0] * self.x * self.y)

    def get(self, x, y):
        i1 = (x + (y * self.x)) * 3
        i2 = i1 + 3

        return self.data[i1:i2]

    def set(self, x, y, r=0, g=0, b=0):
        i1 = (x + (y * self.x)) * 3
        i2 = i1 + 3

        self.data[i1:i2] = [r, g, b]

    def show(self):
        for y in range(self.y):
            for x in range(self.x):
                r, g, b = self.get(x, y)

                if r or g or b:
                    print(chr(9608)*2, end='')

                else:
                    print('. ', end='')

            print()


b = RGBFrameBuffer()

IPython.embed()

class NonPositiveError(Exception):
    pass

class PositiveList(list):
    def end(self, x):
        if x > 0:
            self.append(x)
        else:
            raise NonPositiveError()

if __name__ == "__main__":
    a = PositiveList()
    a.end(1)
    print(a)
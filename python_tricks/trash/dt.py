import datetime

def foo(y, m, d, n):
    date = datetime.date(y, m, d)
    return datetime.timedelta(n) + date

if __name__ == "__main__":
    y, m, d = map(int, input().split())
    n_d = int(input())
    a = foo(y, m, d, n_d)
    print(a.year, a.month, a.day)
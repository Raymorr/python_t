
import argparse

def runstrat():
    args = parse_args()
    print(args.d)


def parse_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Check Memory Savings')

    parser.add_argument('--d', required=False,
                        default='../../datas/yhoo-1996-2015.txt',
                        help='Data to be read in')

    parser.add_argument('--save', required=False, type=int, default=0,
                        help=('Memory saving level [1, 0, -1, -2]'))

    parser.add_argument('--datalines', required=False, action='store_true',
                        help=('Print data lines'))

    parser.add_argument('--lendetails', required=False, action='store_true',
                        help=('Print individual items memory usage'))

    parser.add_argument('--plot', required=False, action='store_true',
                        help=('Plot the result'))

    return parser.parse_args()


if __name__ == '__main__':
    runstrat()
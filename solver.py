"""Logical Sudoku solver, which does not use brute force methods.
As a consequence, not all sudokus can be solved. May still be possible
logical deductions that aren't *yet* implemented...

Usage:
python3 solver.py <input_file>

TODO:
- Improve logic
- Degeneralise: allow non 9x9 grids
- Jigsawdoku?
"""
import argparse


class GridReader(object):
    """Class for reading input files. """
    def read_file(self, fname):
        with open(fname) as infile:
            lines = infile.readlines()
        formatted_grid = []
        for lineidx, line in enumerate(lines):
            _line = line.split()
            formatted_line = []
            for tokenidx, token in enumerate(_line):
                formatted_line.append(SudokuCell(token, lineidx, tokenidx))
            formatted_grid.append(formatted_line)
        return formatted_grid


class SudokuCell(object):
    """Single cell of a Sudoku grid. """
    def get_cell_values(self):
        return set(range(1, 10))

    def add_grouping(self, grouping):
        self.groupings.append(grouping)

    def set_value(self, value):
        self.value = value
        self.value_known = True
        self.possible_values = set()
        for grouping in self.groupings:
            grouping.remove_missing_value(value)

    def __init__(self, token, yidx, xidx):
        self.groupings = []
        self.x = xidx
        self.y = yidx
        try:
            self.set_value(int(token))
        except ValueError:
            self.value = None
            self.value_known = False
            self.possible_values = self.get_cell_values()

    def remove_possibility(self, value):
        if not self.value_known:
            if len(self.possible_values) == 1:
                val, = self.possible_values
                self.set_value(val)
        try:
            self.possible_values.remove(value)
        except KeyError:
            pass
        if len(self.possible_values) == 1:
            val, = self.possible_values
            self.set_value(val)

    def __repr__(self):
        if self.value_known:
            return str(self.value)
        else:
            return " "


class CellGrouping(object):
    """Groupings of Sudoku cells, i.e. rows, columns or boxes. May be better
    as a class from which rows, cols inherit."""
    def __init__(self, cell_list, gtype=None, grid=None):
        self.type = gtype
        self.grid = grid
        self.cells = cell_list
        for cell in self.cells:
            cell.add_grouping(self)
        self.missing_values = cell_list[0].get_cell_values()
        for cell in self.cells:
            if cell.value_known:
                self.remove_missing_value(cell.value)

    def remove_missing_value(self, value):
        try:
            self.missing_values.remove(value)
        except KeyError:
            pass

    def check_for_singles(self):
        miss_vals = [i for i in self.missing_values]  # copy set
        for val in miss_vals:
            possibilities = []
            for cell in self.cells:
                if val in cell.possible_values:
                    possibilities.append(cell)
            if len(possibilities) == 1:
                possibilities[0].set_value(val)
            elif len(possibilities) <= 3:
                # if grouping is square
                # if possibilities <= 3:
                # if all have same row/ column
                # remove from possibilities for the rest of same row/column
                if self.type == "square":
                    rows = set(possibility.x for possibility in possibilities)
                    cols = set(possibility.y for possibility in possibilities)
                    possibilities_xy = [(possibility.x, possibility.y)
                                        for possibility in possibilities]
                    if len(rows) == 1:
                        rowid, = rows
                        for cell in self.grid.allcells:
                            if cell.x == rowid:
                                if (cell.x, cell.y) not in possibilities_xy:
                                    cell.remove_possibility(val)
                    if len(cols) == 1:
                        colid, = cols
                        for cell in self.grid.allcells:
                            if cell.y == colid:
                                if (cell.x, cell.y) not in possibilities_xy:
                                    cell.remove_possibility(val)


class SudokuGrid(object):
    """All Sudoku cells and their groupings which constitute the puzzle."""
    def gen_cellhash(self):
        return "".join(str(cell.value) for cell in self.allcells)

    def __init__(self, infile):
        reader = GridReader()
        self._initial_positions = reader.read_file(infile)
        self.allcells = [item for sublist in self._initial_positions
                         for item in sublist]
        self.groupings = []
        self.cellhash = self.gen_cellhash()

        # rows
        for row in self._initial_positions:
            self.groupings.append(CellGrouping(row, gtype="row", grid=self))

        # cols
        self.xdim = len(self._initial_positions[0])
        self.ydim = len(self._initial_positions)
        for i in range(self.xdim):
            _tmp = []
            for j in range(self.ydim):
                _tmp.append(self._initial_positions[j][i])
            self.groupings.append(CellGrouping(_tmp, gtype="col", grid=self))

        # squares [could probably be optimised/generalised]
        for i in range(3):
            for j in range(3):
                _tmp = []
                for cell in self.allcells:
                    if cell.x//3 == i and cell.y//3 == j:
                        _tmp.append(cell)
                self.groupings.append(CellGrouping(_tmp, gtype="square",
                                                   grid=self))

        self.positions = self._initial_positions

    def solve(self):
        counter = 2
        while True:
            for grouping in self.groupings:
                for cell in grouping.cells:
                    if cell.value_known:
                        for _cell in grouping.cells:
                            if not _cell.value_known:
                                _cell.remove_possibility(cell.value)
            for grouping in self.groupings:
                grouping.check_for_singles()
            # do solve
            newhash = self.gen_cellhash()
            if newhash == self.cellhash:
                counter -= 1
                if counter == 0:
                    break
            else:
                self.cellhash = newhash
                counter = 2
        if not all(cell.value_known for cell in self.allcells):
            print("solve incomplete")  # Go recursive brute force
        else:
            return

    def print_self(self):
        delim = "#"*37
        print(delim)
        for idx, i in enumerate(self.positions):
            if idx % 3 == 0 and idx > 0:
                print(delim)
            retstr = "#"
            for bitidx, bit in enumerate(i):
                if (bitidx+1) % 3 == 0:
                    retstr += " {0} #".format(bit)
                else:
                    retstr += " {0} |".format(bit)
            print(retstr)
        print(delim)


def read_input_args():
    """ Argument parsing object, purely for reading input file."""
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file",
                        help="Input unsolved Sudoku",
                        default="input.txt",
                        type=str)
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = read_input_args()
    sudoku = SudokuGrid(args.input_file)
    print()
    sudoku.solve()
    sudoku.print_self()

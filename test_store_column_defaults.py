"""Only the column-reset behaviour not covered by the retained defaults check."""
import unittest
from types import SimpleNamespace
from media_sorter import FilePane, details_column_order

class FakeTree:
    def __init__(self):
        self.columns=('name','codec','resolution','duration','size')
        self.order=('size','name','duration','codec','resolution')
        self.widths={c:80 for c in self.columns}
    def __getitem__(self,key):return self.columns if key=='columns' else self.order
    def configure(self,**kw):self.order=tuple(kw['displaycolumns'])
    def column(self,c,**kw):self.widths[c]=kw['width']

class ColumnResetTests(unittest.TestCase):
    def test_explicit_reset_restores_order_and_widths(self):
        tree=FakeTree()
        pane=SimpleNamespace(tree=tree,fitted_column_width=lambda c:140,refresh_view=lambda:None)
        FilePane.reset_column_layout(pane)
        self.assertEqual(tree.order[:3],('name','resolution','duration'))
        self.assertTrue(all(w==140 for w in tree.widths.values()))
    def test_malformed_entries_and_missing_preferences_are_repaired(self):
        columns=('name','codec','resolution','duration','size')
        for value in (None,[],{},'name',[{},'size','size','missing']):
            order=details_column_order(columns,value)
            self.assertEqual(set(order),set(columns));self.assertEqual(len(order),len(columns))
        self.assertEqual(details_column_order(columns,['size','name'])[:2],['size','name'])

if __name__=='__main__':unittest.main()

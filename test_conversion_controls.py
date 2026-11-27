import unittest
from media_sorter import details_column_order

class ColumnOrderTests(unittest.TestCase):
 def test_defaults_migrate_but_custom_order_is_preserved(self):
  columns=('name','codec','resolution','duration','size','fps')
  expected=['name','resolution','duration','codec','size','fps']
  self.assertEqual(details_column_order(columns),expected)
  self.assertEqual(details_column_order(columns,list(columns)),expected)
  self.assertEqual(details_column_order(columns,['name','size','codec','resolution','duration','fps']),['name','size','codec','resolution','duration','fps'])

if __name__=='__main__':unittest.main()

import tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from media_sorter import MediaSorterApp

class SimilarReviewTests(unittest.TestCase):
    def setup_case(self):
        items=[SimpleNamespace(path=Path(f'/photos/{n}.jpg'),size=size,modified=modified) for n,size,modified in [('a',100,30),('b',300,10),('c',200,20)]]
        tree=Mock();tree.get_children.return_value=['a','b','c','unrelated']
        tree.item.side_effect=lambda iid,field: (str(Path('/photos')/(iid+'.jpg')),)
        pane=SimpleNamespace(tree=tree,update_thumbnail_selection=Mock(),clear_checks=Mock(),status_var=Mock())
        app=SimpleNamespace(tr=lambda key,**kw:key.split('.')[-1]); window=Mock()
        return app,pane,items,window

    def test_all_five_rules_select_alternatives_only(self):
        for strategy,keeper in [('first','a'),('newest','a'),('oldest','b'),('smallest','a'),('largest','b')]:
            with self.subTest(strategy=strategy):
                app,pane,items,window=self.setup_case()
                with patch('media_sorter.messagebox.askyesno',return_value=True),patch('media_sorter.messagebox.showinfo'):
                    MediaSorterApp.apply_duplicate_strategy(app,pane,[items],strategy,window,visually_similar=True)
                self.assertEqual(set(pane.tree.selection_set.call_args.args[0]),{'a','b','c'}-{keeper})
                pane.update_thumbnail_selection.assert_called_once();pane.clear_checks.assert_called_once();window.destroy.assert_called_once()

    def test_refusing_warning_preserves_existing_selection_and_review(self):
        app,pane,items,window=self.setup_case()
        with patch('media_sorter.messagebox.askyesno',return_value=False):
            MediaSorterApp.apply_duplicate_strategy(app,pane,[items],'largest',window,visually_similar=True)
        pane.tree.selection_set.assert_not_called();pane.clear_checks.assert_not_called();window.destroy.assert_not_called()

    def test_filtered_items_not_selected(self):
        app,pane,items,window=self.setup_case();pane.tree.get_children.return_value=['b']
        with patch('media_sorter.messagebox.askyesno',return_value=True),patch('media_sorter.messagebox.showinfo'):
            MediaSorterApp.apply_duplicate_strategy(app,pane,[items],'newest',window,visually_similar=True)
        pane.tree.selection_set.assert_called_once_with(['b'])

    def test_exact_duplicates_keep_existing_confirmation_behaviour(self):
        app,pane,items,window=self.setup_case()
        with patch('media_sorter.messagebox.askyesno') as question,patch('media_sorter.messagebox.showinfo'):
            MediaSorterApp.apply_duplicate_strategy(app,pane,[items],'oldest',window)
        question.assert_not_called()

    def test_similar_results_reuse_review_and_retain_hash_differences(self):
        app=SimpleNamespace(show_duplicate_review=Mock());pane=Mock()
        a=SimpleNamespace(path=Path('a.jpg'));b=SimpleNamespace(path=Path('b.jpg'))
        MediaSorterApp.show_similar_image_results(app,pane,[[(a,0),(b,3)]],6,2,0)
        args=app.show_duplicate_review.call_args
        self.assertEqual(args.args,(pane,[[a,b]]))
        self.assertEqual(args.kwargs['similar_details'][1],{'a.jpg':0,'b.jpg':2})

if __name__=='__main__':unittest.main()

import unittest
from rtl_display import display_text, mapped_ranges, needs_visual_order, ordered, render_document

class RtlDisplayTests(unittest.TestCase):
    def test_windows_keeps_logical_text_and_linux_shapes_once(self):
        text="المجموعات الذكية H.264 123"
        self.assertEqual(display_text(text,"ar","win32"),text)
        visual=display_text(text,"ar","linux")
        self.assertNotEqual(visual,text)
        self.assertIn("H.264 123",visual)
        self.assertEqual(display_text(visual,"ar","linux"),visual)

    def test_wrapping_and_mapping_preserve_exact_logical_match_across_lines(self):
        logical="المجموعات الذكية تستخدم الملفات الأصلية smart_collections.json\nשלום עולם 123"
        text,lines=render_document(logical,18,len)
        self.assertGreater(len(lines),2)
        indices=[i for line in lines for i in line.logical_indices]
        self.assertEqual(sorted(indices),[i for i,c in enumerate(logical) if c!="\n"])
        start=logical.index("الملفات")
        end=logical.index("smart_collections.json")+len("smart_collections.json")
        found=[]
        for row,a,b in mapped_ranges(lines,start,end): found.extend(lines[row-1].logical_indices[a:b])
        self.assertEqual(sorted(found),list(range(start,end)))

if __name__=="__main__":unittest.main()

import unittest
from image_ui import ImageChoices
class ImageChoiceTests(unittest.TestCase):
    def test_hardware_choice_refresh_keeps_cpu_id_and_gpu_model_label(self):
        import tkinter as tk
        from image_ui import ImageChoiceVar
        variable=ImageChoiceVar(lambda value: {'Automatic':'Auto','CPU (slower)':'CPU langsam'}.get(value,value),('Automatic',),'Automatic',master=tk.Tcl())
        variable.update_choices(('Automatic','CPU (slower)','NVIDIA T1000'))
        self.assertEqual(variable.choices.labels,('Auto','CPU langsam','NVIDIA T1000'))
        variable.set('CPU (slower)')
        self.assertEqual(variable.get(),'CPU (slower)')

    def test_all_automatic_labels_have_no_split_english_suffix(self):
        import json
        from pathlib import Path
        for path in (Path(__file__).parent/'locales').glob('*.json'):
            value=json.loads(path.read_text(encoding='utf-8'))['literals'].get('Automatic','Automatic')
            self.assertNotIn(' matic',value,path.stem)

    def test_translated_display_retains_english_processing_values(self):
        choices=ImageChoices(lambda value: {'Ordinary resizing':'Normal', 'Automatic':'Automatisch'}.get(value,value),('Ordinary resizing','Automatic'))
        self.assertEqual(choices.labels,('Normal','Automatisch'))
        self.assertEqual(choices.internal('Normal'),'Ordinary resizing')
        self.assertEqual(choices.label('Automatic'),'Automatisch')
        self.assertEqual(choices.internal('GPU 0'),'GPU 0')

    def test_translated_tcl_label_round_trips_to_internal_value(self):
        import tkinter as tk
        from image_ui import ImageChoiceVar
        root=tk.Tcl()
        variable=ImageChoiceVar(lambda value: {'Original size':'Originalgroesse','Custom long edge':'Eigene Kante'}.get(value,value),('Original size','Custom long edge'),'Original size',master=root)
        self.assertEqual(root.getvar(str(variable)),'Originalgroesse')
        root.setvar(str(variable),'Eigene Kante')
        self.assertEqual(variable.get(),'Custom long edge')
        variable.set('Original size')
        self.assertEqual(root.getvar(str(variable)),'Originalgroesse')

    def test_actual_german_enhancement_labels_keep_all_processing_choices(self):
        from pathlib import Path
        from localization import Translator
        from image_pipeline import IMAGE_MODES,RESIZE_CHOICES,EFFECTS
        translator=Translator(Path(__file__).parent/'locales','de')
        for values in (tuple(IMAGE_MODES),RESIZE_CHOICES,EFFECTS,('Light','Medium','Strong'),('Skip existing','Keep both')):
            choices=ImageChoices(translator.ui_text,values)
            for original in values:
                self.assertEqual(choices.internal(choices.label(original)),original)
        self.assertNotEqual(translator.ui_text('Original size'),'Original size')

    def test_video_progress_keeps_numeric_fps_outside_translated_display(self):
        from pathlib import Path
        source=(Path(__file__).parent/'media_sorter.py').read_text(encoding='utf-8')
        dialog=source.split('    def convert_selected_videos(self):',1)[1].split('    @staticmethod',1)[0]
        self.assertNotIn("file_status.get().partition(' · Average')",dialog)
        self.assertNotIn("file_status.get().split(' · Average')",dialog)
        self.assertIn('latest_fps',dialog)

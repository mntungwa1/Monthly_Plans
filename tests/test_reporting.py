import json
import sys
import unittest
from pathlib import Path
from io import BytesIO
from copy import deepcopy

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from reporting import *
from docx import Document

class ReportingTests(unittest.TestCase):
    def setUp(self):self.d=loads_draft((ROOT/'examples/bbb_example.json').read_bytes())
    def test_separate_hours(self):
        t=totals([r for r in self.d['activities'] if r['phase']=='Progress'])
        self.assertEqual(t,{'Actual':0,'Estimated':48,'Scheduled':7,'Anticipated':0})
        self.assertEqual(sum(r['hours'] for r in self.d['activities'] if r['phase']=='Workplan'),72)
    def test_draft_roundtrip(self):
        self.assertEqual(self.d,loads_draft(json.dumps(self.d).encode()))
    def test_actual_requires_evidence(self):
        r=self.d['activities'][0];r['basis']='Actual';r['evidence']=''
        self.assertTrue(any('evidence' in x for x in validate(self.d)[0]))
    def test_invalid_dates_and_hours(self):
        self.d['activities'][0]['hours']=-1
        self.d['activities'][1]['end']='2026-09-01'
        self.assertEqual(len(validate(self.d)[0]),2)
        with self.assertRaises(ValueError):export_docx(self.d)
    def test_json_invalid_numbers(self):
        self.d['activities'][0]['hours']=float('nan')
        with self.assertRaises(ValueError):loads_draft(json.dumps(self.d).encode())
    def test_workplan_blocks_actual(self):
        self.d['activities'][-1]['basis']='Actual'
        self.d['activities'][-1]['evidence']='Some record'
        self.assertTrue(any('belong in Progress' in x for x in validate(self.d)[0]))
    def test_word_exports(self):
        for mode,count in [('progress',6),('workplan',4)]:
            doc=Document(BytesIO(export_docx(self.d,mode)))
            self.assertEqual(len(doc.tables[0].rows),count+1)
            self.assertEqual(len(doc.tables[0].columns),4)
            self.assertEqual(len(doc.inline_shapes),1)
            self.assertIn('Confidential',doc.sections[0].footer.paragraphs[0].text)
            text='\n'.join(p.text for p in doc.paragraphs)
            self.assertIn('10.',text)
            self.assertNotIn('……………………',text)
            if mode=='progress':self.assertNotIn('5.7',text)

class AppTests(unittest.TestCase):
    def test_blank_example_and_restored_widgets(self):
        from streamlit.testing.v1 import AppTest
        at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30)
        at.secrets['APP_PASSWORD']='test-password'
        at.run()
        at.text_input[0].set_value('test-password')
        next(b for b in at.button if b.label=='Sign in').click().run()
        self.assertFalse(at.exception)
        next(b for b in at.button if b.label=='Load BBB example').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.text_input[0].value,'Build Back Better (BBB)')
        self.assertEqual([x.value for x in at.metric],['0 h','48 h','7 h','0 h','72 h'])
        # Restore the same way the upload button does: replace draft and increment widget epoch.
        restored=loads_draft(json.dumps(at.session_state['draft']).encode())
        restored['meta']['substream']='SEMS'
        restored['narratives']['summary']='Restored summary'
        at.session_state['draft']=restored
        at.session_state['epoch']+=1
        del at.session_state['editor_source']
        at.run()
        self.assertFalse(at.exception)
        self.assertEqual(at.text_input[0].value,'SEMS')
        self.assertEqual(at.text_area[2].value,'Restored summary')
    def test_password_gate(self):
        from streamlit.testing.v1 import AppTest
        at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30)
        at.secrets['APP_PASSWORD']='test-password'
        at.run();self.assertFalse(at.exception)
        self.assertEqual(at.text_input[0].label,'App password')
        at.text_input[0].set_value('test-password')
        next(b for b in at.button if b.label=='Sign in').click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.text_input[0].label,'Sub-stream name')

    def test_blank_password_blocks_access(self):
        from streamlit.testing.v1 import AppTest
        at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30)
        at.secrets['APP_PASSWORD']=' '
        at.run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.tabs),0)
        self.assertTrue(any('missing or blank' in e.value for e in at.error))

    def test_admin_requires_separate_password(self):
        from streamlit.testing.v1 import AppTest
        at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30)
        at.secrets['APP_PASSWORD']='app-test'
        at.secrets['ADMIN_PASSWORD']='admin-test'
        at.run();at.text_input[0].set_value('app-test')
        next(b for b in at.button if b.label=='Sign in').click().run()
        self.assertFalse(at.exception)
        self.assertFalse(any(b.label=='Lock admin dashboard' for b in at.button))
        next(x for x in at.text_input if x.label=='Admin password').set_value('app-test')
        next(b for b in at.button if b.label=='Unlock admin dashboard').click().run()
        self.assertFalse(any(b.label=='Lock admin dashboard' for b in at.button))
        next(x for x in at.text_input if x.label=='Admin password').set_value('admin-test')
        next(b for b in at.button if b.label=='Unlock admin dashboard').click().run()
        self.assertFalse(at.exception)
        self.assertTrue(any(b.label=='Lock admin dashboard' for b in at.button))
        next(b for b in at.button if b.label=='Lock admin dashboard').click().run()
        self.assertFalse(any(b.label=='Lock admin dashboard' for b in at.button))

class StorageTests(unittest.TestCase):
    def test_archive_roundtrip(self):
        import tempfile
        from storage import save_draft,archived_files
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);d=new_draft()
            first=save_draft(d,root);second=save_draft(d,root)
            self.assertNotEqual(first,second)
            self.assertEqual(len(archived_files(root)),2)
            self.assertEqual(d,loads_draft((root/first).read_bytes()))

class EmailTests(unittest.TestCase):
    def setUp(self):
        self.config={'EMAIL_ADDRESS':'dingaanm@gmail.com','EMAIL_PASSWORD':'test-app-password',
                     'ADMIN_EMAIL':'admin@ncuma.co.za','EMAIL_MODE':'testing'}
        self.d=loads_draft((ROOT/'examples/bbb_example.json').read_bytes())
    def test_testing_and_admin_routing(self):
        from submission import email_config
        self.assertEqual(email_config(self.config.get)[2],'dingaanm@gmail.com')
        self.config['EMAIL_MODE']='administrator'
        self.assertEqual(email_config(self.config.get)[2],'admin@ncuma.co.za')
        self.config['ADMIN_EMAIL']='admin @ncuma.co.za'
        with self.assertRaises(ValueError):email_config(self.config.get)
    def test_empty_credentials_block_email(self):
        from submission import email_config
        self.config['EMAIL_PASSWORD']=' '
        with self.assertRaises(ValueError):email_config(self.config.get)
    def test_smtp_submission_contains_both_reports(self):
        from unittest.mock import patch
        from submission import send_submission
        with patch('submission.smtplib.SMTP_SSL') as smtp:
            client=smtp.return_value.__enter__.return_value
            client.send_message.return_value={}
            recipient=send_submission(self.d,self.config.get)
            self.assertEqual(recipient,'dingaanm@gmail.com')
            client.login.assert_called_once_with('dingaanm@gmail.com','test-app-password')
            message=client.send_message.call_args.args[0]
            self.assertEqual(message['To'],'dingaanm@gmail.com')
            attachments=list(message.iter_attachments())
            self.assertEqual(len(attachments),2)
            self.assertTrue(all(a.get_filename().endswith('.docx') for a in attachments))
            self.assertNotIn('test-app-password',message.as_string())
    def test_submission_button_and_duplicate_guard(self):
        from unittest.mock import patch
        from streamlit.testing.v1 import AppTest
        at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30)
        at.secrets.update(self.config)
        at.secrets['APP_PASSWORD']='app-test'
        at.run();at.text_input[0].set_value('app-test')
        next(b for b in at.button if b.label=='Sign in').click().run()
        next(b for b in at.button if b.label=='Load BBB example').click().run()
        with patch('submission.send_submission',return_value='dingaanm@gmail.com') as send:
            next(b for b in at.button if b.label=='Submit workplan and progress report by email').click().run()
            self.assertFalse(at.exception);send.assert_called_once()
            at.run()
            self.assertTrue(next(b for b in at.button if b.label=='Submit workplan and progress report by email').disabled)

if __name__=='__main__':unittest.main()

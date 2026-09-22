import copy
import io
import json
from pathlib import Path
import runpy
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import check
import update
import wiki


class WikiTests(unittest.TestCase):
    def setUp(self):
        self.pages = json.loads((wiki.PACKAGE/'references/pages.json').read_text())
        self.templates = json.loads((wiki.PACKAGE/'references/templates.json').read_text())
        self.manifest = json.loads((wiki.PACKAGE/'sources.json').read_text())
        self.helper = runpy.run_path(str(wiki.PACKAGE/'scripts/wiki.py'))

    def xml(self, pages=None, templates=None):
        root = ET.Element('mediawiki', xmlns=wiki.XMLNS, version='0.11')
        for record in ((pages or self.pages) | (templates or {'Template:Warning': self.templates['Template:Warning']})).values():
            page = ET.SubElement(root, 'page')
            for name, key in [('title','title'),('ns','namespace'),('id','page_id')]:
                ET.SubElement(page,name).text = str(record[key])
            if record['redirect']:
                ET.SubElement(page, 'redirect', title=record['redirect']['title'])
            rev = ET.SubElement(page, 'revision')
            for name,key in [('id','revision_id'),('timestamp','timestamp'),('model','model'),('text','text')]:
                ET.SubElement(rev,name).text = str(record[key])
        return ET.tostring(root)

    def test_streaming_latest_and_preservation(self):
        root = ET.fromstring(self.xml())
        ns = '{'+wiki.XMLNS+'}'
        page = next(p for p in root if p.findtext(ns+'title') == 'NixOS')
        original = page.find(ns+'revision')
        history = copy.deepcopy(original)
        history.find(ns+'id').text = '99999999'
        history.find(ns+'timestamp').text = '2000-01-01T00:00:00Z'
        history.find(ns+'text').text = 'Historic text must not leak'
        page.append(history)  # latest is selected by time, not XML order or largest ID alone
        text = '<syntaxhighlight lang="nix">\n"&amp; ${value}"\n</syntaxhighlight>\n{{Warning|Keep me}}'
        original.find(ns+'text').text = text
        pages, templates = wiki.extract(io.BytesIO(ET.tostring(root)))
        self.assertEqual(pages['NixOS']['text'], text)
        self.assertEqual(templates['Template:Warning'], self.templates['Template:Warning'])
        files, manifest = wiki.generate(pages, templates, 'a'*64)
        self.assertEqual((files,manifest),wiki.generate(pages,templates,'a'*64))
        # Same timestamp: highest numeric revision wins.
        history.find(ns+'timestamp').text = original.find(ns+'timestamp').text
        pages,_ = wiki.extract(io.BytesIO(ET.tostring(root)))
        self.assertEqual(pages['NixOS']['revision_id'],99999999)

    def test_xml_failures_and_bounds(self):
        valid = self.xml()
        invalid = [valid[:-8], valid.replace(b'export-0.11',b'export-0.10'),
                   b'<!DOCTYPE mediawiki [<!ENTITY x "expanded">]>'+valid,
                   valid.replace(b'<text>',b'<text deleted="deleted">',1),
                   valid.replace(b'<model>wikitext</model>',b'<model>javascript</model>',1),
                   valid.replace(b'<text>',b'<text><evil/>',1),
                   valid.replace(b'<title>NixOS</title>',b'<title>NixOS</title><title>NixOS</title>',1)]
        for data in invalid:
            with self.subTest(data=data[:70]), self.assertRaises((ValueError, wiki.expat.ExpatError)):
                wiki.extract(io.BytesIO(data))
        for key in ['expanded','text','pages','revisions']:
            with self.subTest(limit=key),self.assertRaises(ValueError):
                wiki.extract(io.BytesIO(valid),wiki.LIMITS | {key:1})
        class TinyReader(io.BytesIO):
            def read(self, size=-1):
                return super().read(1)
        with self.assertRaisesRegex(ValueError,'DTD'):
            wiki.extract(TinyReader(b'<!DOCTYPE mediawiki [<!ENTITY x "x">]>'+valid))
        root=ET.fromstring(valid)
        root.append(copy.deepcopy(root[0]))
        with self.assertRaises(ValueError):
            wiki.extract(io.BytesIO(ET.tostring(root)))

    def test_missing_records_redirects_and_hashes(self):
        for mutate in ['missing','hash','identity','copyright','redirect']:
            pages=copy.deepcopy(self.pages)
            if mutate=='missing': del pages['NixOS']
            if mutate=='hash': pages['NixOS']['text'] += 'bad'
            if mutate=='identity': pages['NixOS']['page_id'] = pages['SSH']['page_id']
            if mutate=='copyright': pages[wiki.COPYRIGHT]['revision_id'] += 1000000
            if mutate=='redirect':
                pages['Storage optimization']['text']='#REDIRECT [[Garbage Collection]]'
                pages['Storage optimization']['sha256']=update.digest(pages['Storage optimization']['text'].encode())
                pages['Storage optimization']['redirect']=wiki.redirect(pages['Storage optimization']['text'])
            with self.subTest(case=mutate),self.assertRaises(ValueError):
                wiki.validate_records(pages,self.templates)

    def test_lookup_and_unicode_pagination(self):
        records=self.pages | self.templates
        results=self.helper['search'](records,'rebuild')
        self.assertEqual(results[0][2],'Nixos-rebuild')
        self.assertLessEqual(len(self.helper['search'](records,'a',True)),10)
        self.assertFalse(any(r[2].startswith('Template:') for r in self.helper['search'](records,'Warning')))
        with self.assertRaises(ValueError):self.helper['search'](records,'')
        hops,record,missing=self.helper['route'](records,'Garbage Collection',True)
        self.assertIsNone(missing)
        self.assertEqual(record['title'],'Storage optimization')
        self.assertEqual(hops[0]['redirect']['fragment'],'Garbage collection')
        with self.assertRaises(ValueError):self.helper['route'](records,'garbage collection')
        changed=copy.deepcopy(records)
        changed['Storage optimization']['redirect']={'title':'Garbage Collection','fragment':''}
        with self.assertRaises(ValueError):self.helper['route'](changed,'Garbage Collection',True)
        changed['Storage optimization']['redirect']={'title':'Not bundled','fragment':'section'}
        self.assertEqual(self.helper['route'](changed,'Garbage Collection',True)[2],'Not bundled')
        original='α'*20000+'\n'+'x\n'*250
        parts=[];position=(1,0)
        while position:
            body,next_position,_=self.helper['window'](original,position[0],200,position[1])
            self.assertLessEqual(len(body.encode()),16384)
            self.assertNotEqual(position,next_position)
            parts.append(body);position=next_position
        self.assertEqual(''.join(parts),original)
        for start,lines,offset in [(0,1,0),(1,201,0),(1,1,-1)]:
            with self.assertRaises(ValueError):self.helper['window']('x',start,lines,offset)

    def test_offline_reproduction_and_policy(self):
        with patch.object(socket.socket,'connect',side_effect=AssertionError('Network during offline check')), \
             patch.object(wiki,'download',side_effect=AssertionError('Download during check')), \
             patch.object(wiki.subprocess,'Popen',side_effect=AssertionError('Tool execution during offline check')):
            self.assertEqual(check.validate(wiki.PACKAGE,skill='nixos-wiki'),self.manifest)
            from argparse import Namespace
            wiki.main(Namespace(check=True))
        changed=copy.deepcopy(self.manifest);changed['policy']['limits']['expanded'] *= 2
        with self.assertRaises(ValueError):check.immutable_policy(self.manifest,changed,'nixos-wiki')
        changed=copy.deepcopy(self.manifest);changed['records']['NixOS']['sha256']='0'*64
        with self.assertRaises(ValueError):check.immutable_policy(self.manifest,changed,'nixos-wiki')
        with patch.object(check,'run',return_value='skills/nixos-wiki/scripts/wiki.py'),self.assertRaises(ValueError):
            check.boundary('base',wiki.PACKAGE,skill='nixos-wiki')

    def test_transition_noop_regression_and_report(self):
        self.assertEqual(wiki.changes(self.pages,self.templates,self.pages,self.templates),[])
        pages=copy.deepcopy(self.pages)
        pages['NixOS']['revision_id'] += 1000000
        self.assertIn('provenance-only',wiki.changes(self.pages,self.templates,pages,self.templates)[0])
        pages['NixOS']['text'] += '\nChanged'
        pages['NixOS']['sha256']=update.digest(pages['NixOS']['text'].encode())
        self.assertIn('content',wiki.changes(self.pages,self.templates,pages,self.templates)[0])
        for field,value in [('revision_id',1),('timestamp','2000-01-01T00:00:00Z'),('page_id',90000000)]:
            changed=copy.deepcopy(pages);changed['NixOS'][field]=value
            with self.assertRaises(ValueError):wiki.changes(self.pages,self.templates,changed,self.templates)
        changed=copy.deepcopy(pages);changed['NixOS']['revision_id']=self.pages['NixOS']['revision_id']
        with self.assertRaises(ValueError):wiki.changes(self.pages,self.templates,changed,self.templates)
        changed=copy.deepcopy(self.pages);changed[wiki.COPYRIGHT]['text']+='\n'
        changed[wiki.COPYRIGHT]['sha256']=update.digest(changed[wiki.COPYRIGHT]['text'].encode())
        with self.assertRaises(ValueError):wiki.changes(self.pages,self.templates,changed,self.templates)

    def test_updater_noop_modes(self):
        from argparse import Namespace
        args=Namespace(check=False,dump=None,sha256=None)
        for snapshot in [self.manifest['snapshot_sha256'],'a'*64]:
            with patch.object(wiki,'download',return_value=snapshot), \
                 patch.object(wiki,'hash_file',return_value=snapshot), \
                 patch.object(wiki,'read_dump',return_value=(self.pages,self.templates)) as reader, \
                 patch.object(update,'publish',side_effect=AssertionError('No-op published')):
                wiki.main(args)
                self.assertEqual(reader.call_count,0 if snapshot==self.manifest['snapshot_sha256'] else 1)

    def test_hash_and_decoder_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'bad.zst';path.write_bytes(b'not zstd')
            with self.assertRaisesRegex(ValueError,'SHA-256'):wiki.read_dump(path,'0'*64)
            # Mock the external decoder, keeping offline unit tests Python-only.
            process=unittest.mock.Mock(stdout=io.BytesIO(self.xml()))
            process.wait.return_value=1;process.poll.return_value=1
            with patch.object(wiki.subprocess,'Popen',return_value=process),self.assertRaisesRegex(ValueError,'decompression'):
                wiki.read_dump(path,wiki.hash_file(path))
            with patch.dict(wiki.LIMITS,compressed=1),self.assertRaises(ValueError):wiki.hash_file(path)

    def test_download_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'download.zst'
            response=unittest.mock.MagicMock()
            response.__enter__.return_value=response
            response.geturl.return_value=wiki.UPSTREAM
            response.headers={'Content-Length':'3'}
            response.read.side_effect=io.BytesIO(b'abc').read
            with patch.object(wiki,'urlopen',return_value=response):
                self.assertEqual(wiki.download(path),update.digest(b'abc'))
            response.read.side_effect=io.BytesIO(b'ab').read
            with patch.object(wiki,'urlopen',return_value=response),self.assertRaisesRegex(ValueError,'Truncated'):
                wiki.download(path)
            response.headers={'Content-Length':str(wiki.LIMITS['compressed']+1)}
            with patch.object(wiki,'urlopen',return_value=response),self.assertRaisesRegex(ValueError,'limit'):
                wiki.download(path)
            response.geturl.return_value='https://unrelated.invalid/dump'
            with patch.object(wiki,'urlopen',return_value=response),self.assertRaisesRegex(ValueError,'redirect'):
                wiki.download(path)

    def test_cli_flag_rejection(self):
        for args in [['--skill','nixos-wiki','--release','1.0'],['--skill','nixos-wiki','--dump','x'],
                     ['--skill','nixos-wiki','--check','--sha256','a'*64],['--dump','x','--sha256','a'*64]]:
            result=subprocess.run([sys.executable,str(update.ROOT/'scripts/update.py'),*args],capture_output=True)
            self.assertEqual(result.returncode,2,result.stderr)

    def test_partial_write_restoration(self):
        with tempfile.TemporaryDirectory() as directory:
            package=Path(directory)/'skill';shutil.copytree(wiki.PACKAGE,package)
            before={name:(package/name).read_bytes() for name in wiki.GENERATED}
            pages=copy.deepcopy(self.pages);pages['NixOS']['revision_id']+=1000000
            files,_=wiki.generate(pages,self.templates,'b'*64)
            replace=update.os.replace;calls=[]
            def fail_second(source,target):
                calls.append(target)
                if len(calls)==2:raise OSError('partial write')
                replace(source,target)
            with patch.object(update.os,'replace',side_effect=fail_second),self.assertRaises(OSError):
                update.publish(files,package,skill='nixos-wiki')
            self.assertEqual(before,{name:(package/name).read_bytes() for name in before})


if __name__=='__main__':unittest.main()

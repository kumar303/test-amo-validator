
import json
import os
import sys
import unittest
from cStringIO import StringIO

from nose.tools import eq_
from validator.validate import validate


def _validator(file_path):
    # TODO(Kumar) This is currently copied from Zamboni because
    # it's really hard to import from zamboni outside of itself.
    # TODO(Kumar) remove this when validator is fixed, see bug 620503
    from validator.testcases import scripting
    import validator.constants
    js = os.environ.get('SPIDERMONKEY_INSTALLATION', 'js')
    scripting.SPIDERMONKEY_INSTALLATION = js
    validator.constants.SPIDERMONKEY_INSTALLATION = js
    apps = os.path.join(os.path.dirname(__file__), 'apps.json')
    orig = sys.stderr
    sys.stderr = StringIO()
    try:
        result = validate(file_path, format='json',
                        # Test all tiers at once. This will make sure we see
                        # all error messages.
                        determined=True,
                        approved_applications=apps,
                        spidermonkey=js)
        sys.stdout.write(sys.stderr.getvalue())
        if 'Traceback' in sys.stderr.getvalue():
            # the validator catches and ignores certain errors in an attempt
            # to remain versatile.  There should not be any exceptions
            # while testing.
            raise RuntimeError(
                "An exception was raised during validation. Check stderr")
    finally:
        sys.stderr = orig
    return result


_cached_validation = {}


class ValidatorTest(unittest.TestCase):

    def setUp(self):
        self.validation = None
        self.messages = None

    def msg_set(self, d):
        return sorted(set([m['message'] for m in d['messages']]))

    def validate(self, xpi):
        self.validation = self._run_validation(xpi)
        self.messages = self.msg_set(self.validation)
        return self.validation

    def _run_validation(self, xpi):
        path = os.path.join(os.path.dirname(__file__), 'addons', xpi)
        if path in _cached_validation:
            return _cached_validation[path]
        v = json.loads(_validator(path))
        _cached_validation[path] = v
        return v

    def assertPartialMsg(self, partial_msg):
        found = False
        for m in self.messages:
            if m.startswith(partial_msg):
                found = True
        assert found, ('Unexpected: %r' % self.messages)

    def expectMsg(self, msg):
        assert msg in self.messages, (
                    'Expected %r but only got %r' % (msg, self.messages))


class JavaScriptTests(ValidatorTest):

    def test_createelement__used(self):
        self.validate('glee-20101227219.xpi')
        self.assertPartialMsg('createElement() used to create script tag')

    def test_dangerous_global(self):
        self.validate('feedly-addon-201101111013.xpi')
        self.expectMsg(u'Dangerous Global Object')

    def test_global_called(self):
        self.validate('babuji-20110124355.xpi')
        self.expectMsg(u'Global called in dangerous manner')

    def test_potentially_malicious(self):
        self.validate('add-on201101101027.xpi')
        self.expectMsg(u'Potentially malicious JS')

    def test_variable_element(self):
        self.validate('glee-20101227219.xpi')
        self.expectMsg(u'Variable element type being created')


class GeneralTests(ValidatorTest):

    def test_contains_jar_files(self):
        self.validate('test-theme-3004.jar')
        self.expectMsg(u'Add-on contains JAR files, no <em:unpack>')

    def test_potentially_illegal_name(self):
        self.validate('add-on20110110322.xpi')
        self.expectMsg(u'Add-on has potentially illegal name.')

    def test_banned_element(self):
        self.validate('gabbielsan_tools-1.01-ff.xpi')
        self.expectMsg(u'Banned element in install.rdf')

    def test_blacklisted_file(self):
        self.validate('babuji-20110124355.xpi')
        self.expectMsg(u'Flagged file extension found')

    def test_blacklisted_file_2(self):
        self.validate('peerscape-3.1.5-fx.xpi')
        self.expectMsg(u'Flagged file type found')

    def test_em_type_not(self):
        self.validate('babuji-20110124355.xpi')
        self.expectMsg(u'No <em:type> element found in install.rdf')

    def test_obsolete_element(self):
        self.validate('gabbielsan_tools-1.01-ff.xpi')
        self.expectMsg(u'Banned element in install.rdf')

    def test_unknown_file(self):
        self.validate('gabbielsan_tools-1.01-ff.xpi')
        self.expectMsg(u'Unrecognized element in install.rdf')

    def test_unrecognized_element(self):
        self.validate('littlemonkey-1.8.56-sm.xpi')
        self.expectMsg(u'Addon missing install.rdf.')

    def test_invalid_id(self):
        self.validate('add-ongoogle-201101121132.xpi')
        self.expectMsg(u'The value of <em:id> is invalid.')

    def test_xpi_cannot(self):
        self.validate('lavafox_test-theme-20101130538.xpi')
        self.expectMsg(u'The XPI could not be opened.')

    def test_invalid_version(self):
        self.validate('invalid maximum version number.xpi')
        self.expectMsg(u'Invalid maximum version number')


class LocalizationTests(ValidatorTest):

    def test_translation(self):
        self.validate('babuji-20110124355.xpi')
        self.expectMsg(u'Unchanged translation entities')

    def test_encodings(self):
        self.validate('babuji-20110124355.xpi')
        self.expectMsg(u'Unexpected encodings in locale files')

    def test_missing_translation(self):
        self.validate('download_statusbar-0.9.7.2-fx (1).xpi')
        self.expectMsg(u'Missing translation entity')


class SecurityTests(ValidatorTest):

    def test_missing_comments(self):
        self.validate('add-on-20110113408.xpi')
        self.expectMsg(u'Missing comments in <script> tag')

    def test_typeless_iframes_browsers(self):
        self.validate('add-on201101081038.xpi')
        self.expectMsg(u'Typeless iframes/browsers must be local.')


class NoErrorsExpected(ValidatorTest):

    def test_an_attempt(self):
        d = self.validate('tmp.xpi')
        eq_(d['errors'], 0)

    def test_don_t_freak(self):
        d = self.validate('test (1).xpi')
        eq_(d['errors'], 0)

    def test_don_t_freak_2(self):
        d = self.validate('littlemonkey-1.8.56-sm.xpi')
        msg = self.msg_set(d)
        ok = True
        for m in msg:
            if 'install.js' in msg:
                ok = False
        assert ok, ('Unexpected: %r' % msg)

    def test_unknown_file(self):
        d = self.validate('add-on20101228444 (1).jar')
        eq_(d['errors'], 0)


class SearchTools(ValidatorTest):

    def test_opensearch_providers(self):
        self.validate('sms_search-20110115 .xml')
        self.expectMsg(u'OpenSearch: <Url> elements may not be rel=self')

    def test_opensearch_shortname(self):
        self.validate('lexisone_citation_search-20100116 .xml')
        self.expectMsg(u'OpenSearch: <ShortName> element too long')

    def test_too_many(self):
        self.validate('addon-12201-latest.xml')
        self.expectMsg(u'OpenSearch: Too many <ShortName> elements')

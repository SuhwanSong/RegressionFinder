import unittest

def minimize_(html, minimization_function):
    return html

SIMPLE_HTML_TESTCASE = (
    "<!doctype html>\n"
    "<style>\n"
    "  div {\n"
    "    background: blue;\n"
    "    border: 1px solid black;\n"
    "  }\n"
    "  span {\n"
    "    color: green;\n"
    "  }\n"
    "</style>\n"
    "<div>\n"
    "  <span>\n"
    "    hello world\n"
    "  </span>\n"
    "</div>")

THREE_STYLE_SELECTOR_TESTCASE = (
    "<!doctype html>\n"
    "<style>\n"
    "  a { background: red; }\n"
    "  b { background: green; }\n"
    "  c { background: blue; }\n"
    "</style>\n")

THREE_STYLE_RULE_TESTCASE = (
    "<!doctype html>\n"
    "<style>\n"
    "  a {\n"
    "    background: red;\n"
    "    background: green;\n"
    "    background: blue;\n"
    "  }\n"
    "</style>\n")

THREE_DIV_TESTCASE = (
    "<!doctype html>\n"
    "<div id=a></div>\n"
    "<div id=b></div>\n"
    "<div id=c></div>\n")

THREE_ATTRIBUTE_TESTCASE = (
    "<!doctype html>\n"
    "<div first=a second=b third=c></div>\n")

TWO_STYLED_ELEMENTS_TESTCASE = (
    "<!doctype html>\n"
    "<style>\n"
    "  div { background: blue; }\n"
    "  span { color: green; }\n"
    "</style>\n"
    "<div>foo</div>\n"
    "<span>foo</span>")

class TestMinimizer(unittest.TestCase):
    def test_noop(self):
        def minimization_function(html):
            return SIMPLE_HTML_TESTCASE == html
        expected = SIMPLE_HTML_TESTCASE
        minimized = minimize_(SIMPLE_HTML_TESTCASE, minimization_function)
        self.assertEqual(expected, minimized)

    def test_minimize_to_empty_style(self):
        just_html_part = (
            "<div>\n"
            "  <span>\n"
            "    hello world\n"
            "  </span>\n"
            "</div>")
        def minimization_function(html):
            return just_html_part in html
        expected = (
            "<!doctype html>\n"
            "<style>\n"
            "</style>\n") + just_html_part
        minimized = minimize_(SIMPLE_HTML_TESTCASE, minimization_function)
        self.assertEqual(expected, minimized)

    def test_minimize_to_single_string(self):
        def minimization_function(html):
            return 'hello world' in html
        expected = (
            "<!doctype html>\n"
            "<style>\n"
            "</style>\n"
            "hello world")
        minimized = minimize_(SIMPLE_HTML_TESTCASE, minimization_function)
        self.assertEqual(expected, minimized)

    def test_minimize_to_outer_nested_element(self):
        def minimization_function(html):
            return '<div>' in html and '</div>' in html
        expected = (
            "<!doctype html>\n"
            "<style>\n"
            "</style>\n"
            "<div></div>\n")
        minimized = minimize_(SIMPLE_HTML_TESTCASE, minimization_function)
        self.assertEqual(expected, minimized)

    def test_minimize_to_inner_nested_element(self):
        def minimization_function(html):
            return '<span>' in html and '</span>' in html
        expected = (
            "<!doctype html>\n"
            "<style>\n"
            "</style>\n"
            "<span></span>\n")
        minimized = minimize_(SIMPLE_HTML_TESTCASE, minimization_function)
        self.assertEqual(expected, minimized)

    def test_minimize_to_single_style_selector_1(self):
        def minimization_function(html):
            return 'a { background: red; }' in html
        expected = (
            "<!doctype html>\n"
            "<style>\n"
            "  a { background: red; }\n"
            "</style>\n")
        minimized = minimize_(THREE_STYLE_SELECTOR_TESTCASE, minimization_function)
        self.assertEqual(expected, minimized)

    def test_minimize_to_single_style_selector_2(self):
        def minimization_function(html):
            return 'b { background: green; }' in html
        expected = (
            "<!doctype html>\n"
            "<style>\n"
            "  b { background: green; }\n"
            "</style>\n")
        minimized = minimize_(THREE_STYLE_SELECTOR_TESTCASE, minimization_function)
        self.assertEqual(expected, minimized)

    def test_minimize_to_single_style_selector_3(self):
        def minimization_function(html):
            return 'c { background: blue; }' in html
        expected = (
            "<!doctype html>\n"
            "<style>\n"
            "  c { background: blue; }\n"
            "</style>\n")
        minimized = minimize_(THREE_STYLE_SELECTOR_TESTCASE, minimization_function)
        self.assertEqual(expected, minimized)

    def test_minimize_to_single_style_rule_1(self):
        def minimization_function(html):
            return 'a {' in html and 'background: red;' in html
        expected = (
            "<!doctype html>\n"
            "<style>\n"
            "  a {\n"
            "    background: red;\n"
            "  }\n"
            "</style>\n")
        minimized = minimize_(THREE_STYLE_RULE_TESTCASE, minimization_function)
        self.assertEqual(expected, minimized)

    def test_minimize_to_single_style_rule_2(self):
        def minimization_function(html):
            return 'a {' in html and 'background: green;' in html
        expected = (
            "<!doctype html>\n"
            "<style>\n"
            "  a {\n"
            "    background: green;\n"
            "  }\n"
            "</style>\n")
        minimized = minimize_(THREE_STYLE_RULE_TESTCASE, minimization_function)
        self.assertEqual(expected, minimized)

    def test_minimize_to_single_style_rule_3(self):
        def minimization_function(html):
            return 'a {' in html and 'background: blue;' in html
        expected = (
            "<!doctype html>\n"
            "<style>\n"
            "  a {\n"
            "    background: blue;\n"
            "  }\n"
            "</style>\n")
        minimized = minimize_(THREE_STYLE_RULE_TESTCASE, minimization_function)
        self.assertEqual(expected, minimized)

    def test_minimize_to_single_html_element_1(self):
        def minimization_function(html):
            return 'div id=a' in html
        expected = (
            "<!doctype html>\n"
            "<div id=a></div>\n")
        minimized = minimize_(THREE_DIV_TESTCASE, minimization_function)
        self.assertEqual(expected, minimized)

    def test_minimize_to_single_html_element_2(self):
        def minimization_function(html):
            return 'div id=b' in html
        expected = (
            "<!doctype html>\n"
            "<div id=b></div>\n")
        minimized = minimize_(THREE_DIV_TESTCASE, minimization_function)
        self.assertEqual(expected, minimized)

    def test_minimize_to_single_html_element_3(self):
        def minimization_function(html):
            return 'div id=c' in html
        expected = (
            "<!doctype html>\n"
            "<div id=c></div>\n")
        minimized = minimize_(THREE_DIV_TESTCASE, minimization_function)
        self.assertEqual(expected, minimized)

    def test_minimize_to_single_attribute_1(self):
        def minimization_function(html):
            return 'first=a' in html
        expected = (
            "<!doctype html>\n"
            "<div first=a></div>\n")
        minimized = minimize_(THREE_ATTRIBUTE_TESTCASE, minimization_function)
        self.assertEqual(expected, minimized)

    def test_minimize_to_single_attribute_2(self):
        def minimization_function(html):
            return 'second=b' in html
        expected = (
            "<!doctype html>\n"
            "<div second=b></div>\n")
        minimized = minimize_(THREE_ATTRIBUTE_TESTCASE, minimization_function)
        self.assertEqual(expected, minimized)

    def test_minimize_to_single_attribute_3(self):
        def minimization_function(html):
            return 'third=c' in html
        expected = (
            "<!doctype html>\n"
            "<div third=c></div>\n")
        minimized = minimize_(THREE_ATTRIBUTE_TESTCASE, minimization_function)
        self.assertEqual(expected, minimized)

    def test_minimize_to_single_style_element_pair_1(self):
        def minimization_function(html):
            return 'div { background: blue; }' in html and '<div>foo</div>' in html
        expected = (
            "<!doctype html>\n"
            "<style>\n"
            "  div { background: blue; }\n"
            "</style>\n"
            "<div>foo</div>\n")
        minimized = minimize_(TWO_STYLED_ELEMENTS_TESTCASE, minimization_function)
        self.assertEqual(expected, minimized)

    def test_minimize_to_single_style_element_pair_2(self):
        def minimization_function(html):
            return 'span { color: green; }' in html and '<span>foo</span>' in html
        expected = (
            "<!doctype html>\n"
            "<style>\n"
            "  span { color: green; }\n"
            "</style>\n"
            "<span>foo</span>\n")
        minimized = minimize_(TWO_STYLED_ELEMENTS_TESTCASE, minimization_function)
        self.assertEqual(expected, minimized)

Provides sample data to run parameterized tests. Inspired/in the style of PHPUnit DataProviders.

Each parameterized test is run as a subtest with a sample datum.

Data
====

Sample data can be provided by a literal, a (class) variable or a callable (e.g. a function or class method).

    class SomeTest(unittest.TestCase):
        @DataProvider([('i', 1), ('ii', 2)])
        def test_literal(self, numeral, number):
            # ...

        @DataProvider([i * 2 for i in range(5)])
        def test_evens(self, i):
            # ...

        roman = [('i', 1), ('ii', 2)]
        @DataProvider(roman)
        def test_variable(self, numeral, number):
            # ...

        @classmethod
        def roman_numerals(cls):
            return [('i', 1), ('ii', 2)]

        @DataProvider(roman_numerals)
        def test_classmethod(self, numeral, number):
            # ...

Data can be an iterable (e.g. list, tuple, dict). If data is an instance of collections.abc.Mapping, the keys are taken as the datum labels. Failing subtests will display the datum label, which can be used to identify the particular sample datum that produces the failure.

    class (unittest.TestCase):
        samples = {
            'lovely':('spam', 'plumage', 'day'),
            'runny':('eggs', 'camembert'),
            'fancy':('lobster thermidor', 'suit', 'talk'),
        }

        @DataProvider(samples)
        def test_(self, food, *args):
            # ...


Sample datums should be integer indexed (e.g. lists, tuples).

Multiple Providers
==================

More than one data provider can be used on a test. The earlier, outer providers bind to function arguments first.

Options
=======

DataProviders accept some keyword arguments that affect behavior. .

  setUp
  :	Call the setUp method before each test, and tearDown afterwards. Can be:
     * a function (taking test object & setup data),
     * method name (retrieved from test object using `getattr`), or
     * boolean (in which case the standard `setUp` method is used).
    default: True
  setupData
  :	Pass sample data from the data provider to the setUp method. Can be slice or key sequence to use just some of the sample data.
    default: True
  verbose
  :	Print additional information (such as data sample labels). Value is an int representing the level of verbosity.
    default: 0
  dotsubtests
  :	Print a dot for each subtest.
    default: True

Test & `setUp` Arity
==================

If there is more data provided than the test function accepts (i.e. the length of the data is greater than the test function's arity), DataProvider discards data from the end (which comes from inmost data providers). DataProvider does take variadicity (i.e. `**args`) into account.

By default, all sample data will be collected (from outermost data providers first) and will be passed to setUp; this can be controlled by the 'setupData' option. 'setupData' specifies which data to use: slices will be applied to data. If there are more arguments than `setUp` accepts, only the beginning of the data (from the outermost data providers) will be passed.

    class FooTest(unittest.TestCase)
        sample_ints = [ -1, 0, 1 ]
        sample_strs = [
            ('', '', ''),
            ('AB', 'ab', 'Ab'),
        ]

        def setUp(self, i=None, lower=None):
            # ...

        @DataProvider(sample_ints) # these will be passed as `i`
        @DataProvider(sample_ints,setupData=False) # won't be passed
        @DataProvider(sample_strs,setupData=[1, 2]) # only the 2nd element will actually be passed to setUp
        def test_(self, i, j, upper, lower, mixed):
            #...


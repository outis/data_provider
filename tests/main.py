from data_provider import DataProvider
import unittest

def roman_func():
	return [('i', 1), ('ii', 2)]


class SingleProviderTests(unittest.TestCase):
	"""
    Basic tests of single providers of each basic type for test functions.
	"""
	
	ints=range(0,3)
	
	@DataProvider(ints,setUp=False)
	def test_scalar(self, i):
		self.assertIn(i, self.ints)
	
	@DataProvider(list(ints) + list(range(-9, -4)),setUp=False)
	def test_scalar(self, i):
		self.assertTrue(i in self.ints or i in range(-9, -4))
	
	roman = roman_func()
	
	@classmethod
	def roman_numerals(cls):
		return [('i', 1), ('ii', 2)]
	
	def check_roman_sample(self, numeral, number):
		self.assertIn((numeral, number), self.roman)

	@DataProvider([('i', 1), ('ii', 2)])
	def test_literal(self, numeral, number):
		self.check_roman_sample(numeral, number)
				
	@DataProvider(roman)
	def test_class_variable(self, numeral, number):
		self.check_roman_sample(numeral, number)

	@DataProvider(roman_func)
	def test_func(self, numeral, number):
		self.check_roman_sample(numeral, number)
	
	@DataProvider(roman_numerals)
	def test_classmethod(self, numeral, number):
		self.check_roman_sample(numeral, number)
	
	dict_samples = {
		'lovely':('spam', 'plumage', 'day'),
		'runny':('eggs', 'camembert'),
		'fancy':('lobster thermidor', 'suit', 'talk'),

		'woody':('gorn', 'sausage', 'bound', 'vole'),
		'tinny':('newspaper', 'litter-bin'),
		'pvc': ('leap',),
	}
	
	@DataProvider(dict_samples)
	def test_dict_sample(self, *args):
		self.assertIn(args, self.dict_samples.values())

class SetUpCallCountTest(unittest.TestCase):
	"""
	Checks that a test is called once for each sample on tests that specify it.
	"""
	nCalls = 0
	setupCalled = False
	ints=range(0,3)
	
	def setUp(self):
		self.setupCalled = True
	
	@DataProvider(ints,setUp=False)
	def test_nCalls(self, i):
		self.assertEqual(i, self.nCalls)
		self.nCalls += 1
	
	@DataProvider(ints,setUp=False)
	def test_setUp_called_once(self, i):
		if i:
			# subsequent calls
			self.assertFalse(self.setupCalled)
		else:
			# 1st call
			self.assertTrue(self.setupCalled)
		self.setupCalled = False
	
	@DataProvider(ints,setUp=True)
	def test_setUp_called_each_test(self, i):
		self.assertTrue(self.setupCalled)
		self.setupCalled = False

class SetUpArgumentsTest(unittest.TestCase):
	"""
	Tests that the appropriate arguments are passed to `setUp`.
	"""
	
	roman = [('i', 1), ('ii', 2)]

	def setUp(self, numeral=None):
		self.numeral = numeral

	def test_setUp(self):
		self.assertIsNone(self.numeral)
	
	@DataProvider(roman)
	def test_setUp_reinvoked(self, numeral, number):
		self.assertEqual(numeral, self.numeral)

class MultipleProviderTests(unittest.TestCase):
	"""
	Tests multiple providers for a single test function.
	"""
	
	sample_ints = [ -1, 0, 1 ]
	sample_strs = [
		('', '', ''),
		('AB', 'ab', 'Ab'),
	]
	
	def setUp(self, i=None, lower=None):
		self.i = i
		self.lower = lower
	
	@DataProvider(sample_ints) # these will be passed as `i`
	@DataProvider(sample_ints,setupData=False) # won't be passed
	@DataProvider(sample_strs,setupData=[1, 2]) # only the 2nd element will actually be passed to setUp
	def test_(self, i, j, upper, lower, mixed):
		self.assertEqual((i, lower), (self.i, self.lower))
		self.assertIn(i, self.sample_ints)
		self.assertIn(j, self.sample_ints)
		self.assertIn((upper, lower, mixed), self.sample_strs)

if __name__ == '__main__':
	unittest.main()

import sys, traceback, inspect
from collections import abc, defaultdict
from unittest import SkipTest

"""
? Data provider
? Data source
? Sample set
? Parameterized test

Glossary-
sample set: a collection of data to pass to a test function
data source: what provides the sample set
data provider(?): what passes the samples to the tests

TODO:
* test with other decorators (e.g. @unittest.expectedFailure)
"""

class DataProvider(object):
	"""
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
	"""

	default_options = {
		'verbose': 0,
		#'fulltrace': False,
		'dotsubtests': True,
		'setupData': True,
		'setUp': True,
	}
	outmost = True
	inmost = True
	active = []
	setupArgs = []
	setupKwargs = {}

	@property
	def wrapper(self):
		return self._wrapper

	@wrapper.setter
	def wrapper(self, wrapper):
		self._wrapper = wrapper
		self._wrapper.provider = self

	def __init__(self, dataSource, **kwargs):
		if callable(dataSource):
			self.samples = dataSource()
		else:
			self.samples = dataSource
		self.options = self.default_options | kwargs
		self.report('init ' + str(self.options['verbose']))
		#self.options = defaultdict(lambda: False, kwargs)
		self._setProvide()

	def report(self, msg, lvl=1):
		if self.options['verbose'] > lvl:
			print(msg)

	def begin(self, tester, fn):
		assert len(DataProvider.active) == 0 or DataProvider.active[-1] != self
		DataProvider.active.append(self)
		# handled by __call__
		#self._setMosts(tester)
		#self.report('\nbegin: %a %a' % (tester, fn))

	def _setMosts(self, tester):
		"""
		Sets inmost & outmost DataProviders.
		"""
		if len(DataProvider.active) > 0:
			if DataProvider.active[0] == self:
				self.outmost = True
			else:
				self.outmost = False
		# Note: 'inmost' test assumes there are no decorators in between data providers
		if isinstance(tester, DataProvider):
			self.inmost = False
		else:
			self.inmost = True

	def end(self, tester, fn):
		assert DataProvider.active[-1] == self
		DataProvider.active.pop()

	def get_samples(self, tester, fn):
		# Class isn't fully defined when DataProvider is invoked, so class methods providing samples must be late bound; perform binding the first time the decorated method is called.
		if isinstance(self.samples, classmethod):
			self.samples = self.samples.__func__(type(tester))
		self.get_samples = lambda *args:None

	def isProvidedFor(self, fn):
		return hasattr(fn, 'provider') and isinstance(fn.provider, DataProvider)

	def sliceData(self, data, kwdata , indices):
		"""
		Ensures data to pass as arguments is a list, possibly slicing it.
		"""
		# slice args to pass to setUp
		if isinstance(indices, bool):
			args = list(data)
		else:
			try:
				args = data[indices]
			except TypeError as te:
				try:
					# Try key as collection of indices
					args = [(kwdata if isinstance(i, str) else data)[i] for i in indices]
				except IndexError as e:
					raise
				except Exception as e:
					args = list(data)
		return args

	def sliceSetupData(self, data, kwdata):
		"""
		If option setupData specifies to only pass some of the data to TestCase.setUp(), this method slices the data.
		"""
		return self.sliceData(data, kwdata, self.options['setupData'])

	def passSetupArgs(self, fn, data, kwdata):
		provider = fn.provider
		# prepend data samples to arg list
		#fn.setupArgs = data + self.setupArgs
		#fn.setupKwargs = kwdata.copy()
		#fn.setupKwargs.update(self.setupKwargs)
		# append data samples to arg list
		provider.setupArgs = self.setupArgs.copy()
		provider.setupKwargs = self.setupKwargs.copy()
		if self.options['setupData']:
			provider.setupArgs += self.sliceSetupData(data, kwdata)
			provider.setupKwargs.update(kwdata)
		#print("Passing setup args: %a" % (provider.setupArgs,))

	def shouldSetUp(self):
		return self.inmost and self.options['setUp']

	def setUp(self, tester, data, kwdata):
		# arguments passed from other data providers
		setupArgs = self.setupArgs
		setupKwargs = self.setupKwargs
		# use any of own sample data?
		if self.options['setupData']:
			setupArgs = setupArgs + self.sliceSetupData(data, kwdata)
			setupKwargs = setupKwargs.copy()
			setupKwargs.update(kwdata)
		# get setup function
		if isinstance(self.options['setUp'], str):
			setUp = getattr(tester, self.options['setUp'])
		elif callable(self.options['setUp']):
			setupMethod = self.options['setUp']
			setUp = lambda *args, **kwargs: setupMethod(tester, *args, **kwargs)
		else:
			setUp = tester.setUp
		# determine what arguments the setup function can take
		setupArgspec = inspect.getfullargspec(setUp)
		if not setupArgspec.varargs:
			# N-adic, where 1st arg is `self`. Use N-1 args (-1 for self)
			setupArgs = setupArgs[:len(setupArgspec.args)-1]
		if setupArgspec.varkw:
			setUp(*setupArgs, **setupKwargs)
		else:
			setUp(*setupArgs)

	def test(self, tester, fn, data, addl=[], kwaddl={}):
		try:
			kwdata = kwaddl.copy()
			if isinstance(data, dict):
				# data is keyword arguments, rather than positional
				kwdata.update(data)
				data = []
			# Massage arguments not provided as argument lists
			if not (isinstance(data, list) or isinstance(data, tuple)):
				data = [data]
			# TODO: can passing of setup args be moved outside this method (for efficiency)?
			# pass own data to sub-provider for tester.setUp
			if self.isProvidedFor(fn):
				self.passSetupArgs(fn, data, kwdata)
			elif self.shouldSetUp():
				self.setUp(tester, data, kwdata)
			elif self.options['setupData']:
				#print("fn: %s" % (type(fn).__name__,))
				pass
			# data, addl -> prepend data samples to arg list; last DataProvider samples go in first
			#fn(tester, *data, *addl)
			# addl, data -> append data samples to arg list; first DataProvider samples go in first
			args = [tester, *addl, *data]
			fnArgSpec = inspect.getfullargspec(fn)
			if not fnArgSpec.varargs:
				args = args[:len(fnArgSpec.args)]
			if fnArgSpec.varkw:
				fn(*args, **kwdata)
			else:
				fn(*args)
			if self.options['dotsubtests']:
				print('.', end='', file=sys.stderr)
		except AssertionError:
			print('F', end='', file=sys.stderr)
			raise
		except SkipTest:
			print('s', end='', file=sys.stderr)
			# TODO: anything else? re-raising doubles each 's' in output
			#raise
		except Exception:
			print('E', end='', file=sys.stderr)
			raise
		finally:
			tester.tearDown()
		"""
		try:
			fn(self, *data)
		except Exception as e:
			if provider.options['fulltrace']:
				print("%s trace:\n" % (type(e).__name__))
			traceback.print_exception(type(e), e, e.__traceback__, limit=10)
			print("\n")
			raise e.with_traceback(e.__traceback__)
		"""

	def _setProvide(self, allowDelay=True):
		if isinstance(self.samples, abc.Mapping):
			self.provide = self.provide_map
		elif isinstance(self.samples, abc.Iterable):
			# Should sequential non-Iterable types (i.e. those with __getitem__) be supported?
			self.provide = self.provide_iter
		elif allowDelay and isinstance(self.samples, classmethod):
			self.provide = self.provide_delayed
		#elif isinstance(self.samples, abc.AsyncIterable):
		#	self.provide = self.provide_asyncseq
		else:
			raise TypeError(f"a {type(self.samples).__name__} isn't a valid data source")

	def provide_map(self, fn):
		provider = self
		def wrapper(tester, *args, **kwargs):
			try:
				provider.begin(tester, fn)
				if provider.options['dotsubtests']:
					print('{', end='', file=sys.stderr)
				for label, data in provider.samples.items():
					with tester.subTest(data=label):
						if provider.options['verbose']:
							print("subtest %s" % label)
						provider.test(tester, fn, data, addl=args, kwaddl=kwargs)
				if provider.options['dotsubtests']:
					print('}', end='', file=sys.stderr)
			finally:
				provider.end(tester, fn)
		return wrapper

	def provide_iter(self, fn):
		"""
		Wrap `fn` .
		"""
		provider = self
		def wrapper(tester, *args, **kwargs):
			try:
				provider.begin(tester, fn)
				if provider.options['dotsubtests']:
					print('[', end='', file=sys.stderr)
				for data in provider.samples:
					# use subtest so test failure/error doesn't preclude test with other data
					with tester.subTest(data=data):
						provider.test(tester, fn, data, addl=args, kwaddl=kwargs)
				if provider.options['dotsubtests']:
					print(']', end='', file=sys.stderr)
			finally:
				provider.end(tester, fn)
		return wrapper

	def provide_delayed(self, fn):
		"""
		Wrap `fn` so that samples are generated when the tester object is available (the first time `fn` is called).

		Allows class methods to provide data.
		"""
		provider = self
		# the (initial) wrapper for `fn`, `delay_wrapper`, is responsible for
		# generating samples (via `get_samples`), but then hands off to another
		# `provide_*` method to generate the actual wrapper, which is then
		# called. Subsequent calls to `fn` should skip calls to `delay_wrapper`.
		# Since the returned wrapper can't take itself out of consideration,
		# `provide_delayed` does the next best thing: the outer `wrapper`
		# variable allows the wrapper implementation to be switched from
		# `delay_wrapper` to the . .
		def delay_wrapper(tester, *args, **kwargs):
			nonlocal wrapper
			# Perform late binding for class methods that provide samples
			provider.get_samples(tester, fn)
			provider._setProvide(allowDelay=False)
			# assigning provider.wrapper sets wrapper.provider; beyond that,
			# assinging provider.wrapper probably isn't necessary
			wrapper = provider.wrapper = provider.provide(fn)
			wrapper(tester, *args, **kwargs)
		wrapper = delay_wrapper
		def bounce(*args, **kwargs):
			wrapper(*args, **kwargs)
		return bounce

	def provide_asyncseq(self, fn):
		# TODO: test
		provider = self
		async def wrapper(tester, *args, **kwargs):
			try:
				provider.begin(tester, fn)
				if provider.options['dotsubtests']:
					print('[', end='', file=sys.stderr)
				async for data in provider.samples:
					# use subtest so test failure/error doesn't preclude test with other data
					with tester.subTest(data=data):
						provider.test(tester, fn, data, addl=args, kwaddl=kwargs)
				if provider.options['dotsubtests']:
					print(']', end='', file=sys.stderr)
			finally:
				provider.end(tester, fn)
		return wrapper

	def __call__(self, fn):
		self.report('provide ' + str(self.options['verbose']))
		if hasattr(fn, 'provider'):
			fn.provider.outmost = False
			self.inmost = False
		self.fn = fn
		self.wrapper = self.provide(fn)
		return self.wrapper

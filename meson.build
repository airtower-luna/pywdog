project(
  'pywdog', 'c',
  license: 'ISC',
  license_files: ['LICENSE'],
  meson_version: '>=1.1'
)

wdog = dependency('libwdog', version: '>=4.0')

py = import('python').find_installation(pure: false)

# build_libwdog.py uses cffi to generate module C source
gen_src = custom_target(
  'gen-wdog',
  input: ['build_libwdog.py'],
  output: ['_libwdog.c'],
  command: [py.full_path(), '@INPUT@', '@OUTPUT@']
)

# let Meson compile the generated module
mod = py.extension_module(
  '_libwdog',
  gen_src,
  install: true,
  dependencies: [wdog, py.dependency()],
)
py.install_sources('wdog.py')

pytest = find_program('pytest')

if get_option('tests')
  watchdogd = find_program(get_option('watchdogd'), required: true)
  test('pytest', files('test-namespace-wrapper.sh'), args: [
	 pytest.full_path(),
	 '-v',
	 '--override-ini', '='.join('pythonpath', meson.global_build_root()),
	 [files('test_wdog.py')]],
       env: ['='.join('TEST_WATCHDOGD', watchdogd.full_path())],
       depends: [mod])
endif

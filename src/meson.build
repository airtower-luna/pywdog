# build_libwdog.py uses cffi to generate module C source
gen_src = custom_target(
  '_libwdog-source',
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
  subdir: 'wdog'
)

py.install_sources(['__init__.py', 'py.typed'], subdir: 'wdog')

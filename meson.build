project(
  'pywdog', 'c',
  license: 'ISC',
  license_files: ['LICENSE'],
  meson_version: '>=1.1'
)

wdog = dependency('libwdog', version: '>=4.0', allow_fallback: get_option('watchdogd-fallback'))

py = import('python').find_installation(pure: false)

subdir('src')
